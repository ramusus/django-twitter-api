import json
import re

from oauth_tokens.models import AccessToken

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/33.0',
    'Accept_Language': 'en'
}
IDS_RE = re.compile('data-tweet-id="(\d+)"')


def get_replies(status):
    "Return all replies ids of tweet"

    ids_list = []

    url = 'https://twitter.com/i/%s/conversation/%s' % (status.author.screen_name, status.pk)
    params = {'max_position': 0}
    headers = dict(HEADERS)
    headers['X-Requested-With'] = 'XMLHttpRequest'

    ar = AccessToken.objects.get_token('twitter').auth_request

    while 1:
        r = ar.authorized_request(url=url, params=params, headers=headers)
        response = r.json()

        ids = IDS_RE.findall(response['items_html'])
        ids_list += ids

        if response['has_more_items']:
            params = {'max_position': ids.pop()}
        else:
            break

    return ids_list
