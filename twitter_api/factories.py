import random

from django.utils import timezone

import factory
import models


class UserFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)
    screen_name = factory.Sequence(lambda n: n)
    created_at = factory.LazyAttribute(lambda o: timezone.now())
    entities = {}

    favorites_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    followers_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    friends_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    listed_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    statuses_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    utc_offset = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    class Meta:
        model = models.User


class StatusFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)
    created_at = factory.LazyAttribute(lambda o: timezone.now())
    entities = {}

    author = factory.SubFactory(UserFactory)
    favorites_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    retweets_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    class Meta:
        model = models.Status
