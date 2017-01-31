from session import Session
from user import User
from tracklist import Tracklist
from ktd_exceptions import SessionNotActiveError, UserNotFoundError
import os
import hashlib


class Services:
    def __init__(self):
        self.session = None
        self.cookie_secret = os.urandom(32)
        self.hash = hashlib.sha256()

    def session_created(self):
        """
        Method for checking that the session is active.
        :return bool: session status
        """
        return self.session is not None

    def create_session(self, data, core):
        if self.session_created():
            raise SessionNotActiveError("session already active")
        else:
            username = str(data['admin_username'])
            hash_string = username + self.cookie_secret
            self.hash.update(hash_string)
            cookie = self.hash.hexdigest()

            admin_user = User(data['admin_username'], cookie, True)
            tracklist = Tracklist(core)
            self.session = Session(admin_user, data['session_name'], tracklist)
            self.session.add_user(admin_user)

    def join_session(self, data):
        if self.session_created():
            username = str(data['username'])
            hash_string = (username + self.cookie_secret)
            self.hash.update(hash_string)
            cookie = self.hash.hexdigest()

            user = User(username, cookie)
            self.session.add_user(user)
        else:
            raise SessionNotActiveError("session not active")

    def leave_session(self, data):
        if self.session_created():
            username = data['username']
            return self.session.remove_user(username)
        else:
            raise SessionNotActiveError("session not active")

    def get_user(self, username):
        if username in self.session.users:
            return self.session.users[username]
        else:
            raise UserNotFoundError("user with username: %s not in session" % username)

    def get_user_by_cookie(self, cookie):
        """
        Try to fetch the user with the given cookie. If no user with the
        given cookie exists an error is raised.
        :param string cookie: Cookie that identifies the user
        :return:
        """
        if cookie in self.session.user_cookies:
            user = self.session.user_cookies[cookie]
            return user
        else:
            raise UserNotFoundError("user with given cookie not in session")

    def get_all_users(self):
        return self.session.users.values()




