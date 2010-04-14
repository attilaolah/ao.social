About the middleware
====================

``ao.social`` is a social networking middleware that aims to provide a generic
interface for multiple social networking web services (*Facebook*, *Twitter*,
*Google* (OpenID login) and *LinkedIn* are currently implemented). It provides
a standard WSGI middleware that adds the ``ao.social.user`` environment
variable to the WSGI environment.

.. note::

   You also need to add *Beaker* to your WSGI pipline, otherwise the middleware
   won't be able to *remember* the users. It's up to the developer to configure
   Beaker. The recommended setup is using secure cookies to store session data;
   however, other methods should work just as fine.

.. note::

   To use the ``ao.social`` middleware with *Django*, you need to add it to the
   WSGI pipeline just as you would with any other framework. ``ao.social`` does
   not provide a Django middleware. Instead, it won't even call Django if it is
   not required (i.e. on the login handler pages). The recommended way of
   plumbing Django into the WSGI pipeline along with Beaker and ``ao.social``
   is using the ``twod.wsgi`` package.


Configurung the middleware
==========================

The social middleware is a generic, stand-alone component that can be used for
common social networking interactions, regardless of the web framework being
used. However, it needs some configurations. To make things easier, you can
store this configuration in an external settings file. For example, you can
create a YAML config file like this::

    login_path: /login/%s/
    user_class: foomodule.models.User
    facebook:
      key: your-facebook-api-key
      secret: your-facebook-api-secret
    twitter:
      key: your-twitter-consumer-key
      secret: your-twitter-consumer-secret
    google:
      realm: http://www.example.com/
      secret: your-google-api-secret
      callback: http://www.example.com/login/google/
    linkedin:
      key: your-linkedin-consumer-key
      secret: your-linkedin-consumer-secret

.. note::

   This is a minimal configuration. You can override some of the default
   middleware behavior by using extra parameters in the configuration. For more
   information, take a look at the documented tests and the source code.

If you do not wish to use one of the services, simply leave out that section
from the config file. That way the client machinery won't be loaded at all.

To load the config file from the file, use the *PyYAML* module::

    >>> import yaml
    >>> with open('auth.yaml', 'r') as file:
    ...     conf = yaml.load(confstr)

.. note::
   
   For the google login to work, the callback must be the login path for
   google::

    >>> conf['login_path'] % 'google'
    '/login/google/'

    >>> conf['google']['callback']
    'http://www.example.com/login/google/'

Say your downstream WSGI application is ``wsgi_app``, you can initialize the
middleware like this::

    >>> from ao.social import middleware
    >>> app = middleware.AuthMiddleware(wsgi_app, conf)


About the ``User`` object
=========================


The ``ao.social`` middleware will put the user object in the WSGI enviromnent.
You chould supply the user class when instantiating the middleware, and the
user class should be available to the middleware at that time. The base user
class is available as ``ao.social.UserBase``, but you should subclass it with
the *ORM* model of your choice to make it persistent. A basic interface is
provided, but you need to implement some additional methods. Take a look at the
source code and the test for a list of methods that you need to implement.
(Those are the ones that raise ``NotImplementedError``.)

To log in a user with, say, twitter, redirect to ``config['login_path'] %
'twitter'``. Same rule applies for LinkedIn and Google. Facebook is a little
different, you need to use the XFBML tags to log in, and upon a successful
login, redirect to ``config['login_path'] % 'facebook'`` so that the user's key
gets added to the Beaker session and the credentials (and tokens) get stored in
the user model.

.. note::

   For facebook, it is enough to ping the login path (i.e. make a simple AJAX
   call).

To post to the user's profile, simply use ``user.post(message)``, where message
is a string or unicode that contains the message to be posted. This works for
Facebook (status updates), Twitter (tweets) and LinkedIn (status updates).
Google Buzz is not implemented yet, as the Buzz folks haven't added OAuth
support at the time of writing this module. It will probably be supported in
the future.


Django template tags
====================


There are some handy shortcats for Django applications. If you add
``ao.social`` to your ``INSTALLED_APPS``, the ``social`` template library will
become available. It contains the following three template tags::

    {% apikey method %}

``apikey`` returns the api key for the given method. Not available for Google.

::

    {% liginbutton method onlogin %}

Renders a login button. For Facebook, it will render an XFBML login button. The
developer is responsible for definig the XFBML namespace and initializing the
Facebook Connect script in the template.

.. note::

   The ``onlogin`` parameter is only valid for Facebook. It is a JavaScript
   statement that will be executed upon successful login.

::

    {% avatar height width %}

Displays the user's profile picture.

.. note::

   For Google, the *Gravatar* API is used to construct a profile picture from
   the user's email. LinkedIn doesn't provide a profile picture so the
   ``avatar`` template tag won't work for LinkedIn users.


Django template context processors
==================================


Add the ``ao.social.user`` template context processor to your django
configuration and you'll have the ``user`` variable available in all your
templates.


