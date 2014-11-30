from datetime import datetime
import random

import factory
import models


class UserFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)
    screen_name = factory.Sequence(lambda n: n)
    created_at = datetime.now()
    entities = {}

    favorites_count = 0
    followers_count = 0
    friends_count = 0
    listed_count = 0
    statuses_count = 0
    utc_offset = 0

    class Meta:
        model = models.User


class StatusFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)
    created_at = datetime.now()
    entities = {}

    author = factory.SubFactory(UserFactory)
    favorites_count = 0
    retweets_count = 0

    class Meta:
        model = models.Status
