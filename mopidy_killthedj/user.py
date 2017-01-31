
class User(object):
    def __init__(self, username, cookie, is_admin=False, votes_left=10):
        self.username = username
        self.cookie = cookie
        self.is_admin = is_admin
        self.votes_left = votes_left

    def decrement_votes(self):
        if self.votes_left > 0:
            self.votes_left -= 1
        else:
            raise Exception("user has no votes left")

    def __repr__(self):
        return str('{"username": "%(username)s", "is_admin": %(is_admin)s}'
                   % {"username": self.username, "is_admin": self.is_admin})
