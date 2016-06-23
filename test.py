import os
from urllib import request

import podcastparser
from pydub import AudioSegment
from feedgen.feed import FeedGenerator


def filenameize(fn):
    """better filename characters"""
    try:
        os.mkdir('temp')
    except FileExistsError:
        assert os.path.isdir('temp')
    return os.path.join('temp', fn.replace(':', '').replace('/', ''))


class RemixFeed:
    def __init__(self, location, host):
        self.location = location
        self.host = host
        self.episodes = []
        self.fg = None

    def create_generator(self):
        fg = FeedGenerator()
        fg.load_extension('podcast')

        fg.id('http://lernfunk.de/media/654321')
        fg.title('Some Testfeed')
        fg.author({'name': 'John Doe', 'email': 'john@example.de'})
        fg.link(href='http://example.com', rel='alternate')
        fg.logo('http://ex.com/logo.jpg')
        fg.subtitle('This is a cool feed!')
        fg.link(href='http://larskiesow.de/test.atom', rel='self')
        fg.language('en')
        fg.podcast.itunes_category('Technology', 'Podcasting')
        self.fg = fg

    def add_remix(self, remix):
        self.episodes.append(remix)

    def output(self, location):
        # create all the right files in a folder
        os.mkdir(location)
        self.create_generator()
        for ep in self.episodes:
            audio = ep.output(location)
            encloc = os.path.join(location, ep.name) + '.mp3'
            audio.export(encloc, format='mp3')
            self.add_entry(ep, encloc)
        self.fg.rss_file(os.path.join(location, 'rss.xml'))

    def add_entry(self, remix, encloc):
        fe = self.fg.add_entry()
        fe.id(self.host+encloc)
        fe.title(remix.name)
        fe.description('Released under https://creativecommons.org/licenses/by-nc-sa/2.0/')
        fe.enclosure(self.host+encloc, 0, 'audio/mpeg')


class Remix:
    def __init__(self, name, entries=()):
        self.name = name
        self.entries = list(entries)
        self.feeds = {}
        self.data = {}

    def output(self, location=''):
        self.get_feeds()
        self.get_sources()
        return self.mix()

    def get_feeds(self):
        for feed_url in set(e.feed_url for e in self.entries):
            print('downloading feed', feed_url)
            self.feeds[feed_url] = podcastparser.parse(feed_url, request.urlopen(feed_url))
        print('done getting feeds')

    def get_sources(self):
        source_urls = set(e.source_url(self.feeds[e.feed_url])
                          for e in self.entries)
        for source_url in source_urls:
            name = filenameize(source_url)
            if not os.path.exists(name):
                print('downloading ', source_url, '...')
                with open(name, 'wb') as f:
                    f.write(request.urlopen(source_url).read())
            fmt = os.path.splitext(source_url)[1][1:]
            print('loading ', source_url, '...')
            self.data[source_url] = AudioSegment.from_file(name, fmt)
        print('all required source files loaded')

    def mix(self):
        full = None
        for e in self.entries:
            url = e.source_url(self.feeds[e.feed_url])
            clip = self.data[url][e.start_time*1000:e.end_time*1000]
            if not full:
                full = clip
            else:
                full = full + clip
        print('done creating mix')
        return full


class Segment():
    def __init__(self, feed_url, title, start_time, end_time):
        self.feed_url = podcastparser.normalize_feed_url(feed_url)
        self.title = title
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


FoF = "http://feastoffun.com/feed/"
epname = 'FOF #2348 – Eat, Pray, Gay – 06.23.16'
e1 = Segment(FoF, epname, 3, 10)
e2 = Segment(FoF, epname, 30, 40)

r = Remix('best', [e1, e2])

rf = RemixFeed('greatfeed', 'http://localhost:8000/')

rf.add_remix(r)

rf.output('output')

