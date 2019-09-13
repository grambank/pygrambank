# pygrambank

Curation tools for [Grambank data](https://github.com/glottobank/Grambank).

[![Build Status](https://travis-ci.org/glottobank/pygrambank.svg?branch=master)](https://travis-ci.org/glottobank/pygrambank)
[![codecov](https://codecov.io/gh/glottobank/pygrambank/branch/master/graph/badge.svg)](https://codecov.io/gh/glottobank/pygrambank)
[![PyPI](https://img.shields.io/pypi/v/pygrambank.svg)](https://pypi.org/project/pygrambank)


## Install

`pygrambank` can be installed from PyPI via
```bash
pip install pygrambank
```
or from a clone of [`glottobank/pygrambank`]:
```bash
git clone ...
cd pygrambank
pip install -e .
```

You should install `pygrambank` in a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) to make sure it does not mess with a system-wide Python installation.


## CLI

Installing `pygrambank` will also install a command line program `grambank`. Data curation functionality is implemented as subcommands
of this program. To get information about available subcommands, run
```bash
grambank --help
```

More info on individual subcommands can be obtained running
```bash
grambank help <SUBCOMMAND>
```
e.g.
```bash
$ grambank help check

    grambank --repos PATH/TO/Grambank check
    
    Run data quality checks on a grambank repository.
```


## API

`pygrambank` also allows programmatic access to Grambank data from Python
programs. All functionality is mediated through a `pygrambank.Grambank`
instance:
```python
>>> from pygrambank import Grambank
>>> gb = Grambank('.')
>>> gb.sheets_dir
PosixPath('original_sheets')
>>> for sheet in gb.iter_sheets():
...   print(sheet)
...   break
... 
original_sheets/AH_alag1248.tsv
```
