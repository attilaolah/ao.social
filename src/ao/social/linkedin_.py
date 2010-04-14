import re

from ao.social.oauth_ import OAuthClient

from xml.dom import minidom


rx_key = re.compile('<url>.*?\?.*?;key=(.*?)(&.*|</url>)')


class XML(object):
    """Simple one-level XML node getter"""

    def __init__(self, data):
        """Parse the DOM."""

        self._xml = minidom.parseString(data)#.decode('utf-8'))

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
        'update_url': 'XXXTODO',
    }

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

        raise ValueError, 'POST NOT IMPLEMENTED YET'
