import tornado.web

import tornado.web
import json

from Services import *

services = Services()
class CreateOrJoinSession(tornado.web.RequestHandler):
    def initialize(self, core):
        self.core = core

    def get(self):
        self.write(
            json.dumps(services.sessionCreated()))

class CreateSession(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        self.write(json.dumps(services.createSession(data)))

class JoinSession(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        self.write(json.dumps(services.joinSession(data)))

class GetAllUsers(tornado.web.RequestHandler):
    def get(self):
        self.write(
            json.dumps(services.get_all_users(), default=jdefault))


def jdefault(o):
    return o.__dict__
