from session import Session
from user import User
from tracklist import Tracklist
import os
import hashlib


class Services:
    def __init__(self):
        self.session = None
        self.cookie_secret = os.urandom(26)
        self.hashf = hashlib.sha256()

    def session_created(self):
        """
        Method for checking that the session is active.
        :return bool: session status
        """
        return self.session is not None

    def create_session(self, data, core):
        if self.session_created():
            raise Exception("session not active")
        else:
            self.hashf.update(data['admin_username'] + self.cookie_secret)
            cookie = self.hashf.digest()
            admin = User(data['admin_username'], cookie, True)
            tracklist = Tracklist(core)
            self.session = Session(admin, data['session_name'], tracklist)
            self.session.add_user(admin)

    def join_session(self, data):
        if self.session_created():
            username = data['username']
            self.hashf.update(username + self.cookie_secret)
            cookie = self.hashf.digest()
            user = User(username, cookie)
            self.session.add_user(user)
        else:
            raise Exception("session not active")

    def leave_session(self, data):
        if self.session_created():
            username = data['username']
            return self.session.remove_user(username)
        else:
            raise Exception("session not active")

    def get_user(self, username):
        if username in self.session.users:
            return self.session.users[username]
        else:
            raise Exception("user with username: %s not in session"
                                % username)

    def get_all_users(self):
        return self.session.users.values()




