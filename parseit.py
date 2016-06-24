"""

session = episode of remixcast
section = contiguous portion of a session using same source
play_stmt = clip

//TODO some renaming

"""
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor


grammar = Grammar(
    r"""
    session       = _ version? _ sections _
    sections      = section (nl section)*
    ws            = (" " / "\t")+
    nl            = ~r"\s*\n\s*"
    _             = ~r"\s*"
    version       = "remix version" ws+ versionnum nl
    section       = source "\n" play_stmt ("\n" play_stmt)*
    source        = episode_query ws+ "of" ws+ feed_url
    episode_query = q_by_title / q_by_number
    q_by_title    = "title" ws* "=" ws+ word
    word          = ~r'("?:[^"\\]|\\.)*" | ^["][^\s]*^["]'
    q_by_number   = "episode" ws+ int
    feed_url      = ~".*"
    play_stmt     = "play" (ws+ duration)?
    duration      = "from" ws+ time ws+ "to" ws+ time
    time          = ~r"(?:\d+:)?\d\d?:\d\d?(?:[.]d+)?" / "beginning" / "end"
    float         = ~r"(\d?[.]\d+)|\d+"
    int           = ~r"\d+"
    versionnum    = ~r"\d+(?:[.]\d+)*"
    """)


class RemixVisitor(NodeVisitor):
    def visit_session(self, session, children):
        _, version, _, sections, _ = children
        remix = RemixSession()
        if version:
            remix.version = version[0]
        for section in sections:
            remix.add_section(section)
        return remix

    def visit_sections(self, ast, children):
        (sec, ugh) = children
        sections = [sec] + [x[1] for x in ugh]
        return sections

    def visit_section(self, section, children):
        print('visit_section got:', children)
        source, _, play_stmt, ugh = children
        play_stmts = [play_stmt] + [x[1] for x in ugh]
        print(play_stmts)
        s = Section(source)
        return s

    def visit_version(self, version, children):
        print('version:', children)
        return children[2]

    def visit_versionnum(self, ast, _):
        return ast.text

    def generic_visit(self, node, visited_children):
        return visited_children



example = """
remix version 0.1

episode 17 of http://mypodcast.com/feed.rss
play from 0:10 to 0:15
episode 12 of "http://mypodcast.com/feed.rss"
play
episode 12 of "http://mypodcast.com/feed.rss"
play
"""

#import pudb; pudb.set_trace()
ast = grammar.parse(example)

print(ast)
v = RemixVisitor()

print(v.visit(ast))

