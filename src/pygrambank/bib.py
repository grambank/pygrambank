import re

from clldutils.misc import nfilter

AUTHOR_PATTERNS = [
    re.compile(p) for p in [
        r"(?P<lastname>[^,]+),\s((?P<jr>[JS]r\.|[I]+),\s)?(?P<firstname>[^,]+)$",
        r"(?P<firstname>[^{][\S]+(\s[A-Z][\S]+)*)\s"
        r"(?P<lastname>([a-z]+\s)*[A-Z\\\\][\S]+)(?P<jr>,\s[JS]r\.|[I]+)?$",
        r"(?P<firstname>\\{[\S]+\\}[\S]+(\s[A-Z][\S]+)*)\s"
        r"(?P<lastname>([a-z]+\s)*[A-Z\\\\][\S]+)(?P<jr>,\s[JS]r\.|[I]+)?$",
        r"(?P<firstname>[\s\S]+?)\s\{(?P<lastname>[\s\S]+)\}(?P<jr>,\s[JS]r\.|[I]+)?$",
        r"\{(?P<firstname>[\s\S]+)\}\s(?P<lastname>[\s\S]+?)(?P<jr>,\s[JS]r\.|[I]+)?$",
        r"(?P<lastname>[A-Z][\S]+)$",
        r"\{(?P<lastname>[\s\S]+)\}$",
        r"(?P<lastname>[aA]nonymous)$",
        r"(?P<lastname>\?)$",
        r"(?P<lastname>[\s\S]+)$",
    ]
]

PARTIAL_REGEX_PAGES = r"(?:\:\s*(?P<p>[\d\,\s\-]+))?"
PARTIAL_REGEX_YEAR = r"(?:\d\d\d\d|no date|n.d.|[Nn][Dd])"

REGEX_FULL_SOURCE = re.compile(
    r"^(?P<a>[^,]+),[^(\d]+[\s(](?P<y>"
    + PARTIAL_REGEX_YEAR + r")\s*"
    + PARTIAL_REGEX_PAGES + r"\)?")

PARTIAL_REGEX_CAPITALS = r'ÅA-Z\x8e\x8f\x99\x9aÉ'
REGEX_SOURCE = re.compile(
    r"(?P<a>(?<![^\s(])["
    + PARTIAL_REGEX_CAPITALS + r"vd][a-z]*\D*[^\d,.])\.?\s\(?(?P<y>"
    + PARTIAL_REGEX_YEAR + r")"
    + PARTIAL_REGEX_PAGES + r"\)?")

# Gwynn&Krishnamurti1985, p.144
REGEX_ALTERNATIVE_STYLE_SOURCE = re.compile(
    r"^(?P<a>[A-Z][a-zA-Z&]+)(?P<y>[0-9]{4}),\s+p\.\s*(?P<p>[\d,\s\-]+(?:ff?\.)?)$")

REGEX_NAME_PARTS = re.compile(r"\s+|(d\')(?=[A-Z])")
REGEX_CAPITALISED = re.compile(r"\[?[A-Z]")

REGEX_BRACKETED_CODES = re.compile(r"\[([a-z0-9]{4}[0-9]{4}|[a-z]{3}|NOCODE_[A-Z][^\s\]]+)\]")
REGEX_LGCODE_SEPARATOR = re.compile(r"[,/]\s?")
REGEX_ISO_CODE = re.compile(r"[a-z][a-z][a-z]$|NOCODE_[A-Z][^\s\]]+$")

HHTYPE_RANKING_OLD = [
    'grammar',
    'grammar sketch',
    'dictionary',
    '(typological) study of a specific feature',
    'phonology',
    'text',
    'new testament',
    'wordlist',
    'comparative-historical study',
    'some very small amount of data/information on a language',
    'endangered language',
    'sociolinguistically oriented',
    'dialectologically oriented',
    'handbook/overview',
    'ethnographic work',
    'bibliographically oriented',
    'unknown']

HHTYPE_NEW_TYPES = {
    'grammar': 'grammar',
    'grammar sketch': 'grammar_sketch',
    'dictionary': 'dictionary',
    '(typological) study of a specific feature': 'specific_feature',
    'phonology': 'phonology',
    'text': 'text',
    'new testament': 'new_testament',
    'wordlist': 'wordlist',
    'comparative-historical study': 'comparative',
    'some very small amount of data/information on a language': 'minimal',
    'endangered language': 'endangered language',
    'sociolinguistically oriented': 'socling',
    'dialectologically oriented': 'dialectology',
    'handbook/overview': 'overview',
    'ethnographic work': 'ethnographic',
    'bibliographically oriented': 'bibliographical',
    'unknown': 'unknown',
}

