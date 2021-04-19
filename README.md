# pygrambank

Curation tools for [Grambank data](https://github.com/glottobank/Grambank).

[![Build Status](https://github.com/grambank/pygrambank/workflows/tests/badge.svg)](https://github.com/grambank/pygrambank/actions?query=workflow%3Atests)
[![PyPI](https://img.shields.io/pypi/v/pygrambank.svg)](https://pypi.org/project/pygrambank)


## Install

`pygrambank` can be installed from PyPI via
```bash
pip install pygrambank
```
or from a clone of [`grambank/pygrambank`]:
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
grambank <SUBCOMMAND> -h
```
e.g.
```shell
$ grambank describe -h
usage: grambank describe [-h] [--columns] SHEET

Describe a (set of) sheets.

This includes checking for correctness - i.e. the functionality of `grambank check`.
While references will be parsed, the corresponding sources will **not** be looked up
in Glottolog (since this is slow). Thus, for a final check of a sheet, you must run
`grambank sourcelookup`.

positional arguments:
  SHEET       Path of a specific TSV file to check or substring of a filename
              (e.g. a glottocode)

optional arguments:
  -h, --help  show this help message and exit
  --columns   List columns of the sheet (default: False)
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

