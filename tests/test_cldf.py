from pathlib import Path
from pycldf import StructureDataset

from pygrambank import cldf


def test_create(api, wiki, capsys, tmp_path):
    cldf_repos = tmp_path
    cldf.create(
        StructureDataset.in_dir(cldf_repos / 'cldf'),
        api,
        Path(__file__).parent / 'glottolog')
    #captured = capsys.readouterr()
    #assert 'inconsistent' in captured.out
    ds = StructureDataset.from_metadata(cldf_repos / 'cldf' / 'StructureDataset-metadata.json')
    assert len(list(ds['ValueTable'])) == 1
    assert ds['contributors.csv', 'Photo'].valueUrl.expand(list(ds['contributors.csv'])[0]) == \
           'https://glottobank.org/photos/abc'
    #assert len(list(api.sheets_dir.glob('*.tsv'))) == 5
    #assert len(list(ds['LanguageTable'])) == 2
    #assert 'South America' in read_text(cldf_repos / 'cldf' / 'languages.csv')

    # Sources should be grouped by citekey:
    #assert 'author2018[20-30,45]' in read_text(cldf_repos / 'cldf' / 'values.csv')
