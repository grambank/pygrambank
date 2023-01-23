import re
from termcolor import colored
from itertools import groupby

from clldutils.misc import nfilter, slug

from pygrambank import bib

PARTIAL_REGEX_PAGES = r"(?:\:\s*(?P<p>[\d\,\s\-]+))?"
PARTIAL_REGEX_YEAR = r"(?:\d\d\d\d|no date|n.d.|[Nn][Dd])"

REGEX_FULL_SOURCE = re.compile(r"^(?P<a>[^,]+),[^(\d]+[\s(](?P<y>" + PARTIAL_REGEX_YEAR + r")\s*" + PARTIAL_REGEX_PAGES + r"\)?")

PARTIAL_REGEX_CAPITALS = r'ÅA-Z\x8e\x8f\x99\x9aÉ'
REGEX_SOURCE = re.compile(
    r"(?P<a>(?<![^\s(])[" + PARTIAL_REGEX_CAPITALS + r"vd][a-z]*\D*[^\d,.])\.?\s\(?(?P<y>" +  # noqa: W504
    PARTIAL_REGEX_YEAR + r")" + PARTIAL_REGEX_PAGES + r"\)?")

# Gwynn&Krishnamurti1985, p.144
REGEX_ALTERNATIVE_STYLE_SOURCE = re.compile(
    r"^(?P<a>[A-Z][a-zA-Z&]+)(?P<y>[0-9]{4}),\s+p\.\s*(?P<p>[\d,\s\-]+(?:ff?\.)?)$")


def iter_authoryearpages(source_string):
    for citation_string in source_string.replace("), ", "); ").split(";"):
        if "p.c." in citation_string:
            continue
        condensed = False
        citation_string = citation_string.strip()
        m = REGEX_FULL_SOURCE.search(citation_string)
        if not m:
            m = REGEX_SOURCE.search(citation_string)
        if not m:
            condensed = True
            m = REGEX_ALTERNATIVE_STYLE_SOURCE.search(citation_string)
        if m:
            author, year, pages = m.groups()
            if condensed:
                author = author.replace('&', ' and ')
            wft = author.find("_")
            if wft != - 1:
                word_from_title = author[wft + 1:].lower()
                author = author[:wft]
            else:
                word_from_title = ''
            yield (author, year, pages.strip() if pages else pages, word_from_title)
