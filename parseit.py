"""

session = episode of remixcast
section = contiguous portion of a session using same source
play_stmt = clip

//TODO some renaming

"""
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from remix import Remix, Query, Clip

grammar = Grammar(
    r"""
    session       = _ version? _ sections _
    sections      = section (nl section)*
    ws            = (" " / "\t")+
    nl            = ~r"\s*\n\s*"
    _             = ~r"\s*"
    version       = "remix version" ws+ versionnum nl
    section       = source "\n" play_stmt ("\n" play_stmt)*
    source        = episode_query ws+ "of" ws+ word
    episode_query = q_by_title / q_by_number
    q_by_title    = "title" ws* "=" ws* word
    word          = quoted / unquoted
    quoted        = ~'["].*["]'
    unquoted      = ~r'[^\s]+'
    q_by_number   = "episode" ws+ int
    play_stmt     = "play" (ws+ duration)?
    duration      = "from" ws+ time ws+ "to" ws+ time
    time          = ~r"(?:\d+:)?\d\d?:\d\d?(?:[.]d+)?" / "beginning" / "end"
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

    def visit_feed_url(self, ast, _):
        return ast.text

    def visit_int(self, ast, _):
        return int(ast.text)

    def visit_word(self, ast, _):
        print("word match:", ast.text)
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
        return ast.text

    def visit_version(self, version, children):
        _, _, versionnum, _ = children
        return versionnum

    def visit_versionnum(self, ast, _):
        return ast.text

    def generic_visit(self, node, visited_children):
        return visited_children



example = """
remix version 0.1

episode 17 of "http://mypodcast.com/feed.rss"
play from 0:10 to 0:15
episode 12 of "http://mypodcast.com/feed.rss"
play
episode 12 of http://mypodcast.com/feed.rss
play
"""

#import pudb; pudb.set_trace()
ast = grammar.parse(example)
#print(ast)

v = RemixVisitor()

print(v.visit(ast))

