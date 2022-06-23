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
    # contains empty columns and rows that need to be stripped
    content_a = (
        '\t\ta\t\tb\t\tc\t\t\t\n'
        '\t\t\t\t\t\t\t\t\t\n'
        '\t\t1\t\t2\t\t3\t\t\t\n'
        '\t\t\t\t\t\t\t\t\t\n'
        '\t\t\t\t\t\t\t\t\t\n')
    tsv_a = tmp_path / 'XX_aaaa1234.tsv'
    tsv_a.write_text(content_a, encoding="utf8")

    # contains rows that are too short
    content_b = 'a\tb\tc\n\n1\t2\nx\n'
    tsv_b = tmp_path / 'XX_bbbb1234.tsv'
    tsv_b.write_text(content_b, encoding="utf8")

    # contains missing column label that will raise an error
    content_c = 'a\tb\t\n1\t2\t3\nx\ty\tz\n'
    tsv_c = tmp_path / 'XX_cccc1234.tsv'
    tsv_c.write_text(content_c, encoding="utf8")

    main(['remove_empty', str(tsv_a), str(tsv_b)])
    assert tsv_a.read_text(encoding='utf8') == "a\tb\tc\n1\t2\t3\n"
    assert tsv_b.read_text(encoding='utf8') == 'a\tb\tc\n1\t2\t\nx\t\t\n'
    with pytest.raises(ValueError):
        main(['remove_empty', str(tsv_c)])
    # input file remains unchanged
    assert tsv_c.read_text(encoding='utf8') == 'a\tb\t\n1\t2\t3\nx\ty\tz\n'


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
