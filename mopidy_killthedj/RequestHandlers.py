import tornado.web
import json
from mopidy.models import ModelJSONEncoder
from Services import *


services = Services()


class BaseHandler(tornado.web.RequestHandler):
    """
    Base class for for API endpoint request handlers. 
    Sets headers for CORS.
    All other request handlers should extend this class
    """
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE')

    def options(self):
        self.set_status(204)
        self.finish()


class IndexHandler(BaseHandler):
    def initialize(self, version, core):
        self.core = core
        self.version = version

    def get(self):
        self.write({'message': 'Kill the DJ API', 'version': self.version})
        self.set_header("Content-Type", "application/json")


class CreateOrJoinSession(BaseHandler):
    def initialize(self, core):
        self.core = core

    def get(self):
        self.write(
            json.dumps(services.sessionCreated()))


class CreateSession(BaseHandler):
    def initialize(self, core):
        self.core = core

    def post(self):
        data = json.loads(self.request.body)
        self.write(json.dumps(services.createSession(data, core=self.core)))


class JoinSession(BaseHandler):
    def post(self):
        data = json.loads(self.request.body)
        self.write(json.dumps(services.joinSession(data)))


class GetAllUsers(BaseHandler):
    def get(self):
        self.write(
            json.dumps(services.get_all_users(), default=jdefault))


def jdefault(o):
    return o.__dict__


class TracklistHandler(BaseHandler):
    def initialize(self, core):
        self.core = core

    def get(self):
        """
        Get the tracks currently in the tracklist
        :return:
        """

        tracklist = self.core.tracklist.get_tl_tracks().get()
        self.write({
            'tracklist': [{
                           'id': track_id,
                           'track': json.dumps({list(track)[0]},cls=ModelJSONEncoder)
                          }
                          for (track_id, track) in tracklist]
        })
        self.set_header("Content-Type", "application/json")

    def post(self):
        try:
            track_uri = self.get_query_argument('track_uri')
            self.core.library.lookup(track_uri).get()[0]
            services.session.tracklist.add_track(track_uri)
        except tornado.web.MissingArgumentError:
            self.write({"error": "'track' key not found"})
            self.set_status(400)

    def delete(self):
        try:
            track_uri = self.get_query_argument('track_uri')
            self.core.library.lookup(track_uri).get()[0]
            services.session.tracklist.remove_track(track_uri)
        except tornado.web.MissingArgumentError:
            self.write({"error": "'track' key not found"})
            self.set_status(400)


class TrackHandler(BaseHandler):
    def initialize(self, core):
        self.core = core

    def get(self):
        """
        Get information for a specific track
        :return:
        """
        try:
            track_uri = self.get_query_argument('track_uri')
            search_result = self.core.library.lookup(track_uri).get()[0]
            self.write(json.dumps({list(search_result)[0].tracks}, cls=ModelJSONEncoder))
        except tornado.web.MissingArgumentError:
            self.write({"error": "'track' key not found"})
            self.set_status(400)


class SearchHandler(BaseHandler):
    def initialize(self, core):
        self.core = core

    def error(self, code, message):
        self.write({
            'error': code,
            'message': message
        })

        self.set_status(code, message)

    def post(self):
        """
        Search for tracks
        :return:
        """
        field = self.get_body_argument('field', '')
        values = self.get_body_argument('values', '')

        if not field:
            return self.error(400, 'Please provide a field')

        search = {field: [values]}

        search_result = self.core.library.search(search).get()[0]

        self.set_header("Content-Type", "application/json")
        self.write("""
                    {
                        "uri": "%s",
                        "albums": %s,
                        "artists": %s,
                        "tracks": %s
                    }
                   """ % (search_result.uri,
                json.dumps(search_result.albums, cls=ModelJSONEncoder),
                json.dumps(search_result.artists, cls=ModelJSONEncoder),
                json.dumps(search_result.tracks, cls=ModelJSONEncoder)))


class VoteHandler(BaseHandler):
    def initialize(self, core):
        self.core = core

    def get(self):
        """
        Get the vote for a specific track
        :return:
        """

        try:
            track_uri = self.get_query_argument('track_uri')
            vote_count = services.session.tracklist.get_track_votes(track_uri)
            search_result = self.core.library.lookup(track_uri).get()[0]
            self.write({'track': json.dumps({list(search_result)[0]}, cls=ModelJSONEncoder),
                        'vote_count': vote_count})
            self.set_header("Content-Type", "application/json")
        except KeyError as k_err:
            self.set_status(400)
            self.write({"error": k_err.message})
        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "'track' key not found"})

    def post(self):
        """
        Increment the vote count for a specific track
        :return:
        """
        try:
            track_uri = self.get_query_argument('track_uri')
            vote_count = services.session.tracklist.get_track_votes(track_uri)
            services.session.tracklist.set_track_votes(track_uri, votes=(vote_count + 1))
            services.session.tracklist.update_tracklist()
            self.set_status(200)
        except KeyError as k_err:
            self.set_status(400)
            self.write({"error": k_err.message})
        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "'track' key not found"})

    def delete(self):
        """
        Decrement the vote count for a specific track
        :return:
        """
        try:
            track_uri = self.get_query_argument('track_uri')
            vote_count = services.session.tracklist.get_track_votes(track_uri)
            services.session.tracklist.set_track_votes(track_uri, votes=(vote_count - 1))
            services.session.tracklist.update_tracklist()
            self.set_status(200)
        except KeyError as k_err:
            self.set_status(400)
            self.write({"error": k_err.message})
        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "'track' key not found"})
