"""

session = episode of remixcast
section = contiguous portion of a session using same source
play_stmt = clip

//TODO some renaming

"""
import sys

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from remix import Remix, Query, Clip, parse_time

grammar = Grammar(
    r"""
    session       = _* version? _* sections _*
    sections      = section (nl section)*
    ws            = (" " / "\t")
    nl            = ws* comment? "\n" _*
    _             = ~r"\s+" / comment
    comment       = "#" ~r".*"
    version       = "remix version" ws+ versionnum nl
    section       = source nl play_stmt (nl play_stmt)*
    source        = episode_query ws+ "of" ws+ word
    episode_query = q_by_title / q_by_number
    q_by_title    = "title" ws* "=" ws* word
    word          = quoted / unquoted
    quoted        = ~'["][^"]*["]'
    unquoted      = ~r'[^\s]+'
    q_by_number   = "episode" ws+ int
    play_stmt     = "play" (ws+ duration)?
    duration      = "from" ws+ time ws+ "to" ws+ time
    time          = ~r"(?:\d+:)?\d\d?:\d\d?(?:[.]\d+)?" / "beginning" / "end"
    float         = ~r"(\d?[.]\d+)|\d+"
    int           = ~r"\d+"
    versionnum    = ~r"\d+(?:[.]\d+)*"
    """)


class RemixVisitor(NodeVisitor):
    def visit_session(self, session, children):
        _, version, _, clips, _ = children
        remix = Remix('TODO add title to grammar')
        if version:
            remix.version = version[0]
        for clip in clips:
            remix.add_clip(clip)
        return remix

    def visit_nl(self, ast, _):
        return _

    def visit_sections(self, ast, children):
        (clips, ugh) = children
        sections = clips + [clip for x in ugh for clip in x[1]]
        return sections

    def visit_section(self, section, children):
        (feed_url, query), _, play_stmt, ugh = children

        play_stmts = [play_stmt] + [x[1] for x in ugh]
        clips = [Clip(feed_url, query, p[0], p[1])
                 for p in play_stmts]
        return clips

    def visit_source(self, ast, children):
        (query,), _, _, _, feed_url = children
        return (feed_url, query)

    def visit_q_by_number(self, ast, children):
        _, _, number = children
        return Query('episode', number)

    def visit_q_by_title(self, ast, children):
        _, _, _, _, title = children
        return Query('title', title)

    def visit_feed_url(self, ast, _):
        return ast.text

    def visit_int(self, ast, _):
        return int(ast.text)

    def visit_word(self, ast, _):
        if ast.text.startswith('"') and ast.text.endswith('"'):
            return ast.text[1:-1]
        return ast.text

    def visit_play_stmt(self, ast, children):
        _, rest = children
        if rest:
            ((_, (start_time, end_time)),) = rest
            return (start_time, end_time)
        return ("beginning", "end")

    def visit_duration(self, ast, children):
        _, _, t1, _, _, _, t2 = children
        return [t1, t2]

    def visit_time(self, ast, children):
        parse_time(ast.text)
        return ast.text

    def visit_version(self, version, children):
        _, _, versionnum, _ = children
        return versionnum

    def visit_versionnum(self, ast, _):
        return ast.text

    def generic_visit(self, node, visited_children):
        return visited_children


def remix_from_string(s):
    ast = grammar.parse(s)
    v = RemixVisitor()
    return v.visit(ast)


def example():
    example = """
    remix version 0.1

    episode 17 of "http://mypodcast.com/feed.rss"
    play from 0:10 to 0:15
    episode 12 of "http://mypodcast.com/feed.rss"
    play
    episode 12 of http://mypodcast.com/feed.rss
    play
    """

    ast = grammar.parse(example)
    print(ast)
    v = RemixVisitor()
    print(v.visit(ast))


if __name__ == '__main__':
    args = sys.argv[1:]
    ast = grammar.parse(open(args[0]).read())
    v = RemixVisitor()
    print(v.visit(ast))
