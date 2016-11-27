from Session import *
from User import *
class Services:
    def __init__(self):
        self.session = None

    def sessionCreated(self):
        return self.session is not None

    def createSession(self, data):
        if self.sessionCreated():
            return False
        else:
            admin = User(data['admin'], True)
            self.session = Session(admin, data['titre'])
            return True

    def joinSession(self, data):
        if self.sessionCreated():
            return self.session.addUser(User(**data))
        else:
            return False

    def get_all_users(self):
        return self.session.users


