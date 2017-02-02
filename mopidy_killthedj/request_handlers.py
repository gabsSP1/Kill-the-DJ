import tornado.web
import json
from mopidy.models import ModelJSONEncoder
from mopidy.exceptions import ValidationError
from services import *
from ktd_exceptions import SessionNotActiveError, UserNotFoundError

services = Services()


class Listener(CoreListener, pykka.ThreadingActor):

    def __init__(self):
        super(Listener, self).__init__()

    def track_playback_ended(self, tl_track, time_position):
        first_track = max(services.session.tracklist.trackToPlay.values(), key=attrgetter('votes'))
        services.play_song(first_track.track.uri)
        del services.session.tracklist.trackToPlay[first_track.track.uri]

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
                        "Origin, X-Requested-With, Content-Type, Accept, Username, X-KTD-Cookie")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, PUT, OPTIONS, DELETE")
        self.set_header("Content-Type", "application/json")

    def options(self):
        self.set_status(204)
        self.finish()

    def data_received(self, chunk):
        pass

    def write_error(self, status_code, **kwargs):
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            self.set_header("Content-Type", "text/plain")
            err_cls, err, traceback = kwargs["exc_info"]
            self.finish('{"error": "%(message)s"}' % {"message": err.message})
        else:
            self.set_status(status_code)
            if "reason" in kwargs.keys():
                self.finish(kwargs["reason"])
            else:
                self.finish('{"error": %(message)s}' % {"message": self._reason})


class IndexHandler(BaseHandler):
    def initialize(self, version, core):
        self.core = core
        self.version = version

    def get(self):
        self.write({"message": "Kill the DJ API", "version": self.version})

    def data_received(self, chunk):
        pass


class SessionHandler(BaseHandler):
    def get(self):
        """
        Get status of session
        :return:
        """
        try:
            self.set_status(200)
            self.write(
                json.dumps({"active": services.session_created()}))

        except SessionNotActiveError as err:
            self.set_status(400)
            self.write({"error": err.message})

    def post(self):
        """
        Create a new session and add the ADMINISTRATOR user

        The ADMINISTRATOR cookie is generated and returned in the response.
        The ADMINISTRATOR cookie identifies the ADMINISTRATOR user, and has to be used
        in all the requests that require ADMINISTRATOR privileges.
        :return:
        """
        try:
            data = json.loads(self.request.body)
            username = data["admin_username"]
            session_name = data['session_name']
            session_length = data['session_length']
            max_votes = data['max_votes']

            services.create_session(data, core=self.core)
            cookie = services.get_user(username).cookie

            print cookie
            self.set_status(201)
            self.write(json.dumps({"session_name": session_name,
                                   "session_length": session_length,
                                   "max_votes": max_votes,
                                   "admin_user": {"username": username,
                                                  "cookie": cookie}},
                                  encoding='latin1'))

        except KeyError as key_err:
            self.set_status(400)
            self.write({"error": "attribute %s not in request body" % key_err.message})

    def data_received(self, chunk):
        pass


