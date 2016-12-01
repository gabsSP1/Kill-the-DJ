import itertools
from heapq import heappush, heappop


class Track(object):
    def __init__(self, track_uri):
        self.track_uri = track_uri
        self.votes = 0

    def increment_votes(self, ):
        self.votes += 1

    def set_votes(self, votes):
        self.votes = votes

    def get_votes(self):
        return self.votes

    def __lt__(self,other): 
        if not isinstance(other, Track):
            raise TypeError("Not comparable")
        return self.votes > other.votes

    def __str__(self): 
        return str("Track(%s,%s)" % (self.track_uri, self.votes))


class Tracklist(object):
    """
    Tracklist works as following:
    Track with the most votes goes first. After that the track with one vote less.
    If the next track has the same number of votes, the track where the newest vote is the oldest overall wins.
    """
    def __init__(self, core):
        self.core = core
        self.tracklist = []
        self.entry_finder = {}
        self.counter = itertools.count()

    def update_tracklist(self):
        """
        Update mopidy's core tracklist
        :param tracklist:
        :return:
        """
        self.core.tracklist.clear()
        # We copy the tracklist to avoid modifying it
        tl_copy = list(self.tracklist)
        self.core.tracklist.add(uris=[heappop(tl_copy).track_uri for _ in range(len(tl_copy))])

    def add_song(self, track_uri):
        """
        Add a new song or update the vote count of an existing song
        """
        if track_uri in self.entry_finder:
            self.remove_track(track_uri)
        count = next(self.counter)

        track = Track(track_uri)
        entry = [track, count]
        self.entry_finder[track_uri] = entry
        heappush(self.playlist, entry)

    def remove_track(self, track_uri):
        """
        Remove a track from the tracklist. Raise KeyError if not found.
        """
        if track_uri in self.entry_finder:
            entry = self.entry_finder.pop(track_uri)
            entry[0] = None
        else:
            raise KeyError('Track not in tracklist')

    def set_track_votes(self, track_uri, votes=0):
        """
        Set the vote count for a track in the tracklist
        """
        if track_uri in self.entry_finder:
            entry = self.entry_finder[track_uri]
            entry[0].set_votes(votes)
        else:
            raise KeyError('Track not in tracklist')

    def get_track_votes(self, track_uri):
        """
        Get the vote count for a track in the tracklist
        """
        if track_uri in self.entry_finder:
            entry = self.entry_finder[track_uri]
            entry[0].get_votes()
        else:
            raise KeyError('Track not in tracklist')