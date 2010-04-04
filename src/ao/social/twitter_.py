import cgi

from ao.social.json_ import json

from oauth import oauth

import urllib

try:
    from google.appengine.api import memcache, urlfetch

except ImportError:

    import urllib2

    class URLFetch(object):
        """Fall-back URL fetch."""

        GET, POST = 'GET', 'POST'

        def fetch(self, url, payload=None, method=None, headers={}):
            """Somulate App Engine's `fetch` method for this module."""

            method = method or self.GET
            if method == self.GET:
                payload = None
            if method == self.POST:
                payload = payload or ''

            request = urllib2.Request(url, data=payload, headers=headers)

            return Response(request)

    class Response(object):
        """Simulate App Engine's URL fetch response."""

        def __init__(self, request):
            """Store the request object."""

            self._request = request
            self._response = None

        def _fetch(self):
            """Lazily fetch the response."""

            if self._response is None:
                response = urllib2.urlopen(self._request)
                self._response = {
                    'obj': response,
                    'data': response.read(),
                }

        def content(self):
            """Simulate the content property."""

            self._fetch()
            return self._response['data']

        content = property(content)

    class MemCache(object):
        """Mock the memcache object."""

        def get(self, key):
            """Get the key from the cache."""

            raise NotImplementedError('Memcache only works on App Engine.')

        def set(self, key, value):
            """Get the key from the cache."""

            raise NotImplementedError('Memcache only works on App Engine.')

    urlfetch, memcache = URLFetch(), MemCache()


class TwitterClient(object):
    """Twitter-specific OAuth client."""

    _default_config = {
        'request_token_url': 'https://twitter.com/oauth/request_token',
        'access_token_url': 'https://twitter.com/oauth/access_token',
        'authorize_url': 'https://twitter.com/oauth/authorize',
        'account_verification_url':
            'https://twitter.com/account/verify_credentials.json',
        'update_url': 'https://api.twitter.com/1/statuses/update.%(format)s',
    }

    def __init__(self, config={}):
        """Configure the client."""

        for key, value in self._default_config.iteritems():
            if key not in config:
                config[key] = value

        self._config = config

        self._signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self._consumer = oauth.OAuthConsumer(config['key'], config['secret'])

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
        """Creates a Twitter specific OAuth request object."""

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
        """Creates a Twitter specific OAuth request object."""

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

    def _make_protected_request(self, token, secret):
        """Creates a Twitter specific OAuth request object."""

        token = oauth.OAuthToken(token, secret)
        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer,
            token=token,
            http_url=self._config['account_verification_url'],
        )
        request.sign_request(
            self._signature_method,
            self._consumer,
            token,
        )

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
