import logging

from django.conf import settings
from oauth_tokens.models import AccessToken
import tweepy


__all__ = ['api']

log = logging.getLogger('twitter_api')

ACCESS_TOKEN = getattr(settings, 'TWITTER_API_ACCESS_TOKEN', None)

TWITTER_CLIENT_ID = getattr(settings, 'OAUTH_TOKENS_TWITTER_CLIENT_ID', None)
TWITTER_CLIENT_SECRET = getattr(settings, 'OAUTH_TOKENS_TWITTER_CLIENT_SECRET', None)


def get_tokens():
    '''
    Get all vkontakte tokens list
    '''
    return AccessToken.objects.filter(provider='twitter').order_by('-granted_at')


def update_token():
    '''
    Update token from provider and return it
    '''
    return AccessToken.objects.fetch('twitter')


def get_api():
    '''
    Return API instance with latest token from database
    '''
    if ACCESS_TOKEN:
        token = ACCESS_TOKEN
    else:
        tokens = get_tokens()
        if not tokens:
            update_token()
            tokens = get_tokens()
        token = tokens[0].access_token

    delimeter = AccessToken.objects.get_token_class('twitter').delimeter
    auth = tweepy.OAuthHandler(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)

    token = token.split(delimeter)
    try:
        auth.access_token = tweepy.oauth.OAuthToken(token[0], token[1])
    except AttributeError:
        # dev version
        auth.access_token = token[0]
        auth.access_token_secret = token[1]

    return tweepy.API(auth)


def api(method, *args, **kwargs):
    '''
    Call API using access_token
    '''
    api = get_api()
    try:
        response = getattr(api, method)(*args, **kwargs)
#    except GraphException, e:
#        if e.code == 190:
#            update_token()
#            return graph(method, **kwargs)
#        elif 'An unexpected error has occurred. Please retry your request later' in str(e):
#            sleep(1)
#            return graph(method, **kwargs)
#        else:
#            raise e
#    except ValueError, e:
#        log.warning("ValueError: %s registered while executing method %s with params %s" % (e, method, kwargs))
# sometimes returns this dictionary, sometimes empty response, covered by test "test_empty_result"
#        data = {"error_code":1,"error_msg":"An unknown error occurred"}
#        return None
    except Exception, e:
        log.error("Unhandled error: %s registered while executing method %s with params args=%s, kwargs=%s" %
                  (e, method, args, kwargs))
        raise e

#    if getattr(response, 'error_code', None):
#        log.error("Error %s: %s returned while executing method %s with params %s" % (response.error_code, response.error_msg, method, kwargs))

    return response
