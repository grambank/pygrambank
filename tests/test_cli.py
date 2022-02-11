import shutil
import pathlib
import argparse
import collections

import pytest

from pygrambank.__main__ import main
from pygrambank.commands import new, issues


@pytest.fixture
def args(api, wiki):
    return argparse.Namespace(repos=api, wiki_repos=wiki)


def test_recode(tmp_path):
    tmp_path.joinpath('test').write_text('äöü', encoding='macroman')
    main(['recode', '--encoding', 'macroman', str(tmp_path / 'test')])
    assert tmp_path.joinpath('test').read_text(encoding='utf8') == 'äöü'


def test_updatefeatures(api, capsys):
    main(['--repos', str(api.repos),
          'updatefeatures', 'ABBR',
          '--wiki_repos', str(pathlib.Path(__file__).parent / 'grambank.wiki')])


def test_describe(api, capsys, tmp_path):
    main(['--repos', str(api.repos), 'describe', 'ABBR', '--columns'])
    out, _ = capsys.readouterr()
    assert 'abcd1234.tsv' in out
    p = tmp_path / 'ABBR_abcd1234.tsv'
    shutil.copy(str(api.sheets_dir.joinpath('ABBR_abcd1234.tsv')), str(p))
    main(['--repos', str(api.repos), 'describe', str(p), '--columns'])


def test_issues(args, capsys):
    args.id = None
    args.format = 'simple'
    issues.run(args)
    out, _ = capsys.readouterr()
    assert 'Comments' in out


def test_issues_detail(args, capsys):
    args.id = 223
    args.format = 'simple'
    issues.run(args)
    out, _ = capsys.readouterr()
    assert 'Ping @' in out


def test_new(args, tmp_path):
    args.out = sheet = tmp_path / 'sheet.tsv'
    new.run(args)
    assert sheet.exists()
    text = sheet.read_text(encoding='utf-8')
    assert all(s in text for s in ['GB021', 'Patron'])


def test_remove_empty(tmp_path):
    content = """a\tb\tc\t\t\t\n\t\t\t\t\t\n1\t2\t3\t\t\t\n"""
    tsv = tmp_path / 'XX_aaaa1234.tsv'
    tsv.write_text(content, encoding="utf8")
    main(['remove_empty', str(tsv)])
    assert tsv.read_text(encoding='utf8') == "a\tb\tc\n1\t2\t3\n"


def test_check(repos, capsys, tmp_path):
    main(['--repos', str(repos), 'check', '--verbose', '--report', str(tmp_path / 'report.tsv')])
    out, err = capsys.readouterr()
    assert all(word in out for word in ['WARNING', 'ERROR', 'Selecting', 'skipping'])
    main([
        '--repos', str(repos),
        'check',
        '--filename', str(repos / 'original_sheets' / 'ABBR_abcd1234.tsv')])


def test_sourcelookup(repos, capsys):
    main([
        '--repos', str(repos),
        'sourcelookup',
        str(pathlib.Path(__file__).parent / 'glottolog'),
        str(repos / 'original_sheets' / 'ABBR_abcd1234.tsv')])


def test_fix(repos):
    fname = repos / 'original_sheets' / 'ABBR_abcd1234.tsv'
    assert 'Author 2020' in fname.read_text(encoding='utf8')
    main([
        '--repos', str(repos),
        'fix',
        "lambda r: r.update(Source=(r.get('Source') or '').replace('2020', 'xyz')) or r",
        str(fname),
    ])
    text = fname.read_text(encoding='utf8')
    assert ('Author 2020' not in text) and ('Author xyz' in text)


def test_features(repos, capsys, mocker):
    mocker.patch('pygrambank.features.patrons', collections.defaultdict(lambda: 'HJH'))
    main([
        '--repos', str(repos), 'features',
        '--wiki_repos', str(pathlib.Path(__file__).parent / 'grambank.wiki'),
    ])
    out, err = capsys.readouterr()
    assert 'Patron' in out