class UsersHandler(BaseHandler):
    def post(self):
        """
        Method for adding a USER to the session.

        The USER to be added from the session is specified in the
        request body. If the request was successful the representation of the
        USER is returned in the response.

        A cookie is generated for each USER added to the session.
        The cookie identifies the USER uniquely, and has to be used in all
        requests that require USER privileges.

        If the session is not active or a USER with that username already
        is in the session, an error response is sent.
        :return:
        """
        try:
            data = json.loads(self.request.body)
            self.set_status(201)
            services.join_session(data)
            username = data["username"]
            cookie = services.get_user(username).cookie
            self.write(json.dumps({"username": username,
                                   "cookie": cookie}, encoding='latin1'))

        # Catches error for when session has not been created
        except SessionNotActiveError as err:
            self.set_status(400)
            self.write({"error": err.message})

    def get(self):
        """
        Method for getting the USERs currently in the session.
        If the request was successful a list of USERSs is returned
        in the response

        If the session is not active an error response is sent.

        TODO: Figure out privileges required for request?
        :return:
        """
        try:
            self.set_status(200)
            self.write(
                json.dumps(services.get_all_users(), default=jdefault))

        except SessionNotActiveError as err:
            self.set_status(400)
            self.write({"error": err.message})

    def delete(self):
        """
        Method for removing a USER from the session.
        The USER to be removed from the session is specified by the username
        in the request body. If the request was successful the representation
        of the USER is returned in the response

        If the session is not active or no USER with that username
        is in the session, an error response is sent.

        Only the ADMINISTRATOR user can delete users from the session.
        Request requires ADMINISTRATOR privileges.
        :return:
        """
        try:
            # Try to get the cookie, cookie is None if the cookie is not set
            cookie = self.request.headers.get("X-KTD-Cookie")
            user = services.get_user_by_cookie(cookie)
            if user.is_admin:
                data = json.loads(self.request.body)
                self.set_status(200)
                services.leave_session(data)
                self.write(data)
            else:
                self.set_status(403)
                self.write({"error": "not authorized to delete users"})

        except SessionNotActiveError as err:
            self.set_status(400)
            self.write({"error": err.message})

    def data_received(self, chunk):
        pass


def jdefault(o):
    return o.__dict__


