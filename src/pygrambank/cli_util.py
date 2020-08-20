import pathlib


def add_wiki_repos(parser):
    parser.add_argument(
        '--wiki_repos',
        help="clone of grambank/grambank.wiki",
        default=pathlib.Path('../grambank.wiki'),
        type=pathlib.Path)
