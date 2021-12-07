import shutil
from pathlib import Path

import pytest


@pytest.fixture
def repos(tmp_path):
    shutil.copytree(Path(__file__).parent / 'repos', tmp_path / 'repos')
    return tmp_path / 'repos'


@pytest.fixture
def api(repos):
    from pygrambank.api import Grambank

    return Grambank(repos)


@pytest.fixture
def wiki(tmp_path):
    shutil.copytree(Path(__file__).parent / 'grambank.wiki', tmp_path / 'grambank.wiki')
    return tmp_path / 'grambank.wiki'
