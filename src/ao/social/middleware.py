import webob
import webob.exc

from ao import social

from oauth import oauth


class AuthMiddleware(object):
    """Authentication and authorization middleware."""

    def __init__(self, app, config={}):
        """Configure the middleware."""

        self._app = app

        self._user_class = self._import_user(config['user_class'])

        self._login_path = config['login_path']
        self._popup_html = config['popup_html']

        self._facebook_client = social.registerClient('facebook',
            config['facebook'])
        self._google_client = social.registerClient('google',
            config['google'])
        self._twitter_client = social.registerClient('twitter',
            config['twitter'])

    def __call__(self, environ, start_response):
        """Put the user object into the WSGI environment."""

        # Save the login path, we might require it in template tags
        environ['ao.social.login'] = self._build_absolute_uri(environ,
            self._login_path)

        # Create our own request object
        request = webob.Request(environ)

        # We need beaker sessions for this middleware
        session = environ['beaker.session']

        # Check if the user already has a session
        environ['ao.social.user'] = None
        if 'ao.social.user' in session:
            environ['ao.social.user'] = self._user_class.get_user(
                session['ao.social.user'])

        # Try to log in the user
        for method in ('facebook', 'twitter', 'google'):
            if request.path_info == self._login_path % method:
                response = self._handle_user(request, method, 'login')
                if response is not None:
                    return response(environ, start_response)

        # Call the downstream application
        return self._app(environ, start_response)

    def _build_absolute_uri(environ, path='/'):
        """Constructs an absolute URI."""

        root = '%s://%s' % (environ['wsgi.url_scheme'], environ['HTTP_HOST'])
        path = not path.startswith('/') and environ['PATH_INFO'] + path or path

        return root + path

    _build_absolute_uri = staticmethod(_build_absolute_uri)

    def _import_user(cls):
        """Import the provided `User` class."""

        modstr, _, cls = cls.rpartition('.')

        mod = __import__(modstr)
        for sub in modstr.split('.')[1:]:
            mod = getattr(mod, sub)

        return getattr(mod, cls)

    _import_user = staticmethod(_import_user)

    def _login_user(self, request, method, credentials):
        """Looks up the user and initiates a session."""

        uid = ':'.join((method, str(credentials['id'])))

        # Get the user from the database backend (or create a new user)
        user = self._user_class.lookup_user(uid)

        # Save the user's details and any associated tokens
        if method == 'facebook':
            uid = credentials['id']
            info = ['name', 'first_name', 'last_name', 'email', 'pic_square']
            data = self._facebook_client.users.getInfo(uid, info)[0]
            user.update_details({
                'name': data['name'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'avatar': data['pic_square'],
                'email': data['email'],
            })
        if method == 'twitter':
            user.set_token('twitter', {
                'token': credentials['token'],
                'secret': credentials['secret'],
            })
            first_name, _, last_name = credentials['name'].partition(' ')
            user.update_details({
                'name': credentials['name'],
                'first_name': first_name,
                'last_name': last_name,
                'avatar': credentials['profile_image_url'],
            })

        # Prepare the response
        if method == 'facebook':
            # Facebook will redirect the main window, so we send the user back.
            location = self._build_absolute_uri(request.environ, '/')
            response = webob.exc.HTTPTemporaryRedirect(location=location)
        if method in ('google', 'twitter'):
            # Handle Google/Twitter popup windows.
            body = self._popup_html % request.GET.get('redirect', '/')
            response = webob.Response(body=body)

        # Store the user's key in the session
        session = request.environ['beaker.session']
        session['ao.social.user'] = str(user.get_key())
        session.save()

        # Save changes to the user object
        user.save_user()

        return response

    def _connect_user(self, request, method, login):
        """Connects the account to the current user."""

        raise NotImplementedError('Connect is not implemented yet.')

    def _handle_user(self, request, method, mode='login'):
        """Handles authentication for the user.

        If `mode` is set to 'connect', it will assume that a user is already
        logged in and connects the new account to the logged in user.
        Otherwise, simply logs in the user.

        """

        # Check if the user has logged in via Facebook Connect.
        if method == 'facebook':
            uid = self._facebook_client.get_user_id(request)
            if uid is None:
                raise social.Unauthorized('Facebook Connect authentication '\
                    'failed.')
            # OK, Twitter user is verified.
            if mode == 'login':
                return self._login_user(request, method, {'id': uid})
            return self._connect_user(request, method, {'id': uid})

        # Check if the user has logged in via Twitter's Oauth.
        if method == 'twitter':
            keys = ('oauth_token', 'oauth_verifier')
            if  not all(key in request.GET for key in keys):
                # Redirect the user to Twitter's authorization URL.
                auth_url = self._login_path % method
                auth_url = self._twitter_client.get_authorization_url(
                    self._build_absolute_uri(request.environ, auth_url))
                return webob.Response(status=302, headers={
                    'Location': auth_url,
                })
            try:
                user = self._twitter_client.get_user_info(
                    request.GET['oauth_token'],
                    request.GET['oauth_verifier'],
                )
                # OK, Twitter user is verified.
                if mode == 'login':
                    return self._login_user(request, method, user)
                return self._connect_user(request, method, user)
            except oauth.OAuthError:
                raise social.Unauthorized('Twitter OAuth authentication '\
                    'failed.')

        # Check if the user has logged in via Google OpenID/OAuth.
        if method == 'google':
            if len(request.GET) < 2:
                # Create a custom auth request and redirect the user.
                return webob.exc.HTTPTemporaryRedirect(
                    location=self._google_client.redirect(),
                )
            # Hopefully the user has come back from the auth request url.
            user = self._google_client.get_user(request.GET,
                self._build_absolute_uri(request.environ))
            if user is None:
                raise social.Unauthorized('Google OpenID authentication '\
                    'failed.')
            # OK, Google user is verified.
            if mode == 'login':
                return self._login_user(request, method, user)
            return self._connect_user(request, method, user)
