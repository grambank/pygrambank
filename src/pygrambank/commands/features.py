"""

"""
import textwrap

from clldutils.clilib import Table, add_format


def register(parser):
    add_format(parser)


def run(args):
    with Table(args, '#', 'ID', 'Title', 'Patron') as t:
        for i, f in enumerate(args.repos.features.values(), start=1):
            t.append([i, f.id, textwrap.shorten(f.name, 50), f.wiki['Patron']])