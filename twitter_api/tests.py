# -*- coding: utf-8 -*-
from django.test import TestCase
from twitter_api.utils import api

STATUS_ID = 327926550815207424

class TwitterApiTest(TestCase):

    def test_request(self):

        response = api('get_status', STATUS_ID)
        self.assertEqual(response.id, STATUS_ID)
        self.assertEqual(response.id_str, str(STATUS_ID))
        self.assertEqual(response.text, '@mrshoranweyhey Thanks for the love! How about a follow for a follow? :) ^LF')
        self.assertEqual(response.source_url, 'http://www.exacttarget.com/social')

#    def test_fetch_status(self):
#
#        response = api()
#
#        result = graph('8576093908/posts', **{'limit': 1000, 'until': 1345661805, 'offset': 0})
#        if result is not None:
#            self.assertEqual(result.error_code, 1)