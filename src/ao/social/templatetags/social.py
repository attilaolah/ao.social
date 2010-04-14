import urllib

from ao import social

from hashlib import md5

from django import template


register = template.Library()


def apikey(parser, token):
    """Renders the API key."""

    method = token.split_contents()[1]

    if method not in ('facebook', 'twitter', 'linkedin'):
        raise template.TemplateSyntaxError('Unsupported method for `apikey`: '\
            '%r' % method)

    return APIKey(method)


register.tag(apikey)


class APIKey(template.Node):
    """The API key node."""

    def __init__(self, method):
        """Save the login method to self.method."""

        self.method = method

    def render(self, context):
        """Render a button for the given context."""

        return social.getClient(self.method).key()


def loginbutton(parser, token):
    """Renders a login button."""

    token = token.split_contents()

    method = token[1]
    onlogin = len(token) > 2 and token[2] or None

    return LoginButton(method, onlogin)


register.tag(loginbutton)


class LoginButton(template.Node):
    """The Login Button node."""

    def __init__(self, method, onlogin=None):
        """Save the login method to self.method."""

        self.method = method
        self.onlogin = onlogin

    def render(self, context):
        """Render a button for the given context."""

        environ = context['request'].environ
        postlogin = 'opener.location.href=\'%s\'' % \
            urllib.quote(environ['PATH_INFO'])

        if self.method == 'facebook':
            if self.onlogin is not None:
                return '<fb:login-button onlogin="%s"></fb:login-button>' % \
                    self.onlogin
            button = '<fb:login-button onlogin="location.href=\'%s\'">'\
                '</fb:login-button>'
            postlogin = 'location.href=\\\'%s\\\'' % \
                urllib.quote(environ['PATH_INFO'])
        elif self.method == 'twitter':
            button = '<a href="%s" class="login login-twitter popup">&nbsp;'\
                '</a>'
        elif self.method == 'google':
            button = '<a href="%s" class="login login-google popup">&nbsp;</a>'

        auth_url = environ['ao.social.login'] % self.method
        auth_url += '?postlogin=' + postlogin

        return button % auth_url


def avatar(parser, token):
    """Renders the user's avatar."""

    width, height = token.split_contents()[1:3]

    return Avatar(width, height)

register.tag(avatar)


class Avatar(template.Node):
    """The Avatar node."""

    def __init__(self, width, height):
        """Save width and height to self.width and self.height."""

        self.width, self.height = width, height

    def gravatar(email, size=120):
        """Constructs a Gravatar image URL."""

        return 'http://www.gravatar.com/avatar.php?%s' % urllib.urlencode({
            'gravatar_id': md5((email or '').lower()).hexdigest(),
            'size': str(size),
        })

    gravatar = staticmethod(gravatar)

    def render(self, context):
        """Render the avatar for the given context."""

        user = context['request'].environ['ao.social.user']

        url = user.avatar or self.gravatar(user.email,
            max(map(int, (self.width, self.height))))

        img = '<img src="%s" alt="%s" style="width: %spx; height: %spx;"/>'
        img = img % (url, user.name, self.width, self.height)

        return img
