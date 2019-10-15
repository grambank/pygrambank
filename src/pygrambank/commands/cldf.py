"""
Create a CLDF StructureDataset from the Grambank data.
"""
import pathlib

from cldfcatalog import Catalog

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


def run(args):
    with Catalog(args.glottolog, args.glottolog_version) as glottolog:
        create(args.repos, glottolog.dir, args.wiki_repos, args.cldf_repos)
