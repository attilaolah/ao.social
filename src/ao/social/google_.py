from openid.consumer.consumer import Consumer, SUCCESS
from openid.extension import Extension
from openid.extensions.ax import AttrInfo, FetchRequest as AXFetchRequest
from openid.message import OPENID2_NS
from openid.store.memstore import MemoryStore


AX_NS = 'http://openid.net/srv/ax/1.0'

# Required information for Attribute Exchange
required = {
    'firstname': 'http://axschema.org/namePerson/first',
    'lastname': 'http://axschema.org/namePerson/last',
    'email': 'http://axschema.org/contact/email',
}


class GoogleClient(object):
    """Holds the settings for Google-specific OpenID."""

    def __init__(self, config={}):
        """Configure the client."""

        self.__endpoint = config['endpoint']
        self.__realm = config['realm']
        self.__callback = config['callback']

    def redirect(self):
        """Returns a custom auth request url."""

        consumer = Consumer({}, MemoryStore())

        # Create an auth request to the given endpoint
        authrequest = consumer.begin(self.__endpoint)

        # Create an Attribute Exchange extension request with the required fields
        axrequest = AXFetchRequest(self.__callback)
        for alias, url in required.iteritems():
            axrequest.add(AttrInfo(url, alias=alias, required=True))
        authrequest.addExtension(axrequest)

        # Create and apply a custom User Interface extension request
        uirequest = UIFetchRequest(mode='popup', icon=True)
        authrequest.addExtension(uirequest)

        # Return the generated URL
        return authrequest.redirectURL(self.__realm, self.__callback)

    def get_user(query, callback):
        """Verifies the request and returns the user's credentials on success."""

        # We use the GenericConsumer class, so we need to add the nonce:
        if 'janrain_nonce' not in query:
            return None

        consumer = Consumer({}, MemoryStore())
        return_to = '%s?janrain_nonce=%s' % (callback, query['janrain_nonce'])
        response = consumer.complete(query, return_to)

        if response.status == SUCCESS:
            url = response.message.getArg(OPENID2_NS, 'claimed_id')
            firstname, lastname, email = (response.message.getArg(AX_NS,
                'value.%s' % val) for val in ('firstname', 'lastname', 'email'))

            return {
                'login': cgi.parse_qs(url.split('?', 1)[-1])['id'][0],
                'email': email,
                'name': '%s %s' % (firstname, lastname),
                'profileurl': url,
            }

    get_user = staticmethod(get_user)


class UIFetchRequest(Extension):
    """User Interface extension for OpenID."""

    ns_alias = 'ui'
    ns_uri = 'http://specs.openid.net/extensions/ui/1.0'

    def __init__(self, mode=None, icon=False, x_has_session=False):
        super(UIFetchRequest, self).__init__()
        self.__args = {}
        if mode is not None:
            self.__args.update({'mode': mode})
        if icon:
            self.__args.update({'icon': str(icon).lower()})
        if x_has_session:
            self.__args.update({'x-has-session': str(x_has_session).lower()})

    def getExtensionArgs(self):
        """Return extension arguments."""

        return self.__args
