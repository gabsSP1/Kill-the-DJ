

class SessionNotActiveError(Exception):
    def __init__(self, *args, **kwargs):
        super(SessionNotActiveError, self).__init__(*args, **kwargs)


class UserNotFoundError(Exception):
    def __init__(self, *args, **kwargs):
        super(UserNotFoundError, self).__init__(*args, **kwargs)


class AuthenticationError(Exception):
    def __init__(self, *args, **kwargs):
        super(AuthenticationError, self).__init__(*args, **kwargs)

