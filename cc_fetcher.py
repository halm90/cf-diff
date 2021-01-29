"""
Interface to the CloudFoundry Cloud Controller REST API.
Note(s):
    1. Requires Python 3
"""
import oauthlib.oauth2
import requests
import requests_oauthlib
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from logger import Logger
from parameters import SysParams


class FailedGetAccessToken(Exception):
    """
    Failed to fetch an access token
    """

class CCFetcher(object):
    """
    Interface to the CloudFoundry Controller REST API.
    """
    def __init__(self):
        """
        Initialize the CC Fetcher interface.
        """
        self.logger = Logger().logger
        self.params = SysParams()
        self.logger.debug("Initializing CCFetcher")

        self._cc_url_format = self.params['CC_URL']
        self._oauth_id = self.params['OAUTH_CLIENT_ID']
        self._oauth_secret = self.params['OAUTH_CLIENT_SECRET']
        self.logger.debug("CCFetcher %s", self._oauth_id)
        self._access_token = None

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        super().__init__()

    def _get_oauth_url(self, foundation):
        """
        Contact the Cloud Controller and fetch the oauth URL for the foundation
        """
        try:
            cc_url = self._cc_url_format.format(foundation=foundation)
            cc_reply = requests.get(cc_url, verify=False)
            if cc_reply.status_code == requests.codes.ok:
                auth_url = cc_reply.json()['links']['uaa']['href']
                auth_url = '/'.join([auth_url, "oauth", "token"])
            else:
                raise FailedGetAccessToken
        except Exception:
            raise FailedGetAccessToken
        self.logger.debug("Oauth URL %s", auth_url)
        return auth_url

    def _get_access_token(self, foundation):
        """
        Get a Cloud Controller access token for this foundation.
        """
        try:
            auth_id = self._oauth_id
            oauth_url = None
            client = oauthlib.oauth2.BackendApplicationClient(client_id=auth_id)
            oauth = requests_oauthlib.OAuth2Session(client=client)
            oauth_url = self._get_oauth_url(foundation)
            self.logger.debug("Fetching token from %s", oauth_url)
            token = oauth.fetch_token(token_url=oauth_url,
                                      client_id=self._oauth_id,
                                      client_secret=self._oauth_secret,
                                      verify=False)
            access_token = token['access_token']
        except Exception:
            self.logger.exception("Failed retrieving access token from url %s",
                                  oauth_url or "unknown")
            self._access_token = None
            raise FailedGetAccessToken
        return access_token

    def _header(self, foundation):
        """
        Return the HTTP header including valid access token
        """
        token = self._access_token or self._get_access_token(foundation)
        return {"Authorization": "bearer " + token}

    def _request_app_count(self, foundation, version='v2', _isRetry=False):
        """
        Send the CloudController request and return only the number of
        'total_results'

        :param foundation: the name of the foundation
        """
        command = "apps"
        base_url = self._cc_url_format.format(foundation=foundation)
        url = "{}/{}/{}".format(base_url, version, command)
        result = None
        self.logger.debug("Sending request %s", url)
        try:
            reply = requests.get(url,
                                 headers=self._header(foundation),
                                 verify=False)
            if reply.status_code == requests.codes.ok:
                result = reply.json()['total_results']
            else:
                self.logger.warn("Request %s/%s failed: %s",
                                 version, command, reply.text)
        except FailedGetAccessToken:
            if _isRetry:
                self.logger.warn("Request failed, abort %s/%s",
                                 version, command)
            else:
                self.logger.warn("Request failed, refresh token and retry")
                self._access_token = None
                result = self._request_app_count(foundation, version=version,
                                                 _isRetry=True)
        except Exception as exn:
            self.logger.warn("Request error: %s", str(exn))

        return result

    def app_count(self, foundation):
        """
        Return the count of the number of (running) applications
        """
        return self._request_app_count(foundation)
