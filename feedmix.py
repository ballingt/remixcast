import argparse
import os
import shutil
from urllib import parse as urlparse

from feedgen.feed import FeedGenerator

from remix import RemixFeed, Remix, Clip, Query
from fastparser import remix_from_string
from mix import mix_session


TEMP_DIR = 'temp'


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
    fg.link(href=urlparse.urljoin(location, 'rss.xml'), rel='self')

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
