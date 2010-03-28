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
    ... popup_html: This HTML should close itself and redirect it's opener.
    ... facebook:
    ...   key: your-facebook-api-key
    ...   secret: your-facebook-api-secret
    ... twitter:
    ...   key: your-twitter-consumer-key
    ...   secret: your-twitter-consumer-secret
    ...   request_token_url: http://twitter.com/oauth/request_token
    ...   access_token_url: http://twitter.com/oauth/access_token
    ...   authorize_url: http://twitter.com/oauth/authorize
    ...   account_verification_url: http://twitter.com/account/verify_credentials.json
    ... google:
    ...   realm: http://www.example.com/
    ...   secret: yout-google-api-secret
    ...   endpoint: https://www.google.com/accounts/o8/id
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

Currently the Twitter-specific parts expect to be run on App Engine, so we mock
that for the thesting environment too::

    >>> import minimock
    >>> import sys

    >>> mocks = (
    ...     'google',
    ...     'google.appengine',
    ...     'google.appengine.api',
    ...     'google.appengine.ext',
    ... )

    >>> sys.modules.update(dict((mock, minimock.Mock(mock)) for mock in mocks))

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

    >>> def fake_import(modstr, *args, **kw):
    ...     if modstr == 'foomodule.models':
    ...         return minimock.Mock('foomodule')
    ...     return __builtin__.__original_import__(modstr, *args, **kw)
    ...

    >>> import __builtin__
    >>> __builtin__.__original_import__ = __builtin__.__import__
    >>> __builtin__.__import__ = fake_import

    >>> #import foomodule.models
    >>> #foomodule.models.User = User

Set up a dummy function as the downstream WSGI application::

    >>> from ao.social import middleware
    >>> def wsgi_app(environ, start_response):
    ...     print 'I am the downstream application! The current user is:',
    ...     print environ['ao.social.user']

Now we can configure the middleware::

    >>> app = middleware.AuthMiddleware(wsgi_app, conf)

Clean up after the tests::

    >>> from zope.testing import cleanup
    >>> cleanup.cleanUp()
