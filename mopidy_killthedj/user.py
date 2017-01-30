class User():
    def __init__(self, username, cookie, is_admin=False):
        self.username = username
        self.cookie = cookie
        self.is_admin = is_admin

    def __repr__(self):
        return str('{"username": "%(username)s", "is_admin": %(is_admin)s}'
                   % {"username": self.username, "is_admin": self.is_admin})
