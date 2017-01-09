from session import *
from user import *
from tracklist import Tracklist


class Services:
    def __init__(self):
        self.session = None

    def session_created(self):
        return self.session is not None

    def create_session(self, data, core):
        if self.session_created():
            return False
        else:
            admin = User(data['admin_username'], True)
            tracklist = Tracklist(core)
            self.session = Session(admin, data['session_name'], tracklist)
            self.session.add_user(admin)
            return True

    def join_session(self, data):
        if self.session_created():
            return self.session.add_user(User(data["username"]))
        else:
            return False

    def get_all_users(self):
        return self.session.users




