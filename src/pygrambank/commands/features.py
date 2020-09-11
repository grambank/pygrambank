"""

"""
import textwrap

from clldutils.clilib import Table, add_format

from pygrambank.cli_util import add_wiki_repos


def register(parser):
    add_wiki_repos(parser)
    add_format(parser)


def run(args):
    with Table(args, '#', 'ID', 'Title', 'Patron') as t:
        for i, f in enumerate(args.repos.features.values(), start=1):
            t.append([i, f.id, textwrap.shorten(f.wiki['title'], 50), f.wiki['Patron']])