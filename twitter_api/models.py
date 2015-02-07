# -*- coding: utf-8 -*-
import logging
import re

import tweepy
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.related import RelatedObject
from django.utils import timezone
from django.utils.translation import ugettext as _
from m2m_history.fields import ManyToManyHistoryField

from . import fields
from .api import TwitterError, api_call
from .decorators import fetch_all
from .parser import get_replies

__all__ = ['User', 'Status', 'TwitterContentError', 'TwitterModel', 'TwitterManager', 'UserManager']

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
        m = re.findall(r'(?:https?://)?(?:www\.)?twitter\.com/([^/]+)/?', url)
        if not len(m):
            raise ValueError("Url should be started with https://twitter.com/")

        return self.get_by_slug(m[0])

    def get_by_slug(self, slug):
        '''
        Return object by slug
        '''
        # TODO: change to self.get method
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

    def api_call(self, method, *args, **kwargs):
        if method in self.methods:
            method = self.methods[method]
        return api_call(method, *args, **kwargs)

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
        extra_fields['fetched'] = timezone.now()
        response = self.api_call('get', *args, **kwargs)

        return self.parse_response(response, extra_fields)

    def parse_response(self, response, extra_fields=None):
        # if response is None:
        #     return []
        # el
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


class UserManager(TwitterManager):

    def get_followers_ids_for_user(self, user, all=False, count=5000, **kwargs):
        # https://dev.twitter.com/docs/api/1.1/get/followers/ids
        if all:
            cursor = tweepy.Cursor(user.tweepy._api.followers_ids, id=user.pk, count=count)
            return list(cursor.items())
        else:
            raise NotImplementedError("This method implemented only with argument all=True")

    def fetch_followers_for_user(self, user, all=False, count=200, **kwargs):
        # https://dev.twitter.com/docs/api/1.1/get/followers/list
        # in docs default count is 20, but maximum is 200
        if all:
            # TODO: make optimization: break cursor iteration after getting already
            # existing user and switch to ids REST method
            user.followers.clear()
            cursor = tweepy.Cursor(user.tweepy._api.followers, id=user.pk, count=count)
            for instance in cursor.items():
                instance = self.parse_response_object(instance)
                instance = self.get_or_create_from_instance(instance)
                user.followers.add(instance)
        else:
            raise NotImplementedError("This method implemented only with argument all=True")
        return user.followers.all()

    def get_or_create_from_instance(self, instance):
        try:
            instance_old = self.model.objects.get(screen_name=instance.screen_name)
            if instance_old.pk == instance.pk:
                instance.save()
            else:
                # perhaps we already have old User with the same screen_name, but different id
                try:
                    self.fetch(instance_old.pk)
                except TwitterError, e:
                    if e.code == 34:
                        instance_old.delete()
                        instance.save()
                    else:
                        raise
            return instance
        except self.model.DoesNotExist:
            return super(UserManager, self).get_or_create_from_instance(instance)


class StatusManager(TwitterManager):

    @fetch_all(max_count=200)
    def fetch_for_user(self, user, count=20, **kwargs):
        # https://dev.twitter.com/docs/api/1.1/get/statuses/user_timeline
        response = self.api_call('user_timeline', id=user.pk, count=count, **kwargs)
        instances = self.parse_response(response, {'user_id': user.pk})
        ids = [self.get_or_create_from_instance(instance).pk for instance in instances]
        return self.filter(pk__in=ids)

    def fetch_retweets(self, status, count=100, **kwargs):
        # https://dev.twitter.com/docs/api/1.1/get/statuses/retweets/%3Aid
        response = self.api_call('retweets', id=status.pk, count=count, **kwargs)
        instances = self.parse_response(response)
        ids = [self.get_or_create_from_instance(instance).pk for instance in instances]
        return self.filter(pk__in=ids)

    def fetch_replies(self, status, **kwargs):
        instances = Status.objects.none()

        replies_ids = get_replies(status)
        for id in replies_ids:
            instance = Status.remote.fetch(id)
            instances |= Status.objects.filter(pk=instance.pk)

        status.replies_count = instances.count()
        status.save()

        return instances


class TwitterModel(models.Model):

    objects = models.Manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(TwitterModel, self).__init__(*args, **kwargs)

        # different lists for saving related objects
        self._external_links_post_save = []
        self._foreignkeys_pre_save = []
        self._external_links_to_add = []

    def save(self, *args, **kwargs):
        '''
        Save all related instances before or after current instance
        '''
        for field, instance in self._foreignkeys_pre_save:
            instance = instance.__class__.remote.get_or_create_from_instance(instance)
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

    def _substitute(self, old_instance):
        '''
        Substitute new user with old one while updating in method Manager.get_or_create_from_instance()
        Can be overrided in child models
        '''
        self.pk = old_instance.pk

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

    def _get_foreignkeys_for_fields(self, *args):

        for field_name in args:
            model = self._meta.get_field(field_name).rel.to
            try:
                id = int(self._response.pop(field_name + '_id', None))
                setattr(self, field_name, model.objects.get(pk=id))
            except model.DoesNotExist:
                try:
                    self._foreignkeys_pre_save += [(field_name, model.remote.get(id))]
                except tweepy.TweepError:
                    pass
            except TypeError:
                pass


