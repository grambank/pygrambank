import pathlib
import argparse
import collections

import pytest

from pygrambank.__main__ import main
from pygrambank.commands import cldf, new, issues


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


def test_issues(args, capsys):
    args.id = None
    args.format = 'simple'
    issues.run(args)
    out, _ = capsys.readouterr()
    assert 'Comments' in out


def test_issues_detail(args, capsys):
    args.id = '223'
    args.format = 'simple'
    issues.run(args)
    out, _ = capsys.readouterr()
    assert 'Ping @' in out


def test_new(args, tmpdir):
    args.out = str(tmpdir.join('sheet.tsv'))
    new.run(args)
    sheet = pathlib.Path(args.out)
    assert sheet.exists()
    text = sheet.read_text(encoding='utf-8')
    assert all(s in text for s in ['GB021', 'Patron'])


def test_remove_empty(tmpdir):
    content = """a\tb\tc\t\t\t\n\t\t\t\t\t\n1\t2\t3\t\t\t\n"""
    tsv = tmpdir.join('XX_aaaa1234.tsv')
    tsv.write_text(content, encoding="utf8")
    main(['remove_empty', str(tsv)])
    assert tsv.read_text(encoding='utf8') == "a\tb\tc\n1\t2\t3\n"


def test_check(repos, capsys, tmpdir):
    main(['--repos', str(repos), 'check', '--verbose', '--report', str(tmpdir.join('report.tsv'))])
    out, err = capsys.readouterr()
    assert all(word in out for word in ['WARNING', 'ERROR', 'Selecting', 'skipping'])
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


def test_features(repos, capsys, mocker):
    mocker.patch('pygrambank.features.patrons', collections.defaultdict(lambda: 'HJH'))
    main(['--repos', str(repos), 'features'])
    out, err = capsys.readouterr()
    assert 'Patron' in out


def test_cldf2(repos, tmpdir):
    d = pathlib.Path(__file__).parent
    main([
        '--repos', str(repos),
        'cldf',
        '--wiki_repos', str(d / 'Grambank.wiki'),
        '--cldf_repos', str(tmpdir),
        str(d / 'glottolog'),
    ])