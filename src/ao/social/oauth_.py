import cgi

from ao.social.utils import memcache, urlfetch

from oauth import oauth

import urllib


class OAuthClient(object):
    """Generic OAuth client."""

    _default_config = {
        'request_token_url': '',
        'access_token_url': '',
        'authorize_url': '',
        'account_verification_url': '',
        'update_url': '',
    }

    def __init__(self, config={}):
        """Configure the client."""

        for key, value in self._default_config.iteritems():
            if key not in config:
                config[key] = value

        self._config = config

        self._signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self._consumer = oauth.OAuthConsumer(config['key'], config['secret'])

    def key(self):
        """Return the API key."""

        return self._config['key']

    def _extract_credentials(self, result):
        """Extract Credentials.

        Returns an dictionary containing the token and secret (if present),
        or raises OAuthError.

        """

        token = None
        secret = None
        parsed_results = cgi.parse_qs(result.content)

        if 'oauth_token' in parsed_results:
            token = parsed_results['oauth_token'][0]

        if 'oauth_token_secret' in parsed_results:
            secret = parsed_results['oauth_token_secret'][0]

        if not (token and secret) or result.status_code != 200:
            raise oauth.OAuthError, 'Problem talking to the service'

        return {
            'token': token,
            'secret': secret,
        }

    def _get_memcache_auth_key(self, auth_token):
        """Get the memcache auth_key from an auth_token."""

        return 'oauth_%s' % auth_token

    def _get_auth_token(self, callback_url):
        """Get Authorization Token.

        Actually gets the authorization token and secret from the service. The
        token and secret are stored in memcache, and the auth token is
        returned.

        """

        # Create an OAuth request and extract the credentials.
        result = self._extract_credentials(
            self._make_callback_request(callback_url))

        auth_token = result['token']
        auth_secret = result['secret']

        # Add the secret to memcache.
        memcache.set(self._get_memcache_auth_key(auth_token), auth_secret,
            time=1200)

        return auth_token

    def _make_callback_request(self, callback_url):
        """Makes a generic OAuth request."""

        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer,
            callback=callback_url,
            http_url=self._config['request_token_url'],
        )
        request.sign_request(
            self._signature_method,
            self._consumer,
            None,
        )

        return urlfetch.fetch(request.to_url())

    def _make_verification_request(self, token, secret, verifier, params):
        """Makes a verification OAuth request."""

        token = oauth.OAuthToken(token, secret)
        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer,
            token=token,
            verifier=verifier,
            http_url=self._config['access_token_url'],
        )
        request.sign_request(
            self._signature_method,
            self._consumer,
            token,
        )

        return urlfetch.fetch(request.to_url())

    def _make_protected_request(self, token, secret, headers=False):
        """Makes a protected OAuth request object."""

        url = self._config['account_verification_url']
        token = oauth.OAuthToken(token, secret)
        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer,
            token=token,
            http_url=url,
        )
        request.sign_request(
            self._signature_method,
            self._consumer,
            token,
        )

        if headers:
            # LinkedIn requires the parameters to be sent as headers
            return urlfetch.fetch(url, headers=request.to_header())

        # Twitter works fine with URL query string parameters
        return urlfetch.fetch(request.to_url(),
            headers={'Authorization': 'OAuth'})

    def get_authorization_url(self, callback_url):
        """Get Authorization URL."""

        return '%s?oauth_token=%s' % (self._config['authorize_url'],
            self._get_auth_token(callback_url))

    def get_user_info(self, auth_token, auth_verifier):
        """Get User Info.

        Exchanges the auth token for an access token and returns a dictionary
        of information about the authenticated user.

        """

        auth_token = urllib.unquote(auth_token)
        auth_verifier = urllib.unquote(auth_verifier)

        auth_secret = memcache.get(self._get_memcache_auth_key(auth_token))
        auth_secret = auth_secret or ''  # memcache might return None

        response = self._make_verification_request(auth_token, auth_secret,
            auth_verifier, {'oauth_verifier': auth_verifier})

        # Extract the access token/secret from the response.
        result = self._extract_credentials(response)

        # Try to collect some information about this user from the service.
        user_info = self.lookup_user_info(result['token'], result['secret'])
        user_info.update(result)

        return user_info

    def lookup_user_info(self, access_token, access_secret):
        """Lookup User Info.

        Same as `get_user_info` except that it uses a stored access_token and
        access_secret.

        """

        raise NotImplementedError('Subclasses must implement this method.')

    def post(self, text, token='', secret=''):
        """Do a profile profile update."""

        raise NotImplementedError('Subclasses must implement this method.')
