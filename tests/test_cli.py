import pathlib
import argparse

import pytest

from pygrambank.__main__ import main
from pygrambank.commands import cldf
from pygrambank.commands import new


@pytest.fixture
def args(api, wiki):
    return argparse.Namespace(repos=api, wiki_repos=wiki)


def test_recode(tmpdir):
    tmpdir.join('test').write_text('äöü', encoding='macroman')
    main(['recode', '--encoding', 'macroman', str(tmpdir.join('test'))])
    assert pathlib.Path(str(tmpdir)).joinpath('test').read_text(encoding='utf8') == 'äöü'


def test_cldf(args, tmpdir):
    with pytest.raises(AttributeError):
        cldf.run(args)

    args.glottolog = str(tmpdir)
    args.wiki_repos = pathlib.Path('x')
    with pytest.raises(AttributeError):
        cldf.run(args)


def test_new(args, tmpdir):
    args.out = str(tmpdir.join('sheet.tsv'))
    new.run(args)
    sheet = pathlib.Path(args.out)
    assert sheet.exists()
    assert 'GB021' in sheet.read_text(encoding='utf-8')
