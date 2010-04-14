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
                'availbale: `json`, `simplejson`, `django.utils.simplejson`.')

try:
    from google.appengine.api import memcache, urlfetch

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

        def content(self):
            """Simulate the content property."""

            self._fetch()
            return self._response['data']

        content = property(content)

    class MemCache(object):
        """Mock the memcache object."""

        def get(self, key):
            """Get the key from the cache."""

            raise NotImplementedError('Memcache only works on App Engine.')

        def set(self, key, value):
            """Get the key from the cache."""

            raise NotImplementedError('Memcache only works on App Engine.')

    urlfetch, memcache = URLFetch(), MemCache()
