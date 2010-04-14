from ao.social.oauth_ import OAuthClient


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

        response = self._make_protected_request(access_token, access_secret, True)

        raise ValueError, response.content

    def post(self, text, token='', secret=''):
        """Do a LinkedIn profile update."""

        raise ValueError, 'POST NOT IMPLEMENTED YET'
