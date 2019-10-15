from argparse import Namespace
from pathlib import Path

import pytest
from clldutils.clilib import ParserError

from pygrambank.commands import cldf
from pygrambank.commands import new


@pytest.fixture
def args(api, wiki):
    return Namespace(repos=api, wiki_repos=wiki)


def test_cldf(args, tmpdir):
    with pytest.raises(AttributeError):
        cldf.run(args)

    args.glottolog = str(tmpdir)
    args.wiki_repos = Path('x')
    with pytest.raises(AttributeError):
        cldf.run(args)


def test_new(args, tmpdir):
    args.out = str(tmpdir.join('sheet.tsv'))
    new.run(args)
    sheet = Path(args.out)
    assert sheet.exists()
    assert 'GB021' in sheet.read_text(encoding='utf-8')
