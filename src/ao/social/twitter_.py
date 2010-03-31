import cgi

from google.appengine.api import memcache, urlfetch

from oauth import oauth

import urllib

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json


class TwitterClient(object):
    """Twitter-specific OAuth client."""

    __signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()

    def __init__(self, config={}):
        """Configure the client."""

        self.__account_verification_url = config['account_verification_url']
        self.__access_token_url = config['access_token_url']
        self.__request_token_url = config['request_token_url']
        self.__authorize_url = config['authorize_url']
        self.__consumer = oauth.OAuthConsumer(config['key'], config['secret'])

    def __extract_credentials(self, result):
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

    def __get_memcache_auth_key(self, auth_token):
        """Get the memcache auth_key from an auth_token."""

        return 'oauth_%s' % auth_token

    def __get_auth_token(self, callback_url):
        """Get Authorization Token.

        Actually gets the authorization token and secret from the service. The
        token and secret are stored in memcache, and the auth token is
        returned.

        """

        # Create an OAuth request and extract the credentials.
        result = self.__extract_credentials(
            self.__make_callback_request(callback_url))

        auth_token = result['token']
        auth_secret = result['secret']

        # Add the secret to memcache.
        memcache.set(self.__get_memcache_auth_key(auth_token), auth_secret,
            time=1200)

        return auth_token

    def __make_callback_request(self, callback_url):
        """Creates a Twitter specific OAuth request object."""

        request = oauth.OAuthRequest.from_consumer_and_token(
            self.__consumer,
            callback=callback_url,
            http_url=self.__request_token_url,
        )
        request.sign_request(
            self.__signature_method,
            self.__consumer,
            None,
        )

        return urlfetch.fetch(request.to_url())

    def __make_verification_request(self, token, secret, verifier, params):
        """Creates a Twitter specific OAuth request object."""

        token = oauth.OAuthToken(token, secret)
        request = oauth.OAuthRequest.from_consumer_and_token(
            self.__consumer,
            token=token,
            verifier=verifier,
            http_url=self.__access_token_url,
        )
        request.sign_request(
            self.__signature_method,
            self.__consumer,
            token,
        )

        return urlfetch.fetch(request.to_url())

    def __make_protected_request(self, token, secret):
        """Creates a Twitter specific OAuth request object."""

        token = oauth.OAuthToken(token, secret)
        request = oauth.OAuthRequest.from_consumer_and_token(
            self.__consumer,
            token=token,
            http_url=self.__account_verification_url,
        )
        request.sign_request(
            self.__signature_method,
            self.__consumer,
            token,
        )

        return urlfetch.fetch(request.to_url(),
            headers={'Authorization': 'OAuth'})

    def get_authorization_url(self, callback_url):
        """Get Authorization URL."""

        return '%s?oauth_token=%s' % (self.__authorize_url,
            self.__get_auth_token(callback_url))

    def get_user_info(self, auth_token, auth_verifier):
        """Get User Info.

        Exchanges the auth token for an access token and returns a dictionary
        of information about the authenticated user.

        """

        auth_token = urllib.unquote(auth_token)
        auth_verifier = urllib.unquote(auth_verifier)

        auth_secret = memcache.get(self.__get_memcache_auth_key(auth_token))

        response = self.__make_verification_request(auth_token, auth_secret,
            auth_verifier, {'oauth_verifier': auth_verifier})

        # Extract the access token/secret from the response.
        result = self.__extract_credentials(response)

        # Try to collect some information about this user from the service.
        user_info = self.lookup_user_info(result['token'], result['secret'])
        user_info.update(result)

        return user_info

    def lookup_user_info(self, access_token, access_secret):
        """Lookup User Info.

        Same as `get_user_info` except that it uses a stored access_token and
        access_secret.

        """

        response = self.__make_protected_request(access_token, access_secret)

        return json.loads(response.content)
