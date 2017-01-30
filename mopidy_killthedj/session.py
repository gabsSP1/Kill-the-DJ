import os

class Session:
    def __init__(self, admin_username, session_name, tracklist):
        self.users = dict()
        self.admin_username = admin_username
        self.session_name = session_name
        self.tracklist = tracklist

    def add_user(self, user):
        if user.username in self.users:
            raise Exception("user with username: %s already in session"
                                % user.username)
        else:
            self.users[user.username] = user

    def remove_user(self, username):
        if username not in self.users:
            raise Exception("user with username: %s not in session"
                                % username)
        else:
            del self.users[username]