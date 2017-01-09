import tornado.web
import json
from mopidy.models import ModelJSONEncoder
from mopidy.exceptions import ValidationError
from services import *

services = Services()


class BaseHandler(tornado.web.RequestHandler):
    """
    Base class for for API endpoint request handlers.
    Sets headers for CORS.
    All other request handlers should extend this class
    """

    def initialize(self, core):
        self.core = core

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers",
                        "Origin, X-Requested-With, Content-Type, Accept")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, OPTIONS, DELETE')
        self.set_header("Content-Type", "application/json")

    def options(self):
        self.set_status(204)
        self.finish()

    def data_received(self, chunk):
        pass

    def write_error(self, status_code, **kwargs):
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            self.set_header('Content-Type', 'text/plain')
            err_cls, err, traceback = kwargs['exc_info']
            self.finish('{"error": "%(message)s"}' % {"message": err.message})
        else:
            self.set_status(status_code)
            if 'reason' in kwargs.keys():
                self.finish(kwargs['reason'])
            else:
                self.finish('{"error": %(message)s}' % {"message": self._reason})


class IndexHandler(BaseHandler):
    def initialize(self, version, core):
        self.core = core
        self.version = version

    def get(self):
        self.write({'message': 'Kill the DJ API', 'version': self.version})

    def data_received(self, chunk):
        pass


class SessionHandler(BaseHandler):
    def get(self):
        self.set_status(200)
        self.write(
            json.dumps({"active": services.session_created()}))

    def post(self):
        data = json.loads(self.request.body)
        if services.create_session(data, core=self.core):
            self.set_status(201)
            self.write(json.dumps(data))

    def data_received(self, chunk):
        pass


class UsersHandler(BaseHandler):
    def post(self):
        data = json.loads(self.request.body)
        self.set_status(201)
        self.write(json.dumps(services.join_session(data)))

    def get(self):
        self.set_status(200)
        self.write(
            json.dumps(services.get_all_users(), default=jdefault))

    def delete(self):
        data = json.loads(self.request.body)
        self.set_status(201)
        self.write(json.dumps(services.leave_session(data)))

    def data_received(self, chunk):
        pass


def jdefault(o):
    return o.__dict__


class TracklistHandler(BaseHandler):
    def get(self):
        """
        Get the tracks currently in the tracklist
        """
        try:
            # tracklist = self.core.tracklist.get_tl_tracks().get()
            tracks = []
            for track, count in services.session.tracklist.tracklist:
                if track:
                    tracks.append(
                        {"uri": track.track_uri,
                         "votes": track.votes}
                    )
            """
            tracks = [
                        json.dumps(track, cls=ModelJSONEncoder)
                        for (tlid, track) in tracklist
                     ]
            """
            self.set_status(200)
            self.write(json.dumps(tracks))

        except AttributeError as attribute_error:
            self.set_status(400)
            self.write({"error": attribute_error.message})

    def post(self):
        """
        Add a track to the tracklist
        The track to be added is specified by its uri, passed as a query parameter.
        If the track is successfully added to the tracklist a JSON serialize model of
        the track is returned in the response body.
        """
        try:
            track_uri = self.get_query_argument('uri')
            # check that the track exists in the active mopidy backends
            tracks = self.core.library.lookup(uris=[track_uri]).get()[track_uri]
            if tracks:
                services.session.tracklist.add_track(track_uri)
                self.set_status(201)
                self.write(json.dumps(tracks[0], cls=ModelJSONEncoder))
            else:
                self.set_status(404)
                self.write({"error": "track not found"})

        except AttributeError as attribute_error:
            self.set_status(400)
            self.write({"error": attribute_error.message})

        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "query parameter 'uri' is missing"})

    def delete(self):
        """
        Delete a track from the tracklist. 
        The track to be deleted is specified by its uri, passed as a query parameter
        """
        try:
            track_uri = self.get_query_argument('uri')
            # check that the track exists
            tracks = self.core.library.lookup(uris=[track_uri]).get()[track_uri]
            if tracks:
                services.session.tracklist.remove_track(track_uri)
                self.set_status(200)
                self.write(json.dumps(tracks[0], cls=ModelJSONEncoder))
            else:
                self.set_status(404)
                self.write({"error": "track not found"})

        except AttributeError as attribute_error:
            self.set_status(400)
            self.write({"error": attribute_error.message})

        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "query parameter 'uri' is missing"})

        except KeyError as key_err:
            self.set_status(404)
            self.write({"error": key_err.message})

    def data_received(self, chunk):
        pass


class VoteHandler(BaseHandler):
    def get(self):
        """
        Get the vote for a specific track
        """
        try:
            track_uri = self.get_query_argument('uri')
            vote_count = services.session.tracklist.get_track_votes(track_uri)
            tracks = self.core.library.lookup(uris=[track_uri]).get()[track_uri]
            if tracks:
                self.set_status(200)
                self.write({'track': json.dumps(tracks[0], cls=ModelJSONEncoder),
                            'vote_count': vote_count})
            else:
                self.set_status(404)
                self.write({"error": "track not found"})

        except KeyError as key_err:
            self.set_status(400)
            self.write({"error": key_err.message})

        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "query parameter 'uri' is missing"})

    def put(self):
        """
        Increment the vote count for a specific track
        """
        try:
            track_uri = self.get_query_argument('uri')
            vote_count = services.session.tracklist.get_track_votes(track_uri)
            services.session.tracklist.set_track_votes(track_uri, votes=(vote_count + 1))
            services.session.tracklist.update_tracklist()
            self.set_status(200)

        except KeyError as key_err:
            self.set_status(404)
            self.write({"error": key_err.message})

        except ValueError as val_err:
            self.set_status(400)
            self.write({"error": val_err.message})

        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "query parameter 'uri' is missing"})

    def delete(self):
        """
        Decrement the vote count for a specific track
        :return:
        """
        try:
            track_uri = self.get_query_argument('uri')
            vote_count = services.session.tracklist.get_track_votes(track_uri)
            services.session.tracklist.set_track_votes(track_uri, votes=(vote_count - 1))
            services.session.tracklist.update_tracklist()
            self.set_status(200)

        except KeyError as key_err:
            self.set_status(404)
            self.write({"error": key_err.message})

        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "query parameter 'uri' is missing"})

    def data_received(self, chunk):
        pass


class TrackHandler(BaseHandler):
    def get(self):
        """
        Get information for a specific track
        :return:
        """
        try:
            track_uri = self.get_query_argument('uri')

            tracks = self.core.library.lookup(uris=[track_uri]).get()[track_uri]
            if tracks:
                self.write(json.dumps(tracks[0], cls=ModelJSONEncoder))
            else:
                self.set_status(404)
                self.write({"error": "track not found"})

        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"error": "query parameter 'uri' is missing"})

    def data_received(self, chunk):
        pass


class SearchHandler(BaseHandler):
    def post(self):
        """
        Search for tracks
        """
        try:
            data = self.request.body

            if not data:
                self.set_status(400)
                self.write("Search query is missing from body")
            else:
                search_parameters = json.loads(data)
                query = search_parameters['query'] if 'query' in search_parameters else None
                uris = search_parameters['uris'] if 'uris' in search_parameters else None
                exact = search_parameters['exact'] if 'exact' in search_parameters else False

                search_result = self.core.library.search(query=query,
                                                         uris=uris,
                                                         exact=exact
                                                         ).get()
                self.set_status(201)
                self.write(json.dumps(search_result, cls=ModelJSONEncoder))

        except ValidationError as validation_err:
            self.set_status(400)
            self.write({"error": validation_err.message})

    def data_received(self, chunk):
        pass
