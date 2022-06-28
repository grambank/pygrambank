import shutil
import pathlib
import argparse
import collections

import pytest

from pygrambank.__main__ import main
from pygrambank.commands import new, issues, check_encoding, recode


@pytest.fixture
def args(api, wiki):
    return argparse.Namespace(repos=api, wiki_repos=wiki)


def test_recode_single_encoding():
    good_text = 'tèst'.encode('cp1252')
    bad_text = 'tèst'.encode('macroman')
    assert recode.decode_line(good_text, 'cp1252') == 'tèst'
    assert recode.decode_line(bad_text, 'cp1252') is None


def test_recode_mixed_encoding():
    good_text = b' -- '.join(['tèst'.encode('utf-8'), 'tèst'.encode('cp1252')])
    bad_text = b' -- '.join(['tèst'.encode('utf-8'), 'tèst'.encode('macroman')])
    assert recode.decode_line(good_text, 'mixed-cp1252') == 'tèst -- tèst'
    assert recode.decode_line(bad_text, 'mixed-cp1252') is None


def test_recode(tmp_path):
    good_single_enc = str(tmp_path / 'good_single_enc.txt')
    bad_single_enc = str(tmp_path / 'bad_single_enc.txt')
    good_mixed_enc = str(tmp_path / 'good_mixed_enc.txt')
    bad_mixed_enc = str(tmp_path / 'bad_mixed_enc.txt')

    with open(good_single_enc, 'wb') as f:
        f.write('tèst'.encode('cp1252'))
    with open(bad_single_enc, 'wb') as f:
        f.write('tèst'.encode('macroman'))
    with open(good_mixed_enc, 'wb') as f:
        f.write('tèst '.encode('cp1252'))
        f.write('tèst'.encode('utf-8'))
    with open(bad_mixed_enc, 'wb') as f:
        f.write('tèst '.encode('macroman'))
        f.write('tèst'.encode('utf-8'))

    main(['recode', '--encoding', 'cp1252', good_single_enc, bad_single_enc])
    main(['recode', '--encoding', 'mixed-cp1252', good_mixed_enc, bad_mixed_enc])

    with open(good_single_enc, 'rb') as f:
        assert f.read() == 'tèst\n'.encode('utf-8')
    with open(bad_single_enc, 'rb') as f:
        # file is unchanged
        assert f.read() == 'tèst'.encode('macroman')
    with open(good_mixed_enc, 'rb') as f:
        assert f.read() == 'tèst tèst\n'.encode('utf-8')
    with open(bad_mixed_enc, 'rb') as f:
        # file is unchanged
        assert f.read() == b' '.join([
            'tèst'.encode('macroman'),
            'tèst'.encode('utf-8')])


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


def test_check_encoding_for_repl_chars():
    line = "�We don't want those dreaded ��� characters anywhere in our stuff!�"
    matches = list(check_encoding.find_replacement_chars(line))
    assert matches[0] == "�We don't want those "
    assert matches[1] == ' want those dreaded ��� characters anywhere'
    assert matches[2] == 'ywhere in our stuff!�'


def test_check_encoding_for_non_ascii():
    line = b"w\xe9 don't want non-utf-8 e\xf1\xe7\xf6ding anywhere in our st\xfcff"
    matches = list(check_encoding.find_non_ascii(line))
    assert matches[0] == b"w\xe9 don't want non-utf-"
    assert matches[1] == b"n't want non-utf-8 e\xf1\xe7\xf6ding anywhere in our"
    assert matches[2] == b'g anywhere in our st\xfcff'


def test_check_encoding_suggestions():
    line = b'wr\xf6ng enc\xf6ding'
    suggestions = check_encoding.suggest_encodings(line)
    assert suggestions['cp1252'] == 'wröng encöding'
    assert suggestions['macroman'] == 'wrˆng encˆding'


def test_check_encoding(tmp_path):
    good_utf8 = str(tmp_path / 'good_utf8.txt')
    corrupted_utf8 = str(tmp_path / 'corrupted-utf8.txt')
    not_utf8 = str(tmp_path / 'not-utf8.txt')
    mixed_encodings = str(tmp_path / 'mixed-encodings.txt')

    with open(good_utf8, 'wb') as f:
        f.write('Zum Gruße!\n'.encode('utf-8'))
    with open(corrupted_utf8, 'wb') as f:
        f.write('Zum Gu�e!\n'.encode('utf-8'))
    with open(not_utf8, 'wb') as f:
        f.write('Zum Gruße!\n'.encode('cp1252'))
    with open(mixed_encodings, 'wb') as f:
        f.write('Zum Gruße!\n'.encode('utf-8'))
        f.write('Zum Gruße!\n'.encode('cp1252'))

    main(['check_encoding', good_utf8, corrupted_utf8, not_utf8, mixed_encodings])
