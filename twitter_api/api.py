from datetime import datetime
import sys

from django.conf import settings
from oauth_tokens.api import ApiAbstractBase, Singleton
from oauth_tokens.models import AccessToken
from tweepy import TweepError as TwitterError
import tweepy

__all__ = ['api_call', 'TwitterError']

TWITTER_CLIENT_ID = getattr(settings, 'OAUTH_TOKENS_TWITTER_CLIENT_ID', None)
TWITTER_CLIENT_SECRET = getattr(settings, 'OAUTH_TOKENS_TWITTER_CLIENT_SECRET', None)

@property
def code(self):
    return self[0][0]['code'] if 'code' in self[0][0] else 0

TwitterError.code = code


class TwitterApi(ApiAbstractBase):

    __metaclass__ = Singleton

    provider = 'twitter'
    error_class = TwitterError
    sleep_repeat_error_messages = [
        'Failed to send request:'
    ]

    def get_consistent_token(self):
        return getattr(settings, 'TWITTER_API_ACCESS_TOKEN', None)

    def get_api(self, token):
        delimeter = AccessToken.objects.get_token_class(self.provider).delimeter
        auth = tweepy.OAuthHandler(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
        auth.set_access_token(*token.split(delimeter))
        return tweepy.API(auth, wait_on_rate_limit=True, retry_count=3, retry_delay=1, retry_errors=set([401, 404, 500, 503]))

    def get_api_response(self, *args, **kwargs):
        return getattr(self.api, self.method)(*args, **kwargs)

    def log_and_raise(self, e, *args, **kwargs):
        self.logger.error("Error '%s'. Method %s, args: %s, kwargs: %s, recursion count: %d" % (
            e, self.method, args, kwargs, self.recursion_count))
        error_class = type(e)
        e.message[0]['message'] = '%s while executing method %s with args %s, kwargs %s' % (
            e.message[0]['message'], self.method, args, kwargs)
        error = error_class(e.message)
        raise error_class, error, sys.exc_info()[2]

    def handle_error_no_active_tokens(self, e, *args, **kwargs):
        if self.used_access_tokens and self.api:

            # check if all tokens are blocked by rate limits response
            try:
                rate_limit_status = self.api.rate_limit_status()
            except self.error_class, e:
                # handle rate limit on rate_limit_status request -> wait 15 min and repeat main request
                if self.get_error_code(e) == 88:
                    self.used_access_tokens = []
                    return self.sleep_repeat_call(seconds=60 * 15, *args, **kwargs)
                else:
                    raise

            # TODO: wrong logic, path is different completelly sometimes
            method = '/%s' % self.method.replace('_', '/')
            status = [methods for methods in rate_limit_status['resources'].values() if method in methods][0][method]
            if status['remaining'] == 0:
                secs = (datetime.fromtimestamp(status['reset']) - datetime.now()).seconds
                self.used_access_tokens = []
                return self.sleep_repeat_call(seconds=secs, *args, **kwargs)
            else:
                return self.repeat_call(*args, **kwargs)
        else:
            return super(TwitterApi, self).handle_error_no_active_tokens(e, *args, **kwargs)

    def handle_error_code_88(self, e, *args, **kwargs):
        # Rate limit exceeded
        self.logger.warning("Rate limit exceeded: %s, method: %s recursion count: %d" %
                            (e, self.method, self.recursion_count))
        token = AccessToken.objects.get_token_class(self.provider).delimeter.join(
            [self.api.auth.access_token, self.api.auth.access_token_secret])
        self.used_access_tokens += [token]
        return self.repeat_call(*args, **kwargs)

    # def handle_error_code_63(self, e, *args, **kwargs):
    #     # User has been suspended.
    #     self.refresh_tokens()
    #     return self.repeat_call(*args, **kwargs)


def api_call(*args, **kwargs):
    api = TwitterApi()
    return api.call(*args, **kwargs)
