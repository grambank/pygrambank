import shutil
from pathlib import Path

import pytest


@pytest.fixture
def repos(tmpdir):
    shutil.copytree(str(Path(__file__).parent / 'repos'), str(tmpdir.join('repos')))
    return Path(str(tmpdir.join('repos')))


@pytest.fixture
def api(repos):
    from pygrambank.api import Grambank

    return Grambank(repos)


@pytest.fixture
def wiki(tmpdir):
    shutil.copytree(str(Path(__file__).parent / 'Grambank.wiki'), str(tmpdir.join('Grambank.wiki')))
    return Path(str(tmpdir.join('Grambank.wiki')))
