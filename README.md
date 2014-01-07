# Django Twitter API

[![Build Status](https://travis-ci.org/ramusus/django-twitter-api.png?branch=master)](https://travis-ci.org/ramusus/django-twitter-api) [![Coverage Status](https://coveralls.io/repos/ramusus/django-twitter-api/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-twitter-api)

Application for interacting with Twitter API objects using Django model interface

## Installation

    pip install django-twitter-api

Add into `settings.py` lines:

    INSTALLED_APPS = (
        ...
        'oauth_tokens',
        'taggit',
        'twitter-api',
    )

    # oauth-tokens settings
    OAUTH_TOKENS_HISTORY = True                                        # to keep in DB expired access tokens
    OAUTH_TOKENS_TWITTER_CLIENT_ID = ''                                # application ID
    OAUTH_TOKENS_TWITTER_CLIENT_SECRET = ''                            # application secret key
    OAUTH_TOKENS_TWITTER_USERNAME = ''                                 # user login
    OAUTH_TOKENS_TWITTER_PASSWORD = ''                                 # user password

    # twitter-api settings
    def twitter_api_get_token_callback():
        import tweepy
        auth = tweepy.OAuthHandler(OAUTH_TOKENS_TWITTER_CLIENT_ID, OAUTH_TOKENS_TWITTER_CLIENT_SECRET)
        auth.username = ''                                              # username
        auth.access_token = tweepy.oauth.OAuthToken('', '')             # pair of access tokens
        auth.request_token = tweepy.oauth.OAuthToken('', '')            # pair of request tokens
        return auth

    TWITTER_API_ACCESS_TOKEN_CALLBACK = twitter_api_get_token_callback

## Usage examples

### Simple API request

    >>> from twitter_api.utils import api
    >>> response = api('get_status', 327926550815207424)
    >>> response.text
    '@mrshoranweyhey Thanks for the love! How about a follow for a follow? :) ^LF'
    >>> response.source_url
    'http://www.exacttarget.com/social'
    >>> response = api('get_user', 'BarackObama')
    >>> response.id, response.name
    (813286, 'Barack Obama')

### Fetch status by ID

    >>> from models import Status
    >>> status = Status.remote.fetch(327926550815207424)
    >>> status
    <Status: Coca-Cola: @mrshoranweyhey Thanks for the love! How about a follow for a follow? :) ^LF>
    >>> status.in_reply_to_status
    <Status: FOOODDD: @CocaCola I LOVE U SO MUCH PLEASE FOLLOW ME IT WOULD BE MY DREAM>

### Fetch user by ID and user name

    >>> from models import User
    >>> User.remote.fetch(813286)
    <User: Barack Obama>
    >>> User.remote.fetch('BarackObama')
    <User: Barack Obama>

### Fetch statuses of user

    >>> from models import User
    >>> user = User.remote.fetch(813286)
    >>> user.fetch_statuses(count=30)
    [<Status: Barack Obama: RT @obamacare: Want to know something awesome? http://t.co/bDLs2MJbid>,
     <Status: Barack Obama: RT @WhiteHouse: Thanks in part to the Affordable Care Act, health care costs are growing at the slowest rate in more than 50 years → http:/…>,
     <Status: Barack Obama: There's a new deadline to #GetCovered. Enroll before January 15th and be covered starting February 1st: http://t.co/dVPtUdoZCI>,
     ...]

### Fetch followers of user

    >>> from models import User
    >>> user = User.remote.fetch(813286)
    >>> user.fetch_followers(all=True)
    [<User: Raymonde Haris>, <User: Dark king>, <User: Byby_Cuachaa>, '...(remaining elements truncated)...']

### Fetch retweets of status

    >>> from models import Status
    >>> status = Status.remote.fetch(329231054282055680)
    >>> status.fetch_retweets()
    [<Status: Alexandr: RT @Tele2Russia: Друзья, мы представляем вам новую услугу «Везде ноль» http://t.co/lDT1wmnhUU>,
     <Status: Andrew Boriskin: RT @Tele2Russia: Друзья, мы представляем вам новую услугу «Везде ноль» http://t.co/lDT1wmnhUU>,
     <Status: Денис Цуканов: RT @Tele2Russia: Друзья, мы представляем вам новую услугу «Везде ноль» http://t.co/lDT1wmnhUU>,
     ...]