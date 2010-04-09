Using the middleware with Django
================================

An important thing to note is that this middleware is not a Django middleware,
but a pure WSGI middleware (meaning that it acts as an actual WSGI
application.) Hence it cannot be used with `MIDDLEWARE_CLASSES` in Django's
`settings.py` file, but instead has to be put in the WSGI pipeline, along with
tha Django application and the Beaker session middleware. To do this, it is
recommended to use `twod.wsgi`.

Once you've set up your middlewares, however, there are some convenince
functions that you can use with django. If you include `ao.social` in your
`INSTALLED_APPS`, you can load the `social` template tag library to use some
handy template tags, like `loginbutton`, `avatar`, or `apikey`.

Also you can include the `ao.social.user` template context processor to have
the `user` template variable available in all your templates.

Test the nodes used by the template rags::

    >>> from ao.social.templatetags import social
    >>> node = social.Avatar(120, 120)

    >>> node.gravatar('foo@example.com')
    'http://www.gravatar.com/avatar.php?size=120&gravatar_id=b48def645758b9...'