class TracklistHandler(BaseHandler):
    def get(self):
        """
        Get the tracks currently in the tracklist

        Request requires USER privileges.
        """
        try:
            # Try to get the cookie, cookie is None if the cookie is not set
            cookie = self.request.headers.get("X-KTD-Cookie")
            # if cookie is none get_user_by_cookie raises an error
            user = services.get_user_by_cookie(cookie)

            # tracklist = self.core.tracklist.get_tl_tracks().get()

            tracks = []
            for track in sorted(services.session.tracklist.trackToPlay.values(), key=attrgetter("votes"), reverse=True):
                if track:
                    tracks.append(
                        {"track": track.track,
                         "votes": track.votes}
                    )

            self.set_status(200)
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

        Every USER can add tracks to the tracklist.
        Request requires USER privileges.
        """
        try:
            # Try to get the cookie, cookie is None if the cookie is not set
            cookie = self.request.headers.get("X-KTD-Cookie")

            print cookie
            # if cookie is none get_user_by_cookie raises an error
            user = services.get_user_by_cookie(cookie)

            data = json.loads(self.request.body)
            track_uri = data["uri"]
            # check that the track exists in the active mopidy backends
            tracks = self.core.library.lookup(uris=[track_uri]).get()[track_uri]
            if tracks:
                if self.core.playback.get_state().get() != "playing":
                    services.play_song(uri=tracks[0].uri)
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

        except UserNotFoundError as err:
            self.set_status(400)
            self.write({"error": err.message})

    def delete(self):
        """
        Delete a track from the tracklist. 
        The track to be deleted is specified by its uri, passed as a query parameter

        Only the ADMINISTRATOR user can delete tracks from the tracklist.
        Request requires ADMINISTRATOR privileges.
        """
        try:
            # Try to get the cookie, cookie is None if the cookie is not set
            cookie = self.request.headers.get("X-KTD-Cookie")
            user = services.get_user_by_cookie(cookie)
            # Check that the user has admin privileges
            if user.is_admin:
                data = json.loads(self.request.body)
                track_uri = data["uri"]
                # check that the track exists
                tracks = self.core.library.lookup(uris=[track_uri]).get()[track_uri]
                if tracks:
                    services.session.tracklist.remove_track(track_uri)
                    self.set_status(200)
                    # return a representation of the track
                    self.write(json.dumps(tracks[0], cls=ModelJSONEncoder))
                else:
                    self.set_status(404)
                    self.write({"error": "track not found"})
            else:
                self.set_status(403)
                self.write({"error": "not authorized to delete tracks"})

        except (AttributeError,
                SessionNotActiveError,
                UserNotFoundError) as err:
            self.set_status(400)
            self.write({"error": err.message})

        except KeyError as key_err:
            self.set_status(404)
            self.write({"error": key_err.message})

    def data_received(self, chunk):
        pass


class PlaybackHandler(BaseHandler):
    def get(self, function):
        """
        Get the uri of track currently playing

        Every USER can get information about the currently playing track.
        Request requires USER privileges.
        """
        try:
            # Try to get the cookie, cookie is None if the cookie is not set
            cookie = self.request.headers.get("X-KTD-Cookie")
            # if cookie is none get_user_by_cookie raises an error
            user = services.get_user_by_cookie(cookie)

            if function == "current":
                current_track = self.core.playback.get_current_track().get()
                if current_track:
                    self.set_status(200)
                    self.write({"uri": current_track.uri})
                else:
                    self.set_status(404)
                    self.write({"error": "no track currently playing"})
            else:
                self.set_status(404)
                self.write({"error": "function: %s not supported" % function})

        except (AttributeError,
                SessionNotActiveError,
                UserNotFoundError) as err:
            self.set_status(400)
            self.write({"error": err.message})

    def data_received(self, chunk):
        pass


class VoteHandler(BaseHandler):
    def put(self):
        """
        Increment the vote count for a track by 1

        Every user can vote for tracks
        Request requires USER privileges.
        """
        try:
            # Try to get the cookie, cookie is None if the cookie is not set
            cookie = self.request.headers.get("X-KTD-Cookie")
            # if cookie is none get_user_by_cookie raises an error
            user = services.get_user_by_cookie(cookie)

            data = json.loads(self.request.body)
            track_uri = data["uri"]
            #services.session.tracklist.increment_track_votes(track_uri)
            #services.session.tracklist.update_tracklist()
            services.session.tracklist.trackToPlay[track_uri].votes += 1
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

    def delete(self):
        """
        Decrement the vote count for a track by 1

        Every user can vote for tracks
        Request requires USER privileges.
        """
        try:
            # Try to get the cookie, cookie is None if the cookie is not set
            cookie = self.request.headers.get("X-KTD-Cookie")
            # if cookie is none get_user_by_cookie raises an error
            user = services.get_user_by_cookie(cookie)

            data = json.loads(self.request.body)
            track_uri = data["uri"]
            services.session.tracklist.decrement_track_votes(track_uri)
            services.session.tracklist.update_tracklist()
            self.set_status(200)

        except KeyError as key_err:
            self.set_status(404)
            self.write({"error": key_err.message})

        except (AttributeError,
                ValueError,
                SessionNotActiveError,
                UserNotFoundError) as err:
            self.set_status(400)
            self.write({"error": err.message})

    def data_received(self, chunk):
        pass


class TrackHandler(BaseHandler):
    def get(self):
        """
        Get information for a specific track
        """
        try:
            data = json.loads(self.request.body)
            track_uri = data["uri"]

            tracks = self.core.library.lookup(uris=[track_uri]).get()[track_uri]
            if tracks:
                self.write(json.dumps(tracks[0], cls=ModelJSONEncoder))
            else:
                self.set_status(404)
                self.write({"error": "track not found"})

        except Exception as err:
            self.set_status(400)
            self.write({"error": err.message})

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
                query = search_parameters["query"] if "query" in search_parameters else None
                uris = search_parameters["uris"] if "uris" in search_parameters else None
                exact = search_parameters["exact"] if "exact" in search_parameters else False

                search_result = self.core.library.search(query=query,
                                                         uris=uris,
                                                         exact=exact
                                                         ).get()
                search_result_json = json.dumps(search_result, cls=ModelJSONEncoder)
                #if search_result_json:
                #    search_result_json = filter_search_result(json.loads(search_result_json))
                self.set_status(201)
                self.write(search_result_json)

        except ValidationError as validation_err:
            self.set_status(400)
            self.write({"error": validation_err.message})

    def data_received(self, chunk):
        pass


def filter_search_result(search_result_json):
    filtered_result = []
    for track in search_result_json[0]["tracks"]:
        filtered_result.append({
            "uri": track["uri"],
            "name": track["name"],
            "length": track["length"],
            "artists": track["artists"]
        })
    return filtered_result
