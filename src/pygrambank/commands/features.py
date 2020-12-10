"""
List active features.
"""
import textwrap

from clldutils.clilib import Table, add_format

from pygrambank.cli_util import add_wiki_repos


def register(parser):
    add_wiki_repos(parser)
    add_format(parser)


def run(args):
    contribs = {c.id: c.name for c in args.repos.contributors}
    with Table(args, '#', 'ID', 'Title', 'Patrons') as t:
        for i, f in enumerate(args.repos.features.values(), start=1):
            t.append([
                i,
                f.id,
                textwrap.shorten(f.wiki['title'], 50),
                ' '.join([contribs[abbr] for abbr in f.patrons])])
