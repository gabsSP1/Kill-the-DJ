from operator import attrgetter

import pykka

from mopidy.core import CoreListener

from session import *
from user import *
from tracklist import Tracklist
from mopidy import backend



class Services():

    def __init__(self):
        self.session = None
        self.core = None

    def session_created(self):
        return self.session is not None

    def create_session(self, data, core):
        self.core  = core
        if self.session_created():
            return False
        else:
            admin = User(data['admin_username'], True)
            tracklist = Tracklist(core)
            self.session = Session(admin, data['session_name'], tracklist)
            self.session.add_user(admin)
            return True

    def get_self(self):
        return self

    def join_session(self, data):
        if self.session_created():
            return self.session.add_user(User(data["username"]))
        else:
            return False

    def leave_session(self, data):
        if self.session_created():
            return self.session.remove_user(data["username"])
        else:
            return False

    def get_all_users(self):
        return self.session.users.values()

    def play_song(self, uri):
        self.core.tracklist.add(at_position=1, uri=uri)
        self.core.playback.play()




