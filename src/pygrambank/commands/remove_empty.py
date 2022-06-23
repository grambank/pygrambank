"""
Removes empty columns and rows from a tsv file.
"""
from csvw import dsv
from clldutils.clilib import PathType
from pygrambank.sheet import Sheet
from itertools import chain, islice, repeat


def real_row_width(row):
    """Return width of a table row ignoring any empty cells at the end."""
    last_index = None
    for index, cell in enumerate(row):
        if cell.strip():
            last_index = index
    if last_index is None:
        return 0
    else:
        return last_index + 1


def real_table_height(table):
    """Return height of a table ignoring any empty rows at the end."""
    last_index = None
    for index, row in enumerate(table):
        if any(c.strip() for c in row):
            last_index = index
    if last_index is None:  # pragma: nocover
        return 0
    else:
        return last_index + 1


def padded_row(row, width):
    """Ensure size of a table row.

    If `row` is longer than `width`, truncate it.
    If `row` is shorter than `width`, pad it with empty strings.
    """
    return list(chain(
        islice(row, width),
        repeat('', max(0, width - len(row)))))


def register(parser):
    parser.add_argument('path', nargs='+', type=PathType(type='file'))


def run(args):
    for p in args.path:
        # use reader rather than iterrows so we operate on raw file rather than a
        # grambank-ifyed version.
        rows = list(Sheet(p)._reader())
        if not rows:  # pragma: nocover
            continue

        width = max(map(real_row_width, rows))
        height = real_table_height(rows)
        rows = [padded_row(row, width) for row in islice(rows, height)]

        cols_with_values = [
            x
            for x in range(width)
            if any(row[x] for row in rows)]
        unlabelled_cols = [
            x
            for x in range(width)
            if not rows[0][x] and x in cols_with_values]
        if unlabelled_cols:
            raise ValueError(
                '{}: Columns {} unlabelled. Fix manually.'.format(
                    p, ', '.join(map(str, unlabelled_cols))))

        new_rows = [
            [row[i] for i in range(width) if i in cols_with_values]
            for row in rows]
        new_rows = [row for row in new_rows if any(row)]

        with dsv.UnicodeWriter(p, delimiter='\t', encoding='utf8') as w:
            w.writerows(new_rows)
