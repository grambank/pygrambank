import shutil
from pathlib import Path

import pytest


@pytest.fixture
def api(tmpdir):
    from pygrambank.api import Grambank

    shutil.copytree(str(Path(__file__).parent / 'repos'), str(tmpdir.join('repos')))
    return Grambank(str(tmpdir.join('repos')))


@pytest.fixture
def wiki(tmpdir):
    shutil.copytree(str(Path(__file__).parent / 'Grambank.wiki'), str(tmpdir.join('Grambank.wiki')))
    return Path(str(tmpdir.join('Grambank.wiki')))
