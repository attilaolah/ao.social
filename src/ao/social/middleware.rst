Configurung the middleware
==========================

The social middleware is a generic, stand-alone component that can be used for
common social networking interactions, regardless of the web framework being
used. However, it needs some configurations. To make things easier, you can
store this configuration in an external settings file. In this example we'll
use a YAML file::

    >>> import StringIO
    >>> confstr = StringIO.StringIO("""
    ... login_path: /login/%s/
    ... user_class: foomodule.models.User
    ... facebook:
    ...   key: your-facebook-api-key
    ...   secret: your-facebook-api-secret
    ... twitter:
    ...   key: your-twitter-consumer-key
    ...   secret: your-twitter-consumer-secret
    ... google:
    ...   realm: http://www.example.com/
    ...   secret: your-google-api-secret
    ...   callback: http://www.example.com/login/google/
    ... """)

    >>> import yaml
    >>> conf = yaml.load(confstr)

Note that for the google login to work, the callback must be the login path for
google::

    >>> conf['login_path'] % 'google'
    '/login/google/'

    >>> conf['google']['callback']
    'http://www.example.com/login/google/'


Setting up the testing environment
==================================

The middleware works with user objects, but it doesn't provide a readily usable
``User`` class. You have to import ``ao.social.UserBase`` and subclass it, and
then pass it through the middleware configuration as ``user_class``. This way
you can chose the database backend of your application, as well as other
attributes and methods for better integration with your application. For this
example, we're going to mock a simple, non-persistent ``User`` class::

    >>> from ao import social
    >>> class User(social.UserBase):
    ...     """Dummy user class."""
    ...

    >>> import minimock
    >>> def fake_import(modstr, *args, **kw):
    ...     if modstr == 'foomodule.models':
    ...         return minimock.Mock('foomodule')
    ...     return __builtin__.__original_import__(modstr, *args, **kw)
    ...

    >>> import __builtin__
    >>> __builtin__.__original_import__ = __builtin__.__import__
    >>> __builtin__.__import__ = fake_import

    >>> import foomodule.models
    >>> foomodule.models.User = User

Set up a dummy function as the downstream WSGI application::

    >>> from ao.social import middleware
    >>> def wsgi_app(environ, start_response):
    ...     user = environ['ao.social.user']
    ...     headers = [('content-type', 'text/html')]
    ...     start_response('200 OK', headers)
    ...     return ('Hello, %s' % repr(user),)
    ...

Now we can configure the middleware::

    >>> app = middleware.AuthMiddleware(wsgi_app, conf)

We also need to add the ``beaker`` middleware for using Beaker sessions::

    >>> import beaker.middleware
    >>> app = beaker.middleware.SessionMiddleware(app, {
    ...     'session.type': 'cookie',
    ...     'session.key': 'session',
    ...     'session.enctypt_key': 'fookey',
    ...     'session.validate_key': 'barkey',
    ... })

The middleware will listen to requests on the path that it is configured with
(``login_path``). On other paths, it will simply check if the user already has
a session, in which case it would initialize the corresponding user and assign
it to the ``ao.social.user`` WSGI environment variable. If no session is
present, the ``ao.social.user`` variable will be ``None``::

    >>> import webtest
    >>> testapp = webtest.TestApp(app)

    >>> testapp.get('/')
    <200 OK text/html body='Hello, None'>

If we go to the login pages, the individual login mechanisms are started. For
example, if we go to the facebook login page::

    >>> #testapp.get('/login/google/')
    >>> # -> <307 Temporary Redirect text/html location: https://www.google.com/...>

The user gets redirected to Google, and on return the openid library is used to
verify the credentials.

The Facebook authentication works in a different way. The user must authorize
the application, and have the corresponding (signed) cookies when he arrives on
the login page. Otherwise, the user won't get authenticated::

    >>> testapp.get('/login/facebook/')
    Traceback (most recent call last):
    ...
    Unauthorized: Facebook Connect authentication failed.

Twitter works similarly to Google, but since we didn't set up valid credentials
for testing, we won't be able to get an authorization token from the Twitter
server::

    >>> #testapp.get('/login/twitter/')
    >>> # -> Traceback (most recent call last):
    >>> # -> ...
    >>> # -> AttributeError: 'NoneType' object has no attribute 'content'

Currently the Twitter client expects to have App Engine's memcache available,
so we mock that for the thesting environment too::

    >>> import sys

    >>> mocks = (
    ...     'google',
    ...     'google.appengine',
    ...     'google.appengine.api',
    ...     'google.appengine.ext',
    ... )

    >>> sys.modules.update(dict((mock, minimock.Mock(mock)) for mock in mocks))

    >>> reload(social.twitter)
    <module 'ao.social.twitter_' from '...'>

Clean up after the tests::

    >>> __builtin__.__import__ = __builtin__.__original_import__
    >>> del __builtin__.__original_import__

    >>> from zope.testing import cleanup
    >>> cleanup.cleanUp()
