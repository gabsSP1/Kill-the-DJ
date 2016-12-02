from Session import *
from User import *
from .models import Tracklist


class Services:
    def __init__(self):
        self.session = None

    def sessionCreated(self):
        return self.session is not None

    def createSession(self, data, core):
        if self.sessionCreated():
            return False
        else:
            admin = User(data['admin'], True)
            tracklist = Tracklist(core)
            self.session = Session(admin, data['titre'], tracklist)
            return True

    def joinSession(self, data):
        if self.sessionCreated():
            return self.session.addUser(User(**data))
        else:
            return False

    def get_all_users(self):
        return self.session.users




