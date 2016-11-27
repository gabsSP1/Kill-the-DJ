class Session:

    def __init__(self, admin, titre):
        self.users = dict()
        self.admin = admin
        self.titre = titre

    def addUser(self, user):
        if self.users.has_key(user.pseudo):
            return False
        else:
            self.users[user.pseudo] = user
            return True