"""
Classes for remixes and components of


"""
import os
import re


class RemixFeed:
    "A collection of remixes and the metadata for a podcast rss feed"
    def __init__(self, title):
        self.title = title
        self.sessions = []

    def add_remix(self, remix):
        self.sessions.append(remix)


def indent(s, n=2):
    return '\n'.join([' '*n+line for line in s.split('\n')])


class Remix:
    def __init__(self, title):
        self.title = title
        self.clips = []

    def add_clip(self, clip):
        self.clips.append(clip)

    def __str__(self):
        s = ''
        if self.version:
            s += 'remix version '+self.version+'\n\n'

        for clip in self.clips:
            s += str(clip)
            s += '\n'
        return 'Remix Session:\n' + indent(s)


class Query:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        if self.key == 'episode':
            return 'episode {}'.format(self.value)
        return '{}="{}"'.format(self.key, self.value)


def parse_time(t):
    """

    >>> parse_time('0:20.1')
    20100
    """
    if t in ('beginning', 'end'):
        return None
    pattern = re.compile(r"""
            ^
            (?:
                (?P<hours>\d+)
                :)?
            (?P<minutes>\d\d?)
            :
            (?P<seconds>\d\d?)
            (?:
                [.]
                (?P<decimal>\d\d?\d?))?
            $
            """, re.VERBOSE)
    parts = pattern.search(t).groupdict('0')
    hours_part = 3600 * int(parts['hours'])
    mins_part = 60 * int(parts['minutes'])
    secs_part = int(parts['seconds'])
    ms_part = int(parts['decimal'].ljust(3, '0'))
    return hours_part*1000 + mins_part*1000 + secs_part*1000 + ms_part


class Clip:
    def __init__(self, feed_url, query, start_time, end_time):
        self.feed_url = feed_url
        self.query = query
        self.start_time = start_time
        self.end_time = end_time

    @property
    def start_time_ms(self):
        """Time seconds, "beginning" and "end" become None"""
        return parse_time(self.start_time)

    @property
    def end_time_ms(self):
        """Time seconds, "beginning" and "end" become None"""
        return parse_time(self.end_time)

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

    def __str__(self):
        s = '{} of {}\nfrom {} to {}'.format(
                self.query,
                self.feed_url,
                self.start_time,
                self.end_time)
        return s

if __name__ == '__main__':
    import doctest
    doctest.testmod()
