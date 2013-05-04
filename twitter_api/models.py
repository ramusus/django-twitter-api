# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.related import RelatedObject
from django.utils.translation import ugettext as _
from utils import api
from decorators import fetch_all
from datetime import datetime
import tweepy
import fields
import dateutil.parser
import logging
import re

__all__ = ['User', 'Status', 'TwitterModel', 'TwitterContentError', 'TwitterManager']

log = logging.getLogger('twitter_api')

class TwitterContentError(Exception):
    pass

class TwitterManager(models.Manager):
    '''
    Twitter Manager for RESTful CRUD operations
    '''
    def __init__(self, methods=None, remote_pk=None, *args, **kwargs):
        if methods and len(methods.items()) < 1:
            raise ValueError('Argument methods must contains at least 1 specified method')

        self.methods = methods or {}
        self.remote_pk = remote_pk or ('id',)
        if not isinstance(self.remote_pk, tuple):
            self.remote_pk = (self.remote_pk,)

        super(TwitterManager, self).__init__(*args, **kwargs)

    def get_by_url(self, url):
        '''
        Return object by url
        '''
        m = re.findall(r'(?:https?://)?(?:www\.)?twitter\.com/(.+)/?', url)
        if not len(m):
            raise ValueError("Url should be started with https://twitter.com/")

        return self.get_by_slug(m[0])

    def get_by_slug(self, slug):
        '''
        Return object by slug
        '''
        return self.model.remote.fetch(slug)

    def get_or_create_from_instance(self, instance):

        remote_pk_dict = {}
        for field_name in self.remote_pk:
            remote_pk_dict[field_name] = getattr(instance, field_name)

        try:
            old_instance = self.model.objects.get(**remote_pk_dict)
            instance._substitute(old_instance)
            instance.save()
        except self.model.DoesNotExist:
            instance.save()
            log.debug('Fetch and create new object %s with remote pk %s' % (self.model, remote_pk_dict))

        return instance

#    def get_or_create_from_resource(self, resource):
#
#        instance = self.model()
#        instance.parse(dict(resource))
#
#        return self.get_or_create_from_instance(instance)

    def api_call(self, *args, **kwargs):
        method = kwargs.pop('method')
        return api(self.methods[method], *args, **kwargs)

    def fetch(self, *args, **kwargs):
        '''
        Retrieve and save object to local DB
        '''
        result = self.get(*args, **kwargs)
        if isinstance(result, list):
            return [self.get_or_create_from_instance(instance) for instance in result]
        else:
            return self.get_or_create_from_instance(result)

    def get(self, *args, **kwargs):
        '''
        Retrieve objects from remote server
        '''
        extra_fields = kwargs.pop('extra_fields', {})
        extra_fields['fetched'] = datetime.now()
        response = self.api_call(method='get', *args, **kwargs)

        return self.parse_response(response, extra_fields)

    def parse_response(self, response, extra_fields=None):
        if isinstance(response, (list, tuple)):
            return self.parse_response_list(response, extra_fields)
        elif isinstance(response, tweepy.models.Model):
            return self.parse_response_object(response, extra_fields)
        else:
            raise TwitterContentError('Twitter response should be list or dict, not %s' % response)

    def parse_response_object(self, resource, extra_fields=None):

        instance = self.model()
        # important to do it before calling parse method
        if extra_fields:
            instance.__dict__.update(extra_fields)
        instance.set_tweepy(resource)
        instance.parse()

        return instance

    def parse_response_list(self, response_list, extra_fields=None):

        instances = []
        for response in response_list:

            if not isinstance(response, tweepy.models.Model):
                log.error("Resource %s is not dictionary" % response)
                continue

            instance = self.parse_response_object(response, extra_fields)
            instances += [instance]

        return instances

class UserTwitterManager(TwitterManager):

    def fetch_followers_for_user(self, user, all=False, count=20, **kwargs):
        # https://dev.twitter.com/docs/api/1.1/get/followers/ids
        # https://dev.twitter.com/docs/api/1.1/get/followers/list
        if all:
            # TODO: make optimization: break cursor iteration after getting already existing user and switch to ids REST method
            user.followers.clear()
            cursor = tweepy.Cursor(user.tweepy._api.followers, id=user.id, count=200)
            for instance in cursor.items():
                instance = self.parse_response_object(instance)
                instance = self.get_or_create_from_instance(instance)
                user.followers.add(instance)
        else:
            raise NotImplementedError("Now implemented only with argument all=True")
        return user.followers.all()

