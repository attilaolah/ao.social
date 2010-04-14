import urllib

from ao.social.oauth_ import OAuthClient
from ao.social.utils import json, urlfetch

from oauth import oauth


class TwitterClient(OAuthClient):
    """Twitter-specific OAuth client."""

    _default_config = {
        'request_token_url': 'https://twitter.com/oauth/request_token',
        'access_token_url': 'https://twitter.com/oauth/access_token',
        'authorize_url': 'https://twitter.com/oauth/authorize',
        'account_verification_url':
            'https://twitter.com/account/verify_credentials.json',
        'update_url': 'https://api.twitter.com/1/statuses/update.%(format)s',
    }

    def lookup_user_info(self, access_token, access_secret):
        """Lookup User Info.

        Same as `get_user_info` except that it uses a stored access_token and
        access_secret.

        """

        response = self._make_protected_request(access_token, access_secret)

        return json.loads(response.content)

    def post(self, text, token='', secret=''):
        """Do a Twitter profile update."""

        url = self._config['update_url'] % {
            'format': 'json',
        }

        data = {
            'status': text.encode('utf-8'),
        }
        data = urllib.urlencode(data)

        token = oauth.OAuthToken(token, secret)
        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer,
            token=token,
            http_url=url,
            http_method='POST',
        )
        request.set_parameter('status', text)
        request.sign_request(
            self._signature_method,
            self._consumer,
            token,
        )

        response = urlfetch.fetch(
            url,
            payload=data,
            method=urlfetch.POST,
            headers=request.to_header(),
        )

        return json.loads(response.content)
