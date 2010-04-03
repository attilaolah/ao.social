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
