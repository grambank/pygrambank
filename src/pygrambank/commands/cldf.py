"""
Create a CLDF StructureDataset from the Grambank data.
"""
import pathlib
import argparse

from cldfcatalog import Catalog
from pycldf import Dataset

from pygrambank.cli_util import add_wiki_repos
from pygrambank.cldf import create


def register(parser):
    add_wiki_repos(parser)
    parser.add_argument(
        'glottolog',
        metavar='GLOTTOLOG',
        help="clone of glottolog/glottolog",
        type=pathlib.Path,
    )
    parser.add_argument(
        '--glottolog-version',
        default=None,
        help="tag to checkout glottolog/glottolog to",
    )
    parser.add_argument(
        '--cldf_repos',
        help="clone of glottobank/grambank-cldf",
        default='../grambank-cldf',
        type=pathlib.Path)
    parser.add_argument(
        '--dev',
        default=False,
        action='store_true',
        help=argparse.SUPPRESS)


def run(args):
    if args.glottolog_version:  # pragma: no cover
        with Catalog(args.glottolog, args.glottolog_version) as glottolog:
            create(args.repos, glottolog.dir, args.wiki_repos, args.cldf_repos)
    else:
        create(args.repos, args.glottolog, args.wiki_repos, args.cldf_repos)

    if not args.dev:
        ds = Dataset.from_metadata(args.cldf_repos / 'cldf' / 'StructureDataset-metadata.json')
        ds.validate(log=args.log)
