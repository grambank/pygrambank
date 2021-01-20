"""

"""
import textwrap
import collections

from clldutils.clilib import Table, add_format
from termcolor import colored


def register(parser):
    add_format(parser, 'simple')
    parser.add_argument('--id', help='Issue ID', type=int, default=None)


def run(args):
    issues = collections.OrderedDict([(i.id, i) for i in args.repos.issues])

    if args.id:
        issue = issues[args.id]
        print(colored('{0.created} {0.user}'.format(issue), 'green'))
        print(colored(issue.title, attrs={'bold', 'underline'}))
        print('')
        print(issue.body)
        for comment in issue.comments:
            print(colored('\n    {0.created} {0.user}'.format(comment), 'green'))
            for line in comment.stripped_body.split('\n'):
                print('    ' + line)
        return

    with Table(args, 'ID', 'Title', 'User', 'Comments') as t:
        for issue in issues.values():
            if issue.coding_problem:
                t.append([
                    issue.id,
                    textwrap.shorten(issue.title, 50, placeholder=' […]'),
                    issue.user,
                    len(issue.comments)])
