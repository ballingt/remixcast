"""
Classes for remixes and components of


"""
import os


class RemixFeed:
    "A collection of remixes and the metadata for a podcast rss feed"
    def __init__(self, title):
        self.title = title
        self.sessions = []

    def add_remix(self, remix):
        self.sessions.append(remix)


class Remix:
    def __init__(self, title):
        self.title = title
        self.clips = []

    def add_clip(self, clip):
        self.clips.append(clip)

    def __str__(self):
        s = 'Remix Session:\n'
        if self.version:
            s += 'remix version '+self.version+'\n\n'

        for section in self.sections:
            s += str(section)
            s += '\n'
        return s


class Query:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Clip:
    def __init__(self, feed_url, query, start_time, end_time):
        self.feed_url = feed_url
        self.query = query
        self.start_time = start_time
        self.end_time = end_time

    def source_url(self, parsed_feed):
        try:
            (ep,) = [ep for ep in parsed_feed['episodes']
                     if ep['title'] == self.title]
        except ValueError:
            print('looking for', repr(self.title))
            print("but couldn't find it among")
            for ep in parsed_feed['episodes']:
                print(repr(ep['title']))
            raise
        return ep['enclosures'][0]['url']


