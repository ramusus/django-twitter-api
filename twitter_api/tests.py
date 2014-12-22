# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils import six
import mock
from oauth_tokens.factories import UserCredentialsFactory
import tweepy

from .api import api_call, TwitterApi, TwitterError
from .factories import UserFactory, StatusFactory
from .models import User, Status
from .parser import get_replies

STATUS_ID = 327926550815207424
USER_ID = 813286
USER_SCREEN_NAME = 'BarackObama'
USER1_ID = 18807761
USER1_SCREEN_NAME = 'voronezh'
STATUS_MANY_REPLIES_ID = 538755896063832064
STATUS_MANY_RETWEETS_ID = 329231054282055680


class TwitterApiTest(TestCase):

    def test_request_error(self):

        with self.assertRaises(TwitterError):
            response = api_call('get_status')

    def test_api_instance_singleton(self):

        self.assertEqual(id(TwitterApi()), id(TwitterApi()))

    def test_request(self):

        response = api_call('get_status', STATUS_ID)
        self.assertEqual(response.text, '@mrshoranweyhey Thanks for the love! How about a follow for a follow? :) ^LF')
        self.assertEqual(response.source_url, 'http://www.exacttarget.com/social')

        response = api_call('get_user', USER_SCREEN_NAME)
        self.assertEqual(response.id, USER_ID)
        self.assertEqual(response.name, 'Barack Obama')

    def test_tweepy_properties(self):

        instance = User.remote.fetch(USER_ID)

        self.assertEqual(instance.screen_name, USER_SCREEN_NAME)
        self.assertIsInstance(instance.tweepy, tweepy.models.User)
        self.assertEqual(instance.tweepy.id_str, str(USER_ID))

    def test_fetch_status(self):

        self.assertEqual(Status.objects.count(), 0)

        instance = Status.remote.fetch(STATUS_ID)

        self.assertEqual(Status.objects.count(), 2)

        self.assertEqual(instance.id, STATUS_ID)
        self.assertEqual(instance.source, 'SocialEngage')
        self.assertEqual(instance.source_url, 'http://www.exacttarget.com/social')
        self.assertEqual(instance.text, '@mrshoranweyhey Thanks for the love! How about a follow for a follow? :) ^LF')
        self.assertEqual(instance.in_reply_to_status_id, 327912852486762497)
        self.assertEqual(instance.in_reply_to_user_id, 1323314442)
        self.assertEqual(instance.in_reply_to_status, Status.objects.get(id=327912852486762497))
        self.assertEqual(instance.in_reply_to_user, User.objects.get(id=1323314442))

    def test_fetch_user(self):

        instance = User.remote.fetch(USER_ID)

        self.assertEqual(instance.screen_name, USER_SCREEN_NAME)
        self.assertEqual(instance.id, USER_ID)
        self.assertEqual(instance.name, 'Barack Obama')
        self.assertEqual(instance.location, 'Washington, DC')
        self.assertEqual(instance.verified, True)
        self.assertEqual(instance.lang, 'en')
        self.assertGreater(instance.followers_count, 30886141)
        self.assertGreater(instance.friends_count, 600000)
        self.assertGreater(instance.listed_count, 192107)

        instance1 = User.remote.fetch(USER_SCREEN_NAME)
        self.assertEqual(instance.name, instance1.name)
        self.assertEqual(User.objects.count(), 1)

    def test_fetch_user_statuses(self):

        instance = UserFactory(id=USER_ID)

        self.assertEqual(Status.objects.count(), 0)

        instances = instance.fetch_statuses(count=30)

        self.assertEqual(len(instances), 30)
        self.assertEqual(len(instances), Status.objects.filter(author=instance).count())

        instances = instance.fetch_statuses(all=True, exclude_replies=True)

        self.assertGreater(len(instances), 3100)
        self.assertLess(len(instances), 4000)
        self.assertEqual(len(instances), Status.objects.filter(author=instance).count())

    def test_fetch_user_followers(self):

        instance = UserFactory(id=USER1_ID)

        self.assertEqual(User.objects.count(), 1)
        instances = instance.fetch_followers(all=True)
        self.assertGreater(len(instances), 870)
        self.assertLess(len(instances), 2000)
        self.assertIsInstance(instances[0], User)
        self.assertEqual(len(instances), User.objects.count() - 1)

    def test_fetch_user_followers_ids(self):

        instance = UserFactory(id=USER1_ID)

        self.assertEqual(User.objects.count(), 1)

        ids = instance.get_followers_ids(all=True)

        self.assertGreater(len(ids), 1000)
        self.assertLess(len(ids), 2000)
        self.assertIsInstance(ids[0], six.integer_types)
        self.assertEqual(User.objects.count(), 1)

    def test_fetch_status_retweets(self):

        instance = StatusFactory(id=STATUS_MANY_RETWEETS_ID)

        self.assertEqual(Status.objects.count(), 1)

        instances = instance.fetch_retweets()

        self.assertGreaterEqual(len(instances), 6)
        self.assertEqual(len(instances), Status.objects.count() - 1)

    def test_get_replies(self):
        """
            Check what ids[0] < ids[1] < ids[2] ...
            this also check what there is no duplicates
        """
        status = Status.remote.fetch(STATUS_MANY_REPLIES_ID)
        ids = get_replies(status)

        self.assertListEqual(ids, sorted(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_status_fetch_replies(self):
        status = Status.remote.fetch(STATUS_MANY_REPLIES_ID)

        self.assertEqual(Status.objects.count(), 1)

        replies = status.fetch_replies()

        self.assertGreater(replies.count(), 50)
        self.assertEqual(replies.count(), status.replies_count)
        self.assertEqual(replies.count(), Status.objects.count() - 1)

        self.assertEqual(replies[0].in_reply_to_status, status)
