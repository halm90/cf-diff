"""
Unit tests for the cf-diff tool cc_fetcher module
"""
import logging
import os
import pytest
import requests
import unittest

from mock import patch, MagicMock
from testfixtures import LogCapture

import cc_fetcher

#pylint: disable=protected-access, invalid-name


class TestFetcher(unittest.TestCase):
    """
    Test basic operation of the class.
    """
    _env_dict = {'CC_URL': 'a/b/{foundation}/d',
                 'FOUNDATION': 'foundation',
                 'LOG_LEVEL': 'DEBUG',
                 'OAUTH_CLIENT_ID': 'client_id',
                 'OAUTH_CLIENT_SECRET': 'shhhh',
                }
    def setUp(self):
        """
        Test setups: patch out functions across all tests.
        """
        patch('requests.packages.urllib3.disable_warnings').start()
        patch.dict(os.environ, self._env_dict).start()

    def tearDown(self):
        """
        Test teardowns: clean up test-wide patches.
        """
        patch.stopall()

    def testGetOauthUrlOK(self):
        """
        Test the _get_oauth_url function "happy path"
        """
        foundation = "myFoundation"
        url_fmt = "https://a/b/{foundation}/d"
        url = url_fmt.format(foundation=foundation)
        class GetRtn:
            status_code = requests.codes.ok
            @staticmethod
            def json():
                return {"links": {"uaa": {"href": url}}}

        with patch("requests.get", return_value=GetRtn()) as mock_get, \
             patch("logger.Logger"):
            fetcher = cc_fetcher.CCFetcher()
            fetcher._cc_url_format = url_fmt
            auth_url = fetcher._get_oauth_url(foundation)
        self.assertEqual(auth_url, '/'.join([url, "oauth", "token"]))
        mock_get.assert_called_once_with(url, verify=False)

    def testGetOauthUrlNotOK(self):
        """
        Test the _get_oauth_url function with non-200 from controller
        """
        foundation = "myFoundation"
        url_fmt = "https://a/b/{foundation}/d"
        url = url_fmt.format(foundation=foundation)
        class GetRtn:
            status_code = requests.codes.teapot
            @staticmethod
            def json():
                return {}

        with patch("requests.get", return_value=GetRtn()) as mock_get, \
             pytest.raises(cc_fetcher.FailedGetAccessToken), \
             patch("logger.Logger"):
            fetcher = cc_fetcher.CCFetcher()
            fetcher._cc_url_format = url_fmt
            auth_url = fetcher._get_oauth_url(foundation)
        mock_get.assert_called_once_with(url, verify=False)

    def testGetOauthUrlRaises(self):
        """
        Test the _get_oauth_url function with non-200 from controller
        """
        foundation = "myFoundation"
        url_fmt = "https://a/b/{foundation}/d"
        url = url_fmt.format(foundation=foundation)

        with patch("requests.get", side_effect=TypeError) as mock_get, \
             patch("logger.Logger"), \
             pytest.raises(cc_fetcher.FailedGetAccessToken):
            fetcher = cc_fetcher.CCFetcher()
            fetcher._cc_url_format = url_fmt
            auth_url = fetcher._get_oauth_url(foundation)
        mock_get.assert_called_once_with(url, verify=False)

    def testGetAccessToken(self):
        """
        Test the _get_access_token function.
        """
        foundation = "myFoundation"
        url = "a/b/c/d"
        secret = "shhh"
        appclient = "app client"
        test_token = "a token"
        mock_oauth = MagicMock()
        mock_fetch = MagicMock(return_value={'access_token': test_token})
        mock_oauth.fetch_token=mock_fetch
        with patch("oauthlib.oauth2.BackendApplicationClient",
                   return_value=appclient) as mock_back, \
             patch("requests_oauthlib.OAuth2Session",
                   return_value=mock_oauth) as mock_auth2, \
             patch("cc_fetcher.CCFetcher._get_oauth_url",
                   return_value=url) as mock_get_url:
            fetcher = cc_fetcher.CCFetcher()
            fetcher._oauth_id = self._env_dict['OAUTH_CLIENT_ID']
            fetcher._oauth_secret = secret
            token = fetcher._get_access_token(foundation)

        mock_get_url.assert_called_once_with(foundation)
        mock_back.assert_called_once_with(client_id=self._env_dict['OAUTH_CLIENT_ID'])

        mock_auth2.assert_called_once_with(client=appclient)
        mock_oauth.fetch_token.assert_called_once_with(token_url=url,
                                                       client_id=fetcher._oauth_id,
                                                       client_secret=fetcher._oauth_secret,
                                                       verify=False)
        self.assertEqual(token, test_token)

    def testGetAccessTokenErr(self):
        """
        Test the _get_access_token function.
        """
        foundation = "myFoundation"
        url = "a/b/c/d"
        secret = "shhh"
        appclient = "app client"
        test_token = "a token"
        mock_oauth = MagicMock()
        mock_fetch = MagicMock(side_effect=cc_fetcher.FailedGetAccessToken)
        mock_oauth.fetch_token=mock_fetch
        with patch("oauthlib.oauth2.BackendApplicationClient",
                   return_value=appclient) as mock_back, \
             patch("requests_oauthlib.OAuth2Session",
                   return_value=mock_oauth) as mock_auth2, \
             pytest.raises(cc_fetcher.FailedGetAccessToken), \
             patch("cc_fetcher.CCFetcher._get_oauth_url",
                   return_value=url) as mock_get_url, \
             LogCapture(level=logging.ERROR) as debug_log:
            fetcher = cc_fetcher.CCFetcher()
            fetcher.logger.setLevel(logging.DEBUG)
            fetcher._oauth_id = self._env_dict['OAUTH_CLIENT_ID']
            fetcher._oauth_secret = secret
            token = fetcher._get_access_token(foundation)

        mock_get_url.assert_called_once_with(foundation)
        mock_back.assert_called_once_with(client_id=self._env_dict['OAUTH_CLIENT_ID'])

        debug_log.check(('logger', 'ERROR',
                        'Failed retrieving access token from url {}'.format(url)))
        mock_auth2.assert_called_once_with(client=appclient)
        mock_oauth.fetch_token.assert_called_once_with(token_url=url,
                                                       client_id=fetcher._oauth_id,
                                                       client_secret=fetcher._oauth_secret,
                                                       verify=False)

    def testHeader(self):
        """
        Test the 'header' function
        """
        test_token = "a token"
        fetcher = cc_fetcher.CCFetcher()
        fetcher._access_token = test_token
        header = fetcher._header("some_foundation")

        self.assertEqual(header, {"Authorization": "bearer " + test_token})

    def testRequestAppCount(self):
        """
        Test the _request_app_count function
        """
        test_token = "a token"
        test_count = 42
        fetcher = cc_fetcher.CCFetcher()
        fetcher._access_token = test_token
        mock_reply = MagicMock()
        mock_reply.status_code = 200
        mock_reply.json = MagicMock(return_value={'total_results': test_count})

        with patch('requests.get', return_value=mock_reply) as mock_request:
            count = fetcher._request_app_count("some_foundation")
            self.assertEqual(count, test_count)

    def testAppCount(self):
        """
        Test the app_count function
        """
        test_foundation = "some_test_foundation"
        fetcher = cc_fetcher.CCFetcher()
        with patch('cc_fetcher.CCFetcher.app_count', return_value=42) as mock_count:
            count = fetcher.app_count(test_foundation)
            self.assertEqual(count, 42)
            mock_count.assert_called_once_with(test_foundation)
