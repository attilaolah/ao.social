def user(request):
    """Adds the session user to the `RequestContext`."""

    return {
        'user': request.environ['ao.social.user'],
    }


class UserBase(object):
    """Base class for `User` implementations.."""

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
