try:
    import json

except ImportError:
    try:
        import simplejson as json

    except ImportError:
        try:
            from django.utils import simplejson as json

        except ImportError:
            raise ImportError('One of the following modules must be '\
                'available: `json`, `simplejson`, `django.utils.simplejson`.')

try:
    from google.appengine.api import memcache

except ImportError:
    try:
        import memcache as memcache_module
        mc = memcache_module.Client(['127.0.0.1:11211'], debug=0)

        class MemCache(object):
            """Mock the memcache object."""

            def get(self, key):
                """Get the key from the cache."""
                #FIXME: mmh, probably not so good
                return mc.get(key.encode('utf-8'))

            def set(self, key, value, time):
                """Get the key from the cache."""
                mc.set(key, value, time)

        memcache = MemCache()

    except ImportError:
        raise ImportError('You must install memcache')

try:
    from google.appengine.api import urlfetch

except ImportError:
    import urllib2

    class URLFetch(object):
        """Fall-back URL fetch."""

        GET, POST = 'GET', 'POST'

        def fetch(self, url, payload=None, method=None, headers={}):
            """Somulate App Engine's `fetch` method for this module."""

            method = method or self.GET
            if method == self.GET:
                payload = None
            if method == self.POST:
                payload = payload or ''

            request = urllib2.Request(url, data=payload, headers=headers)

            return Response(request)

    class Response(object):
        """Simulate App Engine's URL fetch response."""

        def __init__(self, request):
            """Store the request object."""

            self._request = request
            self._response = None

        def _fetch(self):
            """Lazily fetch the response."""

            if self._response is None:
                response = urllib2.urlopen(self._request)
                self._response = {
                    'obj': response,
                    'data': response.read(),
                }

        @property
        def status_code(self):
            return self._response['obj'].getcode()

        def content(self):
            """Simulate the content property."""

            self._fetch()
            return self._response['data']

        content = property(content)

    urlfetch = URLFetch()

