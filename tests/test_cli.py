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


def test_describe(api, capsys):
    main(['--repos', str(api.repos), 'describe', 'ABBR', '--columns'])
    out, _ = capsys.readouterr()
    assert 'abcd1234.tsv' in out


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


def test_remove_empty(tmpdir):
    content = """a\tb\tc\t\t\t\n1\t2\t3\t\t\t\n"""
    tsv = tmpdir.join('XX_aaaa1234.tsv')
    tsv.write_text(content, encoding="utf8")
    main(['remove_empty', str(tsv)])
    assert tsv.read_text(encoding='utf8') == "a\tb\tc\n1\t2\t3\n"


def test_check(repos, capsys, tmpdir):
    main(['--repos', str(repos), 'check', '--report', str(tmpdir.join('report.tsv'))])
    out, err = capsys.readouterr()
    assert all(word in out for word in ['WARNING', 'ERROR'])
    main([
        '--repos', str(repos),
        'check',
        '--filename', str(repos / 'original_sheets' / 'ABBR_abcd1234.tsv')])


def test_fix(repos):
    fname = repos / 'original_sheets' / 'ABBR_abcd1234.tsv'
    assert 'book2018' in fname.read_text(encoding='utf8')
    main([
        '--repos', str(repos),
        'fix',
        "lambda r: r.update(Source=(r.get('Source') or '').replace('2018', 'xyz')) or r",
        str(fname),
    ])
    text = fname.read_text(encoding='utf8')
    assert ('book2018' not in text) and ('bookxyz' in text)


def test_cldf2(repos, tmpdir):
    d = pathlib.Path(__file__).parent
    main([
        '--repos', str(repos),
        'cldf',
        '--wiki_repos', str(d / 'Grambank.wiki'),
        '--cldf_repos', str(tmpdir),
        str(d / 'glottolog'),
    ])