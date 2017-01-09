

class Session:
    def __init__(self, admin_username, session_name, tracklist):
        self.users = dict()
        self.admin_username = admin_username
        self.session_name = session_name
        self.tracklist = tracklist

    def add_user(self, user):
        if self.users.has_key(user.username):
            return False
        else:
            self.users[user.username] = user
            return True

    def remove_user(self, username):
        print self.users.keys()
        print username
        if not self.users.has_key(username):
            return False
        else:
            del self.users[username]
            return True