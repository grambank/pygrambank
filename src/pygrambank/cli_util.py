import pathlib


def add_wiki_repos(parser):
    parser.add_argument(
        '--wiki_repos',
        help="clone of glottobank/Grambank.wiki",
        default=pathlib.Path('../Grambank.wiki'),
        type=pathlib.Path)