HHTYPE_RANKING = [HHTYPE_NEW_TYPES[hhtype] for hhtype in HHTYPE_RANKING_OLD]
HHTYPE_PRIORITIES = {
    hhtype: len(HHTYPE_RANKING) - i
    for i, hhtype in enumerate(HHTYPE_RANKING)}


def get_hhtypes(bibentry):
    hhtype_field = bibentry.get('hhtype', 'unknown')
    hhtype_field = re.sub(r' \([^)]*\)', '', hhtype_field)
    return re.split(r'[;,]\s?', hhtype_field)


def hhtype_priority(hhtype):
    return HHTYPE_PRIORITIES.get(hhtype, 0)


def lowerupper(s):
    parts = [x for x in REGEX_NAME_PARTS.split(s) if x]
    lower, upper = [], []
    for i, x in enumerate(parts):
        if not REGEX_CAPITALISED.match(x):
            lower.append(x)  # pragma: no cover
        else:
            upper = parts[i:]
            break
    return lower, upper


def lastvon(author):
    if 'firstname' not in author:
        return author
    r = {}
    (lower, upper) = lowerupper(author['firstname'])
    r['lastname'] = (' '.join(lower).strip() + ' ' + author['lastname']).strip()
    r['firstname'] = ' '.join(upper)
    if author.get('jr'):
        r['jr'] = author['jr']
    return r


def parse_single_author(n):
    for p in AUTHOR_PATTERNS:
        match = p.match(n)
        if match:
            return lastvon(match.groupdict())
    return None


def parse_authors(author_string):
    author_string = author_string.replace(' & ', ' and ')
    authors = author_string.split(' and ')
    authors = [parse_single_author(a.strip()) for a in authors]
    authors = [a for a in authors if a]
    return authors


def bibkey_authors(bibkey):
    """
    Generator yielding author names as encountered in a citation key.
    """
    # A citation key as used in hh.bib!
    # FIXME that's a bold assumption..
    if ':' in bibkey:
        bibkey = bibkey.split(':')[1]

    current_name = ''
    for char in bibkey:
        # For keys of the form "Meier2018" we stop at the start of year.
        if char.isdigit():
            break
        elif char.isupper() and current_name not in ('Mac', 'De'):
            if current_name:
                yield current_name
            current_name = char
        else:
            current_name += char
    if current_name:
        yield current_name


def lgcodestr(lgcstr):
    lgs = REGEX_BRACKETED_CODES.findall(lgcstr)
    if lgs:
        return lgs

    parts = [p.strip() for p in REGEX_LGCODE_SEPARATOR.split(lgcstr)]
    codes = [p for p in parts if REGEX_ISO_CODE.match(p)]
    return codes


def prioritised_bibkeys(bibkeys, bibliography_entries):
    bibkey_rankings = {}
    for bibkey in bibkeys:
        bibentry = bibliography_entries[bibkey][1]
        hhtypes = get_hhtypes(bibentry)
        hhtype_ranking = max(map(hhtype_priority, hhtypes))
        written_in_english = lgcodestr(bibentry.get('inlg', "")) == ['eng']
        bibkey_rankings[bibkey] = hhtype_ranking, written_in_english
    highest_rank, _ = max(
        (ranking, bibkey)
        for bibkey, ranking in bibkey_rankings.items())
    prioritised_bibkeys = {
        bibkey
        for bibkey, ranking in bibkey_rankings.items()
        if ranking == highest_rank}
    return prioritised_bibkeys


def mismatch_is_fatal(source_string):
    """Filter for source strings."""
    # This code could be combined into one big boolean expression
    # but I somehow doubt that will it any more readable...
    if REGEX_ONLY_PAGES.match(source_string):
        # TODO: Maybe find a way to warn about this
        # print(
        #     'PAGEONLY:',
        #     '[%s] default source:%s' % (glottocode, source_string),
        #     glottocode)
        return False
    elif (
        source_string.find('p.c') != -1
        or source_string.find('personal communication') != -1
        or source_string.find('pers comm') != -1
        or source_string.find('pers. comm') != -1
        or source_string.find('ieldnotes') != -1
        or source_string.find('ield notes') != -1
        or source_string.find('forth') != -1
        or source_string.find('Forth') != -1
        or source_string.find('ubmitted') != -1
        or source_string.find('o appear') != -1
        or source_string.find('in press') != -1
        or source_string.find('in prep') != -1
        or source_string.find('in prog') != -1
        or source_string.startswith('http')
    ):
        return False
    else:
        return True


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
