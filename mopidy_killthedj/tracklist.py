class TrackStructure(object):
    def __init__(self, track):
        self.track = track
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
        self.trackPlayed = {}
        self.trackHistory = []

    def add_track(self, track):
        if track.uri not in self.trackToPlay:
            track_structure = TrackStructure(track)
            self.trackToPlay[track.uri] = track_structure
            self.core.tracklist.add(at_position=1, uri=track.uri)

    def remove_track(self, track_uri):
        """
        Remove a track from the tracklist. Raise KeyError if not found.
        """
        if track_uri in self.trackToPlay:
            del self.trackToPlay[track_uri]
        else:
            raise KeyError('Track not in tracklist')
