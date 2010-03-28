class UserBase(object):
    """Base class for `User` implementations.."""

    def update(self, method, data={}):
        """Updates user information."""

        if method == 'ajax':
            # Ajax callbacks must provide a valid key-value mapping
            for item in data.iteritems():
                setattr(self.__user, *item)

        if method in ('twitter', 'google'):
            # Twitter and Google provide the user's name
            self.__user.name = data['name']

        if method == 'twitter':
            # Twitter also provides the user's profile image
            self.__user.image = data['profile_image_url']

        if method == 'google':
            # Google also provides the user's email
            self.__user.email = data['email']

        if method == 'facebook':
            # For facebook, we have to do an API call to retrive the info
            info = ['name', 'email', 'pic_square_with_logo', 'profile_url']
            uid = self.__user.uid.split(':', 1)[1]
            data = self.__facebook_client.users.getInfo(uid, info)[0]
            self.__user.name = data['name']
            self.__user.email = data['email']
            self.__user.image = data['pic_square_with_logo']
            self.extend_token(method, profileurl=data['profile_url'])

        self.__user.put()

    def post_facebook(self, message):
        """Post the message to the user's facebook profile."""
        self.__facebook_client.stream.publish(
            uid=self.accounts['facebook'],  # TODO: reimplement `accounts`
            message=message,
        )
