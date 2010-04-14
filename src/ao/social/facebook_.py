import facebook

from hashlib import md5


class FacebookClient(object):
    """Facebook Connect handler."""

    def __init__(self, config={}):
        """Configure the client."""

        self._key = config['key']
        self._secret = config['secret']

        self._api = facebook.Facebook(self._key, self._secret)

    def key(self):
        """Return the API key."""

        return self._key

    def get_user(self, request):
        """Check if the user has authorized the application."""

        if self._key in request.cookies:
            hash = md5('expires=%ssession_key=%sss=%suser=%s%s' % tuple(
                [request.cookies.get('%s_%s' % (self._key, item)) \
                for item in ('expires', 'session_key', 'ss', 'user')] +
                [self._secret],
            )).hexdigest()
            if hash == request.cookies[self._key]:
                # OK, Facebook user is verified: return the user id.
                return {
                    'id': str(request.cookies['%s_user' % self._key]),
                    'token': str(request.cookies['%s_session_key' % \
                        self._key]),
                    'secret': str(request.cookies['%s_ss' % self._key]),
                }

    def post(self, text, uid, **kw):
        """Post the message to the user's facebook profile"""

        self._api.stream.publish(uid=uid, message=text, **kw)

    def __getattr__(self, attr):
        """Delegate the rest of the calls to the API."""

        return getattr(self._api, attr)
