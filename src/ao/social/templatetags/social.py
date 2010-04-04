from django import template

import md5

import urllib


register = template.Library()


def loginbutton(parser, token):
    """Renders a login button."""

    method = token.split_contents()[1]

    return LoginButton(method)


register.tag(loginbutton)


class LoginButton(template.Node):
    """The Login Button node."""

    def __init__(self, method):
        """Save the login method to self.method."""

        self.method = method

    def render(self, context):
        """Render a button for the given context."""

        environ = context['request'].environ

        auth_url = environ['ao.social.login'] % self.method
        auth_url += '?redirect=' + urllib.quote(environ['PATH_INFO'])

        if self.method == 'google':
            button = '<a href="%s" class="login login-google popup">&nbsp;</a>'
        elif self.method == 'twitter':
            button = '<a href="%s" class="login login-twitter popup">&nbsp;'\
                '</a>'
        elif self.method == 'facebook':
            button = '<fb:login-button onlogin="location.href=\'%s\'">'\
                '</fb:login-button>'

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

        return 'http://www.gravatar.com/avatar.php?%s' % urlencode({
            'gravatar_id': md5((email or '').lower()).hexdigest(),
            'size': str(size),
        })

    gravatar = staticmethod(gravatar)

    def render(self, context):
        """Render the avatar for the given context."""

        user = context['request'].environ['ao.social.user']

        url = user.avatar or gravatar(user.email,
            max(map(int, (self.width, self.height))))

        img = '<img src="%s" alt="%s" style="width: %spx; height: %spx;"/>'
        img = img % (url, user.name, self.width, self.height)

        return img
