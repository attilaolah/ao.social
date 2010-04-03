from ao.social import facebook_ as facebook, google_ as google, \
    twitter_ as twitter


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
    }

    global clients
    clients['twitter'] = client_classes[method](config)

    return clients['twitter']


def getClient(method):
    """Return the client for the given method."""

    global clients

    try:
        return clients[method]
    except KeyError:
        raise ImproperlyConfigured('The requested client is not initialized.')


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

    def get_user(cls, key):
        """Get a user for the corresponding method & external id."""

        raise NotImplementedError('You must overload the `get_user` method.')

    get_user = classmethod(get_user)

    def lookup_user(cls, uid):
        """Get a user for the corresponding method & external id."""

        raise NotImplementedError('You must overload the `lookup_user` method.')

    lookup_user = classmethod(lookup_user)

    def save_user(self):
        """Get a user for the corresponding method & external id."""

        raise NotImplementedError('You must overload the `save_user` method.')

    def get_key(self):
        """Returns a key that will be stored in session."""

        raise NotImplementedError('You must overload the `get_key` method.')

    def update_details(self, details):
        """Update the user's details."""

        raise NotImplementedError('You must overload the `update_details` method.')

    def method(self):
        """Returns the login method ('google', 'twitter' or 'facebook')."""

        return self.uid.partition(':')[0]

    method = property(method)
