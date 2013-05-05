from models import User, Status
from datetime import datetime
import factory
import random

class UserFactory(factory.Factory):
    FACTORY_FOR = User

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

class StatusFactory(factory.Factory):
    FACTORY_FOR = Status

    id = factory.Sequence(lambda n: n)
    created_at = datetime.now()
    entities = {}

    author = factory.SubFactory(UserFactory)
    favorites_count = 0
    retweets_count = 0