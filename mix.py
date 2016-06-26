import argparse
import os
import sys
import zlib

import requests
import podcastparser
from pydub import AudioSegment

from remix import Remix, Clip, Query
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('remix', metavar='FILE',
                        help='Remix file to mix')
    parser.add_argument('-o', '--output', default='output.mp3', metavar='FILE',
                        help='Outpt file to write remixed audio to')
    args = parser.parse_args()

    if not args.output.endswith('.mp3'):
        args.output = args.output + '.mp3'

    remix = remix_from_string(open(args.remix).read())
    mixed = mix_session(remix)
    mixed.export(args.output, format='mp3')
