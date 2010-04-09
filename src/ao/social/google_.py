import cgi

from openid import extension, message
from openid.consumer import consumer
from openid.extensions import ax
from openid.store import memstore


AX_NS = 'http://openid.net/srv/ax/1.0'


class GoogleClient(object):
    """Holds the settings for Google-specific OpenID."""

    # Required information for Attribute Exchange
    required = {
        'firstname': 'http://axschema.org/namePerson/first',
        'lastname': 'http://axschema.org/namePerson/last',
        'email': 'http://axschema.org/contact/email',
    }

    _default_config = {
        'endpoint': 'https://www.google.com/accounts/o8/id',
    }

    def __init__(self, config={}):
        """Configure the client."""

        for key, value in self._default_config.iteritems():
            if key not in config:
                config[key] = value

        self._config = config

    def redirect(self):
        """Return a custom auth request url."""

        gconsumer = consumer.Consumer({}, memstore.MemoryStore())

        # Create an auth request to the given endpoint
        authrequest = gconsumer.begin(self._config['endpoint'])

        # Create an Attribute Exchange extension request
        axrequest = ax.FetchRequest(self._config['callback'])
        for alias, url in self.required.iteritems():
            axrequest.add(ax.AttrInfo(url, alias=alias, required=True))
        authrequest.addExtension(axrequest)

        # Create and apply a custom User Interface extension request
        uirequest = UIFetchRequest(mode='popup', icon=True)
        authrequest.addExtension(uirequest)

        # Return the generated URL
        return authrequest.redirectURL(self._config['realm'],
            self._config['callback'])

    def get_user(self, query, callback):
        """Verify the request and returns the user's credentials on success."""

        # We use the GenericConsumer class, so we need to add the nonce:
        if 'janrain_nonce' not in query:
            return None

        gconsumer = consumer.Consumer({}, memstore.MemoryStore())
        return_to = '%s?janrain_nonce=%s' % (callback, query['janrain_nonce'])
        response = gconsumer.complete(query, return_to)

        if response.status == consumer.SUCCESS:
            url = response.message.getArg(message.OPENID2_NS, 'claimed_id')
            email, first_name, last_name = (response.message.getArg(AX_NS,
                'value.%s' % val) for val in sorted(self.required.keys()))

            return {
                'id': cgi.parse_qs(url.split('?', 1)[-1])['id'][0],
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            }


class UIFetchRequest(extension.Extension):
    """User Interface extension for OpenID."""

    ns_alias = 'ui'
    ns_uri = 'http://specs.openid.net/extensions/ui/1.0'

    def __init__(self, mode=None, icon=False, x_has_session=False):
        """Some custom UI initialization."""

        super(UIFetchRequest, self).__init__()

        self._args = {}

        mode is not None and self._args.update({'mode': mode})
        icon and self._args.update({'icon': str(icon).lower()})
        x_has_session and self._args.update(
            {'x-has-session': str(x_has_session).lower()})

    def getExtensionArgs(self):
        """Return extension arguments."""

        return self._args
