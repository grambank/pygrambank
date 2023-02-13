"""
Check for non-UTF-8 encoding.

Also checks for Unicode Replacement Characters, because those tend to be a sign
that data corruption might have happened.
"""

import sys

from clldutils.clilib import PathType


REPLACEMENT_CHAR = chr(0xfffd)
SUGGESTED_ENCS = ['cp1252', 'macroman']


def register(parser):
    parser.add_argument('path', nargs='+', type=PathType(type='file'))


def _find_consecutive(pred, iterable):
    current_start = None
    for index, elem in enumerate(iterable):
        if pred(elem):
            if current_start is None:
                current_start = index
        else:
            if current_start is not None:
                yield current_start, index
                current_start = None
    if current_start:
        yield current_start, index
        current_start = None


def context(line, start, end, context_len):
    """Return substring from `start` to `end` (excl.) plus `context_len`
    characters on each side.

    Also works with raw `bytes`.
    """
    return line[max(0, start - context_len):min(len(line), end + context_len)]


def find_replacement_chars(line):
    """Find instances of Unicode Replacement Characters in `line`."""
    for start, end in _find_consecutive(lambda c: c == REPLACEMENT_CHAR, line):
        yield context(line, start, end, 20)


def find_non_ascii(raw_line):
    """Find characters outside of the ASCII range."""
    for start, end in _find_consecutive(lambda b: b >= 0x80, raw_line):
        yield context(raw_line, start, end, 20)


def suggest_encodings(raw_line):
    """Try out a few character encodings and see what the result looks like.

    Returns dictionary (encoding -> result).
    """
    suggestions = {}
    for enc in SUGGESTED_ENCS:
        try:
            suggestions[enc] = raw_line.decode(enc)
        except UnicodeError:  # pragma: nocover
            suggestions[enc] = '<could not decode from {}>'.format(enc)
    return suggestions


def run(args):
    for p in args.path:
        with open(p, 'rb') as f:
            raw_lines = list(f)

        utf8_detected = False
        nonutf8_detected = False

        for index, raw_line in enumerate(raw_lines):
            raw_line = raw_line.rstrip(b'\r\n')
            lineno = index + 1
            try:
                unicode_line = raw_line.decode('utf-8')
                # check for non-ascii characters
                if any(b >= 0x80 for b in raw_line):
                    utf8_detected = True
                for msg in find_replacement_chars(unicode_line):
                    print(
                        '{}:{}: Unicode replacement character found: {}'.format(
                            p, lineno, msg),
                        file=sys.stderr)
            except UnicodeDecodeError:
                nonutf8_detected = True
                for match in find_non_ascii(raw_line):
                    print('{}:{}: Non-UTF8 character found: {}'.format(
                        p, lineno, repr(match)))
                    for enc, res in sorted(suggest_encodings(match).items()):
                        print(" * {}:\t'{}'".format(enc, res.rstrip('\r\n')))

        if utf8_detected and nonutf8_detected:
            print(
                '{}: Mixed encoding detected! Tread with caution!'.format(p),
                file=sys.stderr)