class TwitterBaseModel(TwitterModel):

    _tweepy_model = None
    _response = None

    id = models.BigIntegerField(primary_key=True)
    created_at = models.DateTimeField()
    lang = models.CharField(max_length=10)
    entities = fields.JSONField()

    fetched = models.DateTimeField(u'Fetched', null=True, blank=True)

    class Meta:
        abstract = True

    def set_tweepy(self, model):
        self._tweepy_model = model
        self._response = dict(self._tweepy_model.__dict__)

    @property
    def tweepy(self):
        if not self._tweepy_model:
            # get fresh instance with the same ID, set tweepy object and refresh attributes
            instance = self.__class__.remote.get(self.pk)
            self.set_tweepy(instance.tweepy)
            self.parse()
        return self._tweepy_model

    def parse(self):
        self._response.pop('id_str', None)
        super(TwitterBaseModel, self).parse()

    def get_url(self):
        return 'https://twitter.com/%s' % self.slug


class User(TwitterBaseModel):

    screen_name = models.CharField(u'Screen name', max_length=50, unique=True)

    name = models.CharField(u'Name', max_length=100)
    description = models.TextField(u'Description')
    location = models.CharField(u'Location', max_length=100)
    time_zone = models.CharField(u'Time zone', max_length=100, null=True)

    contributors_enabled = models.BooleanField(u'Contributors enabled', default=False)
    default_profile = models.BooleanField(u'Default profile', default=False)
    default_profile_image = models.BooleanField(u'Default profile image', default=False)
    follow_request_sent = models.BooleanField(u'Follow request sent', default=False)
    following = models.BooleanField(u'Following', default=False)
    geo_enabled = models.BooleanField(u'Geo enabled', default=False)
    is_translator = models.BooleanField(u'Is translator', default=False)
    notifications = models.BooleanField(u'Notifications', default=False)
    profile_use_background_image = models.BooleanField(u'Profile use background image', default=False)
    protected = models.BooleanField(u'Protected', default=False)
    verified = models.BooleanField(u'Verified', default=False)

    profile_background_image_url = models.URLField(max_length=300)
    profile_background_image_url_https = models.URLField(max_length=300)
    profile_background_tile = models.BooleanField(default=False)
    profile_background_color = models.CharField(max_length=6)
    profile_banner_url = models.URLField(max_length=300)
    profile_image_url = models.URLField(max_length=300)
    profile_image_url_https = models.URLField(max_length=300)
    url = models.URLField(max_length=300, null=True)

    profile_link_color = models.CharField(max_length=6)
    profile_sidebar_border_color = models.CharField(max_length=6)
    profile_sidebar_fill_color = models.CharField(max_length=6)
    profile_text_color = models.CharField(max_length=6)

    favorites_count = models.PositiveIntegerField()
    followers_count = models.PositiveIntegerField()
    friends_count = models.PositiveIntegerField()
    listed_count = models.PositiveIntegerField()
    statuses_count = models.PositiveIntegerField()
    utc_offset = models.IntegerField(null=True)

    followers = ManyToManyHistoryField('User', versions=True)

    objects = models.Manager()
    remote = UserManager(methods={
        'get': 'get_user',
    })

    def __unicode__(self):
        return self.name

    @property
    def slug(self):
        return self.screen_name

    def parse(self):
        self._response['favorites_count'] = self._response.pop('favourites_count', None)
        self._response.pop('status', None)
        super(User, self).parse()

    def fetch_followers(self, **kwargs):
        return User.remote.fetch_followers_for_user(user=self, **kwargs)

    def get_followers_ids(self, **kwargs):
        return User.remote.get_followers_ids_for_user(user=self, **kwargs)

    def fetch_statuses(self, **kwargs):
        return Status.remote.fetch_for_user(user=self, **kwargs)


class Status(TwitterBaseModel):

    author = models.ForeignKey('User', related_name='statuses')

    text = models.TextField()

    favorited = models.BooleanField(default=False)
    retweeted = models.BooleanField(default=False)
    truncated = models.BooleanField(default=False)

    source = models.CharField(max_length=100)
    source_url = models.URLField(null=True)

    favorites_count = models.PositiveIntegerField()
    retweets_count = models.PositiveIntegerField()
    replies_count = models.PositiveIntegerField(null=True)

    in_reply_to_status = models.ForeignKey('Status', null=True, related_name='replies')
    in_reply_to_user = models.ForeignKey('User', null=True, related_name='replies')

    favorites_users = ManyToManyHistoryField('User', related_name='favorites')
    retweeted_status = models.ForeignKey('Status', null=True, related_name='retweets')

    place = fields.JSONField(null=True)
    # format the next fields doesn't clear
    contributors = fields.JSONField(null=True)
    coordinates = fields.JSONField(null=True)
    geo = fields.JSONField(null=True)

    objects = models.Manager()
    remote = StatusManager(methods={
        'get': 'get_status',
    })

    def __unicode__(self):
        return u'%s: %s' % (self.author, self.text)

    @property
    def slug(self):
        return '/%s/status/%d' % (self.author.screen_name, self.pk)

    def parse(self):
        self._response['favorites_count'] = self._response.pop('favorite_count', 0)
        self._response['retweets_count'] = self._response.pop('retweet_count', 0)

        self._response.pop('user', None)
        self._response.pop('in_reply_to_screen_name', None)
        self._response.pop('in_reply_to_user_id_str', None)
        self._response.pop('in_reply_to_status_id_str', None)

        self._get_foreignkeys_for_fields('in_reply_to_status', 'in_reply_to_user')

        super(Status, self).parse()

    def fetch_retweets(self, **kwargs):
        return Status.remote.fetch_retweets(status=self, **kwargs)

    def fetch_replies(self, **kwargs):
        return Status.remote.fetch_replies(status=self, **kwargs)
