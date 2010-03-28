import cgi
import os

from hashlib import md5

from oauth import oauth

from ao.social import facebook_ as facebook, google_ as google, \
    twitter_ as twitter


class Unauthorized(Exception):
    """User is not authorized."""


class AuthMiddleware(object):
    """Authentication and authorization middleware."""

    def __init__(self, app, config={}):
        """Configure the middleware."""

        self.__app = app

        self.__user_class = self.__import_user(config['user_class'])

        self.__login_path = config['login_path']
        self.__popup_html = config['popup_html']

        self.__facebook_client = facebook.FacebookClient(config['facebook'])
        self.__google_client = google.GoogleClient(config['google'])
        self.__twitter_client = twitter.TwitterClient(config['twitter'])

    def __call__(self, environ, start_response):
        """Put the user object into the WSGI environment."""

        session = environ['beaker.session']

        # Try to log in the user
        for method in ('facebook', 'twitter', 'google'):
            if environ['PATH_INFO'] == self.__login_path % method:
                response = self.__handle_user(environ, method, 'connect')
                if response is not None:
                    headers = [('content-type', 'text/html')]
                    if response[0].startswith('3'):
                        headers += [('Location', response[1])]
                        start_response(response[0], headers)
                        return ('',)
                    start_response(response[0], headers)
                    return (response[1],)

        # Check if the user already has a session
        environ['ao.social.user'] = 'user' in session and self.__get_user(
            session['key']) or None

        # Call the downstream application
        return self.__app(environ, start_response)

    def __build_absolute_uri(environ, path='/'):
        """Constructs an absolute URI."""

        root = '%s://%s' % (environ['wsgi.url_scheme'], environ['HTTP_HOST'])
        path = not path.startswith('/') and environ['PATH_INFO'] + path or path

        return root + path

    __build_absolute_uri = staticmethod(__build_absolute_uri)

    def __import_user(cls):
        """Import the provided `User` class."""

        modstr, _, cls = cls.rpartition('.')

        mod = __import__(modstr)
        for sub in modstr.split('.')[1:]:
            mod = getattr(mod, sub)

        return getattr(mod, cls)

    __import_user = staticmethod(__import_user)

    def __login_user(self, request, method, login):
        """Looks up the user and initiates a session."""

        # XXX TODO!!!
        request.user = queryUser(login, method)
        if method == 'facebook':
            # Facebook will redirect the main window, so we send the user back.
            response = HttpResponseRedirect(request.GET.get('redirect',
                reverse('home')))
        if method in ('google', 'twitter'):
            # Handle Google/Twitter popup windows.
            response = HttpResponse(self.__popup_html % request.GET.get(
                'redirect', reverse('home')))
        response.set_cookie('user', request.user.key().name(),
            max_age=self.SESSION_TIMEOUT)
        response.set_cookie('session', request.user.new_session(),
            max_age=self.SESSION_TIMEOUT)
        return response

    def __connect_user(self, request, method, login):
        """Connects the account to the current user."""

        raise NotImplementedError('Connect is not implemented yet.')

    def __handle_user(self, environ, method, mode='login'):
        """Handles authentication for the user.

        If `mode` is set to 'connect', it will assume that a user is already
        logged in and connects the new account to the logged in user.
        Otherwise, simply logs in the user.

        """

        # Check if the user has logged in via Facebook Connect.
        if method == 'facebook':
            uid = self.__facebook_client.get_user_id(environ)
            if uid is None:
                raise Unauthorized('Facebook Connect authentication failed.')
            # Ok, Facebook user is verified.
            raise NotImplementedError('OK: facebook user is logged in.')

        # Check if the user has logged in via Twitter's Oauth.
        if method == 'twitter':
            if  not all((key in cgi.parse_qs(environ['QUERY_STRING']) \
                for key in ('oauth_token', 'oauth_verifier'))):
                # Redirect the user to Twitter's authorization URL.
                auth_url = self.__login_path % method
                auth_url = self.__twitter_client.get_authorization_url(
                    self.__build_absolute_uri(environ, auth_url))
                return '302 Redirect', auth_url
            try:
                query = cgi.parse_qs(environ['QUERY_STRING'])
                user = self.__twitter_client.get_user_info(
                    query['oauth_token'],
                    query['oauth_verifier'],
                )
                # OK, Twitter user is verified.
                raise NotImplementedError('OK: twitter user is logged in.')
            except oauth.OAuthError:
                raise Unauthorized('Twitter OAuth authentication failed.')

        # Check if the user has logged in via Google OpenID/OAuth.
        if method == 'google':
            query = cgi.parse_qsl(environ['QUERY_STRING'])
            query = dict((k, unicode(v, 'utf-8')) for k, v in query)
            if len(query) < 2:
                # Create a custom auth request and redirect the user.
                return '302 Redirect', self.__google_client.redirect()
            # Hopefully the user has come back from the auth request url.
            user = self.__google_client.get_user(query,
                self.__build_absolute_uri(environ))
            if user is None:
                raise Unauthorized('Google OpenID authentication failed.')
            # OK, Google user is verified.
            raise NotImplementedError('OK: google user is logged in.')
