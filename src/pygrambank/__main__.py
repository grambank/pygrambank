import sys
from pathlib import Path

from clldutils.clilib import ParserError, register_subcommands, get_parser_and_subparsers
from clldutils.loglib import Logging

from pygrambank.api import Grambank


def propagate_gb20(args):  # pragma: no cover
    """
    grambank --repos=PATH/TO/Grambank --wiki_repos=PATH/TO/Grambank.wiki  propagate_gb20

    Propagate changes in gb20.txt to all derived files (in Grambank repos and wiki).
    """
    api = Grambank(args.repos)
    api.gb20.listallwiki(args.wiki_repos)


def main(args=None, catch_all=False, parsed_args=None):
    import pygrambank.commands

    parser, subparsers = get_parser_and_subparsers('grambank')
    parser.add_argument(
        '--repos', help="clone of glottobank/Grambank", default=Path('.'), type=Path)
    register_subcommands(subparsers, pygrambank.commands)

    args = parsed_args or parser.parse_args(args=args)
    if not hasattr(args, "main"):  # pragma: no cover
        parser.print_help()
        return 1

    args.repos = Grambank(args.repos, wiki=getattr(args, 'wiki_repos', None))
    with Logging(args.log, level=args.log_level):
        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except ParserError as e:  # pragma: no cover
            print(e)
            return main([args._command, '-h'])
        except Exception as e:  # pragma: no cover
            if catch_all:
                print(e)
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
