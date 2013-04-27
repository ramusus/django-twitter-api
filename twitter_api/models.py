# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.related import RelatedObject
from django.utils.translation import ugettext as _
from utils import api
import fields
import dateutil.parser
import logging
import re

log = logging.getLogger('twitter_api')

class TwitterManager(models.Manager):
    '''
    Twitter Manager for RESTful CRUD operations
    '''
    def __init__(self, remote_pk=None, resource_path='%s', *args, **kwargs):
        if '%s' not in resource_path:
            raise ValueError('Argument resource_path must contains %s character')

        self.resource_path = resource_path
        self.remote_pk = remote_pk or ('graph_id',)
        if not isinstance(self.remote_pk, tuple):
            self.remote_pk = (self.remote_pk,)

        super(TwitterManager, self).__init__(*args, **kwargs)

    def get_by_url(self, url):
        '''
        Return object by url
        '''
        m = re.findall(r'(?:https?://)?(?:www\.)?facebook\.com/(.+)/?', url)
        if not len(m):
            raise ValueError("Url should be started with http://facebook.com/")

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

    def get_or_create_from_resource(self, resource):

        instance = self.model()
        instance.parse(dict(resource))

        return self.get_or_create_from_instance(instance)

    def fetch(self, *args, **kwargs):
        '''
        Retrieve and save object to local DB
        '''
        response = graph(self.resource_path % args[0], **kwargs)
        instance = self.get_or_create_from_resource(response.toDict())

        return instance

class TwitterModel(models.Model):
    class Meta:
        abstract = True

    remote_pk_field = 'id'

    objects = models.Manager()

    def __init__(self, *args, **kwargs):
        super(TwitterModel, self).__init__(*args, **kwargs)

        # different lists for saving related objects
        self._external_links_post_save = []
        self._foreignkeys_post_save = []
        self._external_links_to_add = []

    def _substitute(self, old_instance):
        '''
        Substitute new user with old one while updating in method Manager.get_or_create_from_instance()
        Can be overrided in child models
        '''
        self.id = old_instance.id

    def parse(self, response):
        '''
        Parse API response and define fields with values
        '''
        for key, value in response.items():

            if key == self.remote_pk_field:
                key = 'graph_id'

            try:
                field, model, direct, m2m = self._meta.get_field_by_name(key)
            except FieldDoesNotExist:
                log.debug('Field with name "%s" doesn\'t exist in the model %s' % (key, type(self)))
                continue

            if isinstance(field, RelatedObject) and value:
                for item in value:
                    rel_instance = field.model()
                    rel_instance.parse(dict(item))
                    self._external_links_post_save += [(field.field.name, rel_instance)]
            else:
                if isinstance(field, models.DateTimeField) and value:
                    value = dateutil.parser.parse(value)#.replace(tzinfo=None)

                elif isinstance(field, (models.OneToOneField, models.ForeignKey)) and value:
                    rel_instance = field.rel.to()
                    rel_instance.parse(dict(value))
                    value = rel_instance
                    if isinstance(field, models.ForeignKey):
                        self._foreignkeys_post_save += [(key, rel_instance)]

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
        for field, instance in self._foreignkeys_post_save:
            instance = instance.__class__.remote.get_or_create_from_instance(instance)
            instance.save()
            setattr(self, field, instance)
        self._foreignkeys_post_save = []

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

    id = models.BigIntegerField(u'', primary_key=True)
    id_str = models.CharField(u'', max_length=30)

    created_at = models.DateTimeField(u'')

    lang = models.CharField(u'', max_length=10)

    entities = fields.PickleField()

class User(TwitterCommonModel):
    class Meta:
        pass

    screen_name = models.CharField(u'', max_length=50, unique=True)

    name = models.CharField(u'', max_length=100)
    description = models.CharField(u'', max_length=100)
    location = models.CharField(u'', max_length=100)
    time_zone = models.CharField(u'', max_length=100)

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
    url = models.URLField(u'')

    profile_link_color = models.CharField(u'', max_length=6)
    profile_sidebar_border_color = models.CharField(u'', max_length=6)
    profile_sidebar_fill_color = models.CharField(u'', max_length=6)
    profile_text_color = models.CharField(u'', max_length=6)

    favourites_count = models.PositiveIntegerField(u'')
    followers_count = models.PositiveIntegerField(u'')
    friends_count = models.PositiveIntegerField(u'')
    listed_count = models.PositiveIntegerField(u'')
    statuses_count = models.PositiveIntegerField(u'')
    utc_offset = models.IntegerField(u'')

    status = models.ForeignKey('Status')

    def get_url(self):
        return 'https://twitter.com/%s' % self.screen_name


class Status(TwitterCommonModel):
    class Meta:
        pass

    author = models.ForeignKey('User')
    user = models.ForeignKey('User')

    text = models.TextField(u'')

    favorited = models.BooleanField(u'')
    retweeted = models.BooleanField(u'')
    truncated = models.BooleanField(u'')

    source = models.CharField(u'', max_length=100)
    source_url = models.URLField(u'')

    favorite_count = models.PositiveIntegerField(u'')
    retweet_count = models.PositiveIntegerField(u'')

# 'in_reply_to_screen_name': 'mrshoranweyhey',
# 'in_reply_to_status_id': 327912852486762497L,
# 'in_reply_to_status_id_str': '327912852486762497',
# 'in_reply_to_user_id = models.BigIntegerField(u'', primary_key=True)
# 'in_reply_to_user_id_str': '1323314442',
    in_reply_to_status = models.ForeignKey('Status')
    in_reply_to_user = models.ForeignKey('User')

    def parse(self, response):

#        if 'in_reply_to_user_id' in response:
#            response.pop('in_reply_to_user_id_str')
#        if 'in_reply_to_status_id_str' in response:
#            response.pop('in_reply_to_status_id_str')

        if 'in_reply_to_screen_name' in response:
            response.pop('in_reply_to_screen_name')
        if 'in_reply_to_user_id_str' in response:
            response.pop('in_reply_to_user_id_str')
        if 'in_reply_to_status_id_str' in response:
            response.pop('in_reply_to_status_id_str')

        super(Status, self).parse(response)

# 'contributors': None,
# 'coordinates': None,
# 'geo': None,
# 'place': None,
