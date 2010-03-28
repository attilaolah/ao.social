from hashlib import md5


class FacebookClient(object):
    """Facebook Connect handler."""

    def __init__(self, config={}):
        """Configure the client."""

        self.__key = config['key']
        self.__secret = config['secret']


    def get_user_id(self, environ):
        """Check if the user has authorized the application."""

        if self.__key in environ['COOKIES']:
            hash = md5('expires=%ssession_key=%sss=%suser=%s%s' % tuple(
                [environ['COOKIES'].get('%s_%s' % (self.__key, item)) \
                for item in ('expires', 'session_key', 'ss', 'user')] +
                [self.__secret],
            )).hexdigest()
            if hash == environ['COOKIES'][self.__key]:
                # OK, Facebook user is verified: return the user id.
                return str(request.COOKIES['%s_user' % self.__key])