class StatusTwitterManager(TwitterManager):

    @fetch_all(max_count=200)
    def fetch_for_user(self, user, count=20, **kwargs):
        # https://dev.twitter.com/docs/api/1.1/get/statuses/user_timeline
        instances = user.tweepy.timeline(count=count, **kwargs)
        instances = self.parse_response_list(instances, {'user_id': user.id})
        instances = [self.get_or_create_from_instance(instance) for instance in instances]
        return instances

class TwitterModel(models.Model):
    class Meta:
        abstract = True

    objects = models.Manager()

    def __init__(self, *args, **kwargs):
        super(TwitterModel, self).__init__(*args, **kwargs)

        # different lists for saving related objects
        self._external_links_post_save = []
        self._foreignkeys_pre_save = []
        self._external_links_to_add = []

    def _substitute(self, old_instance):
        '''
        Substitute new user with old one while updating in method Manager.get_or_create_from_instance()
        Can be overrided in child models
        '''
        self.id = old_instance.id

    def parse(self):
        '''
        Parse API response and define fields with values
        '''
        for key, value in self._response.items():
            if key == '_api':
                continue

            try:
                field, model, direct, m2m = self._meta.get_field_by_name(key)
            except FieldDoesNotExist:
                log.debug('Field with name "%s" doesn\'t exist in the model %s' % (key, type(self)))
                continue

            if isinstance(field, RelatedObject) and value:
                for item in value:
                    rel_instance = field.model.remote.parse_response_object(item)
                    self._external_links_post_save += [(field.field.name, rel_instance)]
            else:
                if isinstance(field, (models.BooleanField)):
                    value = bool(value)

                elif isinstance(field, (models.OneToOneField, models.ForeignKey)) and value:
                    rel_instance = field.rel.to.remote.parse_response_object(value)
                    value = rel_instance
                    if isinstance(field, models.ForeignKey):
                        self._foreignkeys_pre_save += [(key, rel_instance)]

                elif isinstance(field, (fields.CommaSeparatedCharField, models.CommaSeparatedIntegerField)) and isinstance(value, list):
                    value = ','.join([unicode(v) for v in value])

                elif isinstance(field, (models.CharField, models.TextField)) and value:
                    if isinstance(value, (str, unicode)):
                        value = value.strip()

                setattr(self, key, value)

    def save(self, *args, **kwargs):
        '''
        Save all related instances before or after current instance
        '''
        for field, instance in self._foreignkeys_pre_save:
            instance = instance.__class__.remote.get_or_create_from_instance(instance)
            instance.save()
            setattr(self, field, instance)
        self._foreignkeys_pre_save = []

        super(TwitterModel, self).save(*args, **kwargs)

        for field, instance in self._external_links_post_save:
            # set foreignkey to the main instance
            setattr(instance, field, self)
            instance.__class__.remote.get_or_create_from_instance(instance)
        self._external_links_post_save = []

        for field, instance in self._external_links_to_add:
            # if there is already connected instances, then continue, because it's hard to check for duplicates
            if getattr(self, field).count():
                continue
            getattr(self, field).add(instance)
        self._external_links_to_add = []

class TwitterCommonModel(TwitterModel):
    class Meta:
        abstract = True

    _tweepy_model = None
    _response = None

    id = models.BigIntegerField(u'', primary_key=True)
    created_at = models.DateTimeField(u'')
    lang = models.CharField(u'', max_length=10)
    entities = fields.JSONField()

    fetched = models.DateTimeField(u'Обновлено', null=True, blank=True)

    def set_tweepy(self, model):
        self._tweepy_model = model
        self._response = dict(self._tweepy_model.__dict__)

    @property
    def tweepy(self):
        if not self._tweepy_model:
            # get fresh instance with the same ID, set tweepy object and refresh attributes
            instance = self.__class__.remote.get(self.id)
            self.set_tweepy(instance.tweepy)
            self.parse()
        return self._tweepy_model

    def parse(self):
        self._response.pop('id_str')
        super(TwitterCommonModel, self).parse()

