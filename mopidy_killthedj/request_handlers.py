from operator import attrgetter

import tornado.web
import json
from mopidy.models import ModelJSONEncoder
from mopidy.exceptions import ValidationError
from services import *

services = Services()


class Listener(CoreListener, pykka.ThreadingActor):

    def __init__(self):
        super(Listener, self).__init__()

    def track_playback_ended(self, tl_track, time_position):
        del services.session.tracklist.trackToPlay[max(services.session.tracklist.trackToPlay.values(), key=attrgetter('votes')).track.uri]

listener = Listener()
listener.start()

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
                        "Origin, X-Requested-With, Content-Type, Accept, Username")
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
        else:
            self.set_status(400)

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
            self.set_status(200)
            tracks = []
            for track in sorted(services.session.tracklist.trackToPlay.values(), key=attrgetter("votes"), reverse=True):
                if track:
                    tracks.append(
                        {"track": track.track,
                         "votes": track.votes}
                    )

            self.write(json.dumps(tracks, cls=ModelJSONEncoder))

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
            data = json.loads(self.request.body)
            track_uri = data['uri']
            # check that the track exists in the active mopidy backends
            tracks = self.core.library.lookup(uris=[track_uri]).get()[track_uri]
            if tracks:
                if self.core.playback.get_state().get() != "playing":
                    self.core.tracklist.add(at_position=1, uri=tracks[0].uri)
                    services.play_song(self.core)
                else:
                    services.session.tracklist.add_track(tracks[0])
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
            data = json.loads(self.request.body)
            track_uri = data['uri']
            services.session.tracklist.remove(filter({'uri': track_uri}))
            self.set_status(200)
            self.write(json.dumps(track_uri, cls=ModelJSONEncoder))

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


class PlaybackHandler(BaseHandler):
    def get(self):
        """
        Get the uri of track currently playing
        """
        try:
            current_track = self.core.playback.get_current_track().get()
            if current_track:
                self.set_status(200)
                self.write({"uri": current_track.uri})
            else:
                self.set_status(404)
                self.write({"error": "no track currently playing"})

        except AttributeError as attribute_error:
            self.set_status(400)
            self.write({"error": attribute_error.message})

    def data_received(self, chunk):
        pass


class VoteHandler(BaseHandler):

    def put(self):
        """
        Increment the vote count for a specific track
        """

        try:
            data = json.loads(self.request.body)
            track_uri = data['uri']
            services.session.tracklist.trackToPlay[track_uri].votes += 1
            first_track = max(services.session.tracklist.trackToPlay.values(), key=attrgetter('votes'))
            self.core.tracklist.remove(self.core.tracklist.filter({'uri': first_track.track.uri}))
            self.core.tracklist.add(at_position=1, uri=first_track.track.uri)
            self.write(json.dumps(track_uri))
            self.set_status(200)

        except KeyError as key_err:
            self.set_status(404)
            self.write({"error": key_err.message})

        except ValueError as val_err:
            self.set_status(400)
            self.write({"error": val_err.message})

        except AttributeError as attribute_error:
            self.set_status(400)
            self.write({"error": attribute_error.message})

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
            data = json.loads(self.request.body)
            track_uri = data['uri']

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
