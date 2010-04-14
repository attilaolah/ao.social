import webob
import webob.exc

from ao import social

from oauth import oauth


class AuthMiddleware(object):
    """Authentication and authorization middleware."""

    _popup_html = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <title></title>
    <script>
      try {
        %(postlogin)s;
      } catch (e) {};
      close();
    </script>
  </head>
</html>"""

    def __init__(self, app, config={}):
        """Configure the middleware."""

        self._app = app

        self._user_class = self._import_user(config['user_class'])
        self._login_path = config['login_path']

        self._clients = {}
        for method in ('facebook', 'google', 'twitter', 'linkedin'):
            if method in config:
                self._clients[method] = social.registerClient(method,
                    config[method])

    def __call__(self, environ, start_response):
        """Put the user object into the WSGI environment."""

        # Create our own request object
        request = webob.Request(environ, charset='utf-8')

        # Save the login path, we might require it in template tags
        environ['ao.social.login'] = self._build_absolute_uri(environ,
            self._login_path)

        # We need beaker sessions for this middleware
        session = environ['beaker.session']

        # Check if the user already has a session
        environ['ao.social.user'] = None
        if 'ao.social.user' in session:
            environ['ao.social.user'] = self._user_class.get_user(
                session['ao.social.user'])

        # Try to log in the user
        for method in ('facebook', 'twitter', 'google', 'linkedin'):
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

        id = str(credentials['id'])
        uid = ':'.join((method, id))
        session = request.environ['beaker.session']

        # Get the user from the database backend (or create a new user)
        user = self._user_class.lookup_user(uid)

        # Save the user's details and any associated tokens
        if method == 'facebook':
            info = ['name', 'first_name', 'last_name', 'email', 'pic_square']
            data = self._clients[method].users.getInfo(id, info)[0]
            user.update_details({
                'name': data['name'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'avatar': data['pic_square'],
                'email': data['email'],
            })
            user.set_token('facebook', {
                'uid': id,
                'token': credentials['token'],
                'secret': credentials['secret'],
            })
        elif method == 'twitter':
            first_name, _, last_name = credentials['name'].partition(' ')
            user.update_details({
                'name': credentials['name'],
                'first_name': first_name,
                'last_name': last_name,
                'avatar': credentials['profile_image_url'],
            })
            user.set_token('twitter', {
                'uid': id,
                'token': credentials['token'],
                'secret': credentials['secret'],
            })
        elif method == 'google':
            user.update_details({
                'name': '%s %s' % (credentials['first_name'],
                    credentials['last_name']),
                'first_name': credentials['first_name'],
                'last_name': credentials['last_name'],
                'email': credentials['email'],
            })
            user.set_token('google', {
                'uid': id,
            })
        elif method == 'linkedin':
            user.update_details({
                'name': '%s %s' % (credentials['first_name'],
                    credentials['last_name']),
                'first_name': credentials['first_name'],
                'last_name': credentials['last_name'],
            })
            user.set_token('linkedin', {
                'uid': id,
                'token': credentials['token'],
                'secret': credentials['secret'],
            })

        # Prepare the response
        postlogin = ''
        if 'postlogin' in session:
            postlogin = session['postlogin']
            del session['postlogin']
        body = self._popup_html % {'postlogin': postlogin}
        response = webob.Response(body=body)

        # Store the user's key in the session
        session['ao.social.user'] = str(user.get_key())
        session.save()

        # Save changes to the user object
        user.save_user()

        return response

    def _connect_user(self, request, method, credentials):
        """Connects the account to the current user."""

        id = str(credentials['id'])
        user = request.environ['ao.social.user']
        session = request.environ['beaker.session']

        # Save the user's details and any associated tokens
        if method == 'facebook':
            user.set_token('facebook', {
                'uid': id,
                'token': credentials['token'],
                'secret': credentials['secret'],
            })
        elif method == 'twitter':
            user.set_token('twitter', {
                'uid': id,
                'token': credentials['token'],
                'secret': credentials['secret'],
            })
        elif method == 'google':
            user.set_token('google', {
                'uid': id,
            })
        elif method == 'linkedin':
            user.set_token('linkedin', {
                'uid': id,
                'token': credentials['token'],
                'secret': credentials['secret'],
            })

        # Prepare the response
        postlogin = ''
        if 'postlogin' in session:
            postlogin = session['postlogin']
            del session['postlogin']
        body = self._popup_html % {'postlogin': postlogin}
        response = webob.Response(body=body)

        # Save changes to the user object
        user.save_user()

        return response

    def _handle_user(self, request, method, mode='login'):
        """Handles authentication for the user.

        If `mode` is set to 'connect', it will assume that a user is already
        logged in and connects the new account to the logged in user.
        Otherwise, simply logs in the user.

        """

        user = request.environ['ao.social.user']
        session = request.environ['beaker.session']

        # Save the post login action in the session.
        if 'postlogin' in request.GET:
            session['postlogin'] = request.GET['postlogin']
            session.save()

        # Check if the user has logged in via Facebook Connect.
        if method == 'facebook':
            facebook_user = self._clients[method].get_user(request)
            if facebook_user is None:
                raise social.Unauthorized('Facebook Connect authentication '\
                    'failed.')
            # OK, Facebook user is verified.
            if user is None:
                return self._login_user(request, method, facebook_user)
            return self._connect_user(request, method, facebook_user)

        # Check if the user has logged in via Twitter's Oauth.
        if method == 'twitter':
            keys = ('oauth_token', 'oauth_verifier')
            if  not all(key in request.GET for key in keys):
                # Redirect the user to Twitter's authorization URL.
                auth_url = self._login_path % method
                auth_url = self._clients[method].get_authorization_url(
                    self._build_absolute_uri(request.environ, auth_url))
                return webob.Response(status=302, headers={
                    'Location': auth_url,
                })
            try:
                twitter_user = self._clients[method].get_user_info(
                    request.GET['oauth_token'],
                    request.GET['oauth_verifier'],
                )
                # OK, Twitter user is verified.
                if user is None:
                    return self._login_user(request, method, twitter_user)
                return self._connect_user(request, method, twitter_user)
            except oauth.OAuthError:
                raise social.Unauthorized('Twitter OAuth authentication '\
                    'failed.')

        # Check if the user has logged in via Google OpenID/OAuth.
        if method == 'google':
            if len(request.GET) < 2:
                # Create a custom auth request and redirect the user.
                return webob.exc.HTTPTemporaryRedirect(
                    location=self._clients[method].redirect(),
                )
            # Hopefully the user has come back from the auth request url.
            callback = self._build_absolute_uri(request.environ,
                self._login_path % method)
            google_user = self._clients[method].get_user(request.GET, callback)
            if google_user is None:
                raise social.Unauthorized('Google OpenID authentication '\
                    'failed.')
            # OK, Google user is verified.
            if user is None:
                return self._login_user(request, method, google_user)
            return self._connect_user(request, method, google_user)

        # Check if the user has logged in via LinkedIn's Oauth.
        if method == 'linkedin':
            keys = ('oauth_token', 'oauth_verifier')
            if  not all(key in request.GET for key in keys):
                # Redirect the user to LinkedIn's authorization URL.
                auth_url = self._login_path % method
                auth_url = self._clients[method].get_authorization_url(
                    self._build_absolute_uri(request.environ, auth_url))
                return webob.Response(status=302, headers={
                    'Location': auth_url,
                })
            try:
                linkedin_user = self._clients[method].get_user_info(
                    request.GET['oauth_token'],
                    request.GET['oauth_verifier'],
                )
                # OK, LinkedIn user is verified.
                if user is None:
                    return self._login_user(request, method, linkedin_user)
                return self._connect_user(request, method, linkedin_user)
            except oauth.OAuthError:
                raise social.Unauthorized('LinkedIn OAuth authentication '\
                    'failed.')
