

class Session:
    def __init__(self, admin_username, session_name, tracklist, max_votes):
        self.users = dict()
        self.user_cookies = dict()
        self.admin_username = admin_username
        self.session_name = session_name
        self.tracklist = tracklist
        self.max_votes = max_votes

    def add_user(self, user):
        if user.username in self.users:
            raise Exception("user with username: %s already in session"
                                % user.username)
        else:
            user.votes_left = self.max_votes
            # Adding user to cookie and user dictionaries
            self.users[user.username] = user
            self.user_cookies[user.cookie] = user

    def remove_user(self, username):
        if username not in self.users:
            raise Exception("user with username: %s not in session"
                                % username)
        elif self.users[username].is_admin:
            raise Exception("Impossible to ban the admin")
        else:
            # Deleting user from cookie and user dictionaries
            del self.user_cookies[self.users[username].cookie]
            del self.users[username]

    def reset_votes(self):
        for user in self.users.items():
            user.votes_left = self.max_votes
