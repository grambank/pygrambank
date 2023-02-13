"""
Recode a file, i.e. change its encoding to UTF-8.
"""
from clldutils.clilib import PathType
import sys


def register(parser):
    parser.add_argument('path', nargs='+', type=PathType(type='file'))
    parser.add_argument(
        '--encoding',
        default='cp1252',
        choices=['cp1252', 'macroman', 'mixed-cp1252', 'mixed-macroman'],
    )


def _split_into_nonascii(raw_line):
    start = 0
    found_non_ascii = False
    for index, byte in enumerate(raw_line):
        # non-ascii
        if byte >= 0x80:
            found_non_ascii = True
        elif found_non_ascii:
            yield raw_line[start:index]
            found_non_ascii = False
            start = index
    if index > start:
        yield raw_line[start:]


def split_into_nonascii(raw_line):
    return list(_split_into_nonascii(raw_line))


def _decode_substring(raw_substring, enc):
    try:
        return raw_substring.decode('utf-8')
    except:  # noqa: E722
        try:
            return raw_substring.decode(enc)
        except:   # noqa: E722
            return None


def decode_mixed(raw_line, enc):
    substrings = split_into_nonascii(raw_line)
    unicode_strings = [_decode_substring(s, enc) for s in substrings]
    if None in unicode_strings:
        return None
    else:
        return ''.join(unicode_strings)


def decode_line(raw_line, enc):
    if enc.startswith('mixed-'):
        return decode_mixed(raw_line, enc[6:])
    else:
        try:
            return raw_line.decode(enc)
        except:  # noqa: E722
            return None


def run(args):
    for p in args.path:
        with open(p, 'rb') as f:
            raw_lines = [line.rstrip(b'\r\n') for line in f]

        unicode_lines = [decode_line(line, args.encoding) for line in raw_lines]
        found_invalid = False
        for index, (line, raw_line) in enumerate(zip(unicode_lines, raw_lines)):
            if line is None:
                found_invalid = True
                print(
                    '{}:{}: Could not decode line:'.format(p, index + 1),
                    repr(raw_line),
                    file=sys.stderr)

        if not found_invalid:
            with open(p, 'w', encoding='utf-8') as f:
                print('\n'.join(unicode_lines), file=f)
