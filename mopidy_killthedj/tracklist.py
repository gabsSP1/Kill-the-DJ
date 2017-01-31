import itertools
from heapq import heapify, heappush, heappop


class Track(object):
    def __init__(self, track_uri):
        self.track_uri = track_uri
        self.votes = 0

    def get_votes(self):
        return self.votes

    def __lt__(self, other):
        if not isinstance(other, Track):
            raise TypeError("Object of type %s not comparable with Track" % (type(other)))
        return self.votes > other.votes

    def __repr__(self):
        return str('{"uri": "%(uri)s", "votes": %(votes)s}' % {"uri": self.track_uri, "votes": self.votes})


class Tracklist(object):
    """
    Tracklist works as following:
    Track with the most votes goes first. After that the track with one vote less.
    """
    def __init__(self, core):
        self.core = core
        self.tracklist = []
        self.entry_finder = {}
        self.counter = itertools.count()

    def update_tracklist(self):
        """
        Update mopidy's core tracklist
        :return: None
        """
        self.core.tracklist.clear()
        # We copy the tracklist to avoid modifying it
        tl_copy = list(self.tracklist)
        self.core.tracklist.add(uris=[heappop(tl_copy)[0].track_uri
                                      for _ in range(len(tl_copy))])

    def add_track(self, track_uri):
        """
        Add a new song or update the vote count of an existing song
        """
        if track_uri in self.entry_finder:
            self.remove_track(track_uri)
        count = next(self.counter)

        track = Track(track_uri)
        entry = [track, count]
        self.entry_finder[track_uri] = entry
        heappush(self.tracklist, entry)
        self.core.tracklist.add(uri=track_uri)

    def remove_track(self, track_uri):
        """
        Remove a track from the tracklist. Raise KeyError if not found.
        """
        if track_uri in self.entry_finder:
            entry = self.entry_finder.pop(track_uri)
            self.tracklist.remove(entry)
            self.core.tracklist.remove({'uri': [track_uri]})
        else:
            raise KeyError('Track not in tracklist')

    def set_track_votes(self, track_uri, votes=0):
        """
        Set the vote count for a track in the tracklist
        """
        if votes < 0:
            raise ValueError("vote count can not be negative.")

        if track_uri in self.entry_finder:
            entry = self.entry_finder[track_uri]
            entry[0].set_votes(votes)
            heapify(self.tracklist)
        else:
            raise KeyError('Track not in tracklist.')

    def decrement_track_votes(self, track_uri):
        """
        Decrement the vote count for a track in the tracklist
        """
        if track_uri in self.entry_finder:
            entry = self.entry_finder[track_uri]
            if entry[0].votes > 1:
                entry[0].votes -= 1
                heapify(self.tracklist)
            else:
                raise Exception("vote count for track can not be negative")
        else:
            raise KeyError('Track not in tracklist.')

    def increment_track_votes(self, track_uri):
        """
        Increment the vote count for a track in the tracklist
        """
        if track_uri in self.entry_finder:
            entry = self.entry_finder[track_uri]
            entry[0].votes += 1
            heapify(self.tracklist)
        else:
            raise KeyError('Track not in tracklist.')

    def get_track_votes(self, track_uri):
        """
        Get the vote count for a track in the tracklist
        """
        if track_uri in self.entry_finder:
            entry = self.entry_finder[track_uri]
            return entry[0].get_votes()
        else:
            raise KeyError('Track not in tracklist')