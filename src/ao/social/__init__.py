from ao.social import facebook_ as facebook
from ao.social import twitter_ as twitter
from ao.social import google_ as google
from ao.social import linkedin_ as linkedin
from ao.social.utils import json


clients = {}


class Unauthorized(Exception):
    """User is not authorized."""


class ImproperlyConfigured(Exception):
    """Indicates that the short url handler is not configured properly."""


def registerClient(method, config={}):
    """Register a Twitter client."""

    client_classes = {
        'twitter': twitter.TwitterClient,
        'google': google.GoogleClient,
        'facebook': facebook.FacebookClient,
        'linkedin': linkedin.LinkedInClient,
    }

    global clients
    clients[method] = client_classes[method](config)

    return clients[method]


def getClient(method):
    """Return the client for the given method."""

    global clients

    try:
        return clients[method]
    except KeyError:
        raise ImproperlyConfigured('The requested client (%s) is not '\
            'initialized (available clients: %s).' % (method, clients.keys()))


def user(request):
    """Adds the session user to the `RequestContext`.

    This is a Django `template context processor`. You shouldn't need to use
    this function directly.

    """

    return {
        'user': request.environ['ao.social.user'],
    }


class UserBase(object):
    """Base class for `User` implementations."""

    def post(self, method, text, *args, **kw):
        """Do a stream post or status update to the given service."""

        token = self.get_token(method)
        if method == 'facebook':
            kw['uid'] = token['uid']
        elif method in ('twitter', 'linkedin'):
            kw['token'] = token['token']
            kw['secret'] = token['secret']

        client = getClient(method)

        return client.post(text, *args, **kw)

    def get_user(cls, key):
        """Get a user for the corresponding method & external id."""

        raise NotImplementedError('You must overload the `get_user` method.')

    get_user = classmethod(get_user)

    def lookup_user(cls, uid):
        """Get a user for the corresponding method & external id."""

        raise NotImplementedError('You must overload the `lookup_user` '\
            'method.')

    lookup_user = classmethod(lookup_user)

    def save_user(self):
        """Get a user for the corresponding method & external id."""

        raise NotImplementedError('You must overload the `save_user` method.')

    def get_key(self):
        """Return a key that will be stored in session."""

        raise NotImplementedError('You must overload the `get_key` method.')

    def update_details(self, details):
        """Update the user's details."""

        raise NotImplementedError('You must overload the `update_details` '\
            'method.')

    def id(self):
        """Return the login id."""

        return self.uid.partition(':')[2]

    id = property(id)

    def method(self):
        """Return the login method ('google', 'twitter' or 'facebook')."""

        return self.uid.partition(':')[0]

    method = property(method)

    def get_token(self, method):
        """Return the token for the given method."""

        if not hasattr(self, 'tokens'):
            raise NotImplementedError('User object has no `tokens` attribute.')

        return json.loads(self.tokens or '{}')[method]

    def set_token(self, method, token=None):
        """Store the token for the user."""

        if not hasattr(self, 'tokens'):
            raise NotImplementedError('User object has no `tokens` attribute.')

        tokens = json.loads(self.tokens or '{}')
        if token is None:
            del tokens[method]
        else:
            tokens[method] = token

        self.tokens = json.dumps(tokens, separators=(',', ':'))

        self.save_user()

    def clear_token(self, method):
        """Remove the token."""

        return self.set_token(method)
