class TrackStructure(object):
    def __init__(self, track, user):
        self.track = track
        self.user = user
        self.votes = 0


class Tracklist(object):
    """
    Tracklist works as following:
    Track with the most votes goes first. After that the track with one vote less.
    """
    def __init__(self, core):
        self.core = core
        self.core.tracklist.set_consume(True)
        self.trackToPlay = {}

    def add_track(self, track, user):
        if track.uri not in self.trackToPlay:
            track_structure = TrackStructure(track, user)
            self.trackToPlay[track.uri] = track_structure

    def remove_track(self, track_uri):
        """
        Remove a track from the tracklist. Raise KeyError if not found.
        """
        if track_uri in self.trackToPlay:
            del self.trackToPlay[track_uri]
        else:
            raise KeyError('Track not in tracklist')