class User(TwitterCommonModel):
    class Meta:
        pass

    screen_name = models.CharField(u'', max_length=50, unique=True)

    name = models.CharField(u'', max_length=100)
    description = models.TextField(u'')
    location = models.CharField(u'', max_length=100)
    time_zone = models.CharField(u'', max_length=100, null=True)

    contributors_enabled = models.BooleanField(u'')
    default_profile = models.BooleanField(u'')
    default_profile_image = models.BooleanField(u'')
    follow_request_sent = models.BooleanField(u'')
    following = models.BooleanField(u'')
    geo_enabled = models.BooleanField(u'')
    is_translator = models.BooleanField(u'')
    notifications = models.BooleanField(u'')
    profile_use_background_image = models.BooleanField(u'')
    protected = models.BooleanField(u'')
    verified = models.BooleanField(u'')

    profile_background_image_url = models.URLField(u'')
    profile_background_image_url_https = models.URLField(u'')
    profile_background_tile = models.BooleanField(u'')
    profile_background_color = models.CharField(u'', max_length=6)
    profile_banner_url = models.URLField(u'')
    profile_image_url = models.URLField(u'')
    profile_image_url_https = models.URLField(u'')
    url = models.URLField(u'', null=True)

    profile_link_color = models.CharField(u'', max_length=6)
    profile_sidebar_border_color = models.CharField(u'', max_length=6)
    profile_sidebar_fill_color = models.CharField(u'', max_length=6)
    profile_text_color = models.CharField(u'', max_length=6)

    favorites_count = models.PositiveIntegerField(u'')
    followers_count = models.PositiveIntegerField(u'')
    friends_count = models.PositiveIntegerField(u'')
    listed_count = models.PositiveIntegerField(u'')
    statuses_count = models.PositiveIntegerField(u'')
    utc_offset = models.IntegerField(u'', null=True)

    followers = models.ManyToManyField('User', related_name='followings')

    objects = models.Manager()
    remote = UserTwitterManager(methods={
        'get': 'get_user',
    })

    def get_url(self):
        return 'https://twitter.com/%s' % self.screen_name

    def parse(self):
        self._response['favorites_count'] = self._response['favourites_count']
        if 'status' in self._response:
            self._response.pop('status')
        super(User, self).parse()

    def fetch_followers(self, **kwargs):
        return User.remote.fetch_followers_for_user(user=self, **kwargs)

    def fetch_statuses(self, **kwargs):
        return Status.remote.fetch_for_user(user=self, **kwargs)

class Status(TwitterCommonModel):
    class Meta:
        pass

    author = models.ForeignKey('User', related_name='statuses')

    text = models.TextField(u'')

    favorited = models.BooleanField(u'')
    retweeted = models.BooleanField(u'')
    truncated = models.BooleanField(u'')

    source = models.CharField(u'', max_length=100)
    source_url = models.URLField(u'', null=True)

    favorites_count = models.PositiveIntegerField(u'')
    retweets_count = models.PositiveIntegerField(u'')

# 'in_reply_to_screen_name': 'mrshoranweyhey',
# 'in_reply_to_status_id': 327912852486762497L,
# 'in_reply_to_status_id_str': '327912852486762497',
# 'in_reply_to_user_id = models.BigIntegerField(u'', primary_key=True)
# 'in_reply_to_user_id_str': '1323314442',
    in_reply_to_status = models.ForeignKey('Status', null=True, related_name='replies')
    in_reply_to_user = models.ForeignKey('User', null=True, related_name='replies')

#format doesn't clear:
# 'contributors': None,
# 'coordinates': None,
# 'geo': None,
# 'place': None,

    objects = models.Manager()
    remote = StatusTwitterManager(methods={
        'get': 'get_status',
    })

    def get_url(self):
        return 'https://twitter.com/%s/status/%d' % (self.author.screen_name, self.id)

    def parse(self):
        self._response['favorites_count'] = self._response['favorite_count']
        self._response['retweets_count'] = self._response['retweet_count']
#        if 'in_reply_to_user_id' in response:
#            response.pop('in_reply_to_user_id_str')
#        if 'in_reply_to_status_id_str' in response:
#            response.pop('in_reply_to_status_id_str')
        if 'user' in self._response:
            self._response.pop('user')

        if 'in_reply_to_screen_name' in self._response:
            self._response.pop('in_reply_to_screen_name')
        if 'in_reply_to_user_id_str' in self._response:
            self._response.pop('in_reply_to_user_id_str')
        if 'in_reply_to_status_id_str' in self._response:
            self._response.pop('in_reply_to_status_id_str')

        super(Status, self).parse()