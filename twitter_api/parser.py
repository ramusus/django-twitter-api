import json
import re
from bs4 import BeautifulSoup
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
    ar = AccessToken.objects.get_token('twitter').auth_request

    headers = dict(HEADERS)
    headers['X-Requested-With'] = 'XMLHttpRequest'

    resp = ar.authorized_request(url=status.get_url(), headers=headers)
    params = {'max_position': BeautifulSoup(resp.content).find('div', **{'class': 'stream-container'})['data-min-position']}

    while True:
        r = ar.authorized_request(url=url, params=params, headers=headers)
        response = r.json()
        if 'descendants' in response:
            response = response['descendants']

        ids = IDS_RE.findall(response['items_html'])
        ids_list += ids

        if response['has_more_items'] and len(ids):
            params = {'max_position': response['min_position']}
        else:
            break

    return ids_list
