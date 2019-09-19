from pathlib import Path

import pytest
from clldutils.clilib import ParserError

from pygrambank.__main__ import cldf, propagate_gb20


@pytest.fixture
def args(mocker, api, wiki):
    return mocker.Mock(repos=api.repos, wiki_repos=wiki)


def test_cldf(args, tmpdir):
    args.args = ['x', 'x']
    with pytest.raises(ParserError):
        cldf(args)

    args.args = [str(tmpdir), 'x']
    args.wiki_repos = Path('x')
    with pytest.raises(ParserError):
        cldf(args)


def test_propagate_gb20(args):
    propagate_gb20(args)
