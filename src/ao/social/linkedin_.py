import re

from ao.social.oauth_ import OAuthClient
from ao.social.utils import urlfetch

from oauth import oauth

from xml.dom import minidom


rx_key = re.compile('<url>.*?\?.*?;key=(.*?)(&.*|</url>)')


class XML(object):
    """Simple one-level XML node getter"""

    def __init__(self, data):
        """Parse the DOM."""

        self._xml = minidom.parseString(data)

    def __getitem__(self, name):
        """Return the value of the named text node."""

        return self._xml.getElementsByTagName(name)[0].childNodes[0].nodeValue


class LinkedInClient(OAuthClient):
    """LinkedIn-specific OAuth client."""

    _default_config = {
        'request_token_url': 'https://api.linkedin.com/uas/oauth/requestToken',
        'access_token_url': 'https://api.linkedin.com/uas/oauth/accessToken',
        'authorize_url': 'https://api.linkedin.com/uas/oauth/authorize',
        'account_verification_url':
            'https://api.linkedin.com/v1/people/~',
        'update_url': 'http://api.linkedin.com/v1/people/~/current-status',
    }
    _set_status = '<?xml version="1.0" encoding="UTF-8"?><current-status>'\
        '%(status)s</current-status>'

    def lookup_user_info(self, access_token, access_secret):
        """Lookup User Info.

        Same as `get_user_info` except that it uses a stored access_token and
        access_secret.

        """

        resp = self._make_protected_request(access_token, access_secret, True)
        xml = XML(resp.content)

        return {
            'id': rx_key.search(resp.content).group(1),
            'first_name': xml['first-name'],
            'last_name': xml['last-name'],
        }

    def post(self, text, token='', secret=''):
        """Do a LinkedIn profile update."""

        url = self._config['update_url']

        data = self._set_status % {
            'status': text.encode('utf-8'),
        }

        token = oauth.OAuthToken(token, secret)
        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer,
            token=token,
            http_url=url,
            http_method='PUT',
        )
        request.sign_request(
            self._signature_method,
            self._consumer,
            token,
        )

        urlfetch.fetch(
            url,
            payload=data,
            method=urlfetch.PUT,
            headers=request.to_header(),
        )
