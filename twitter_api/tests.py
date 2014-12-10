# -*- coding: utf-8 -*-
from django.test import TestCase
import tweepy

from .factories import UserFactory, StatusFactory
from .models import User, Status
from .utils import api


STATUS_ID = 327926550815207424
USER_ID = 813286
USER_SCREEN_NAME = 'BarackObama'
USER1_ID = 18807761
USER1_SCREEN_NAME = 'voronezh'


class TwitterApiTest(TestCase):

    def test_request(self):

        response = api('get_status', STATUS_ID)
        self.assertEqual(response.text, '@mrshoranweyhey Thanks for the love! How about a follow for a follow? :) ^LF')
        self.assertEqual(response.source_url, 'http://www.exacttarget.com/social')

        response = api('get_user', USER_SCREEN_NAME)
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
        self.assertIsInstance(ids[0], long)
        self.assertEqual(User.objects.count(), 1)

    def test_fetch_status_retweets(self):

        instance = StatusFactory(id=329231054282055680)

        self.assertEqual(Status.objects.count(), 1)

        instances = instance.fetch_retweets()

        self.assertGreaterEqual(len(instances), 6)
        self.assertEqual(len(instances), Status.objects.count() - 1)
