import argparse
import os
import shutil
import sys
from urllib import parse as urlparse
import zlib

import requests
import podcastparser
from pydub import AudioSegment
from feedgen.feed import FeedGenerator

from remix import RemixFeed, Remix, Clip, Query
from fastparser import remix_from_string


TEMP_DIR = 'temp'


def downloaded_name(path):
    """better filename characters"""
    _, ext = os.path.splitext(path)
    try:
        os.mkdir(TEMP_DIR)
    except FileExistsError:
        assert os.path.isdir(TEMP_DIR)
    return os.path.join(TEMP_DIR, str(zlib.adler32(path.encode('utf8'))) + ext)


def downloaded(url):
    name = downloaded_name(url)
    if not os.path.exists(name):
        print('downloading ', url, '...')
        with open(name, 'wb') as f:
            response = requests.get(url, stream=True)
            try:
                total_length = int(response.headers.get('content-length'))
            except TypeError:
                f.write(response.content)
            else:
                dl = 0
                last_done = -1
                for data in response.iter_content(4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    if done != last_done:
                        last_done = done
                        sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)))
                        sys.stdout.flush()
    return name


def load_feed(path):
    print('loading ', path, '...')
    return podcastparser.parse(path, downloaded(path))


def load_audio(path):
    fmt = os.path.splitext(path)[1][1:]
    print('loading ', path, '...')
    return AudioSegment.from_file(downloaded(path), fmt)


def create_mixed_feed(remix_feed, location, output_dir):
    """Create an rss feed for mixed sessions.

    location is the hostname and folder, like 'http://abc.com/remix/
    output_dir is the folder to write mixed sessions to
    """

    fg = FeedGenerator()
    fg.load_extension('podcast')

    fg.id(location)
    fg.title(remix_feed.title)
    fg.subtitle('this is only a remix')
    fg.link(href=urlparse.urljoin(location, 'feed.rss'), rel='self')

    if os.path.exists(output_dir):
        print('output directory exists, overwriting...')
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    for remix in remix_feed.sessions:
        fe = fg.add_entry()

        mixed = mix_session(remix)
        mixed.export(os.path.join(output_dir, remix.title), format='mp3')

        fe.id(urlparse.urljoin(location, urlparse.quote(remix.title)))
        fe.title(remix.title)
        fe.description('A remix of other things')
        fe.enclosure(urlparse.urljoin(location, urlparse.quote(remix.title)), 0, 'audio/mpeg')

    fg.rss_file(os.path.join(output_dir, 'rss.xml'), pretty=True)


def get_session_feeds(session):
    return {feed_url: load_feed(feed_url)
            for feed_url in {c.feed_url for c in session.clips}}


def run_query(query, feed):
    if query.key == 'title':
        (ep,) = [ep for ep in feed['episodes']
                 if ep['title'] == query.value]
        return ep
    raise ValueError("Other query methods not yet implemnted")


def find_source_url(feed, query):
    ep = run_query(query, feed)
    return ep['enclosures'][0]['url']


def get_session_sources(session, feeds):
    source_urls = set(find_source_url(feeds[clip.feed_url], clip.query)
                      for clip in session.clips)
    data = {source_url: load_audio(source_url)
            for source_url in source_urls}
    print('all required source files loaded')
    return data


def mix_session(session):
    feeds = get_session_feeds(session)
    audio = get_session_sources(session, feeds)

    full = None
    for clip in session.clips:
        url = find_source_url(feeds[clip.feed_url], clip.query)
        clip = audio[url][clip.start_time_s*1000:clip.end_time_s*1000]
        if not full:
            full = clip
        else:
            full = full + clip
    print('done creating mix')
    return full


def example():
    FoF = "http://feastoffun.com/feed/"
    q = Query('title', 'FOF #2348 – Eat, Pray, Gay – 06.23.16')
    c1 = Clip(FoF, q, 3, 10)
    c2 = Clip(FoF, q, 30, 40)

    r = Remix('best')
    r.add_clip(c1)
    r.add_clip(c2)

    rf = RemixFeed('greatfeed')

    rf.add_remix(r)
    create_mixed_feed(rf, 'http://localhost:8000/', 'output')


def serve_folder(path, port=8000, bind='localhost'):
    os.chdir(path)
    import http.server
    handler_class = http.server.SimpleHTTPRequestHandler
    http.server.test(HandlerClass=handler_class, port=port, bind=bind)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', '-b', default='localhost', metavar='ADDRESS',
                        help='Specify alternate bind address '
                             '[default: all interfaces]')
    parser.add_argument('port', action='store',
                        default=8000, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8000]')
    parser.add_argument('remixes', nargs='+', metavar='FILE',
                        help='Remix files to serve in feed')
    args = parser.parse_args()

    rf = RemixFeed('testfeed')
    for filename in args.remixes:
        remix = remix_from_string(open(filename).read())
        rf.add_remix(remix)

    location = 'http://{}:{}'.format(args.bind, args.port)
    create_mixed_feed(rf, location, 'output')

    print(urlparse.urljoin(location, 'rss.xml'))
    serve_folder('output', port=args.port, bind=args.bind)
