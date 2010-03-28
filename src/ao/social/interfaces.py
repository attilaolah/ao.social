from zope.interface import Interface


class IShortUrlHandler(Interface):
    """Interface for ShortUrlHandler objects."""

    def cache_context(url, context):
        """Cache the context (i.e. using memcache)."""

    def get_context_from_cache(url):
        """Look up the cached context."""

    def get_context_from_db(url):
        """Look up the context in the database."""

    def generate_url(len, elems):
        """Generate (a random) new url."""

    def assign_url(context):
        """Create a new URL for the context and assign it to the context."""

    def construct_url(context, request):
        """Construct the short url for the given context."""
