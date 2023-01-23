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


reca = re.compile(r"\s*[,&]\s*")

relu = re.compile(r"\s+|(d\')(?=[A-Z])")
recapstart = re.compile(r"\[?[A-Z]")


def lowerupper(s):
    parts = [x for x in relu.split(s) if x]
    lower, upper = [], []
    for i, x in enumerate(parts):
        if not recapstart.match(x):
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


reisobrack = re.compile(r"\[([a-z0-9]{4}[0-9]{4}|[a-z]{3}|NOCODE_[A-Z][^\s\]]+)\]")
recomma = re.compile(r"[,/]\s?")
reiso = re.compile(r"[a-z][a-z][a-z]$|NOCODE_[A-Z][^\s\]]+$")


def lgcodestr(lgcstr):
    lgs = reisobrack.findall(lgcstr)
    if lgs:
        return lgs

    parts = [p.strip() for p in recomma.split(lgcstr)]
    codes = [p for p in parts if reiso.match(p)]
    return codes


def hhtypes(bibentry):
    hhtype_field = bibentry.get('hhtype', 'unknown')
    hhtype_field = re.sub(r' \([^)]*\)', '', hhtype_field)
    return re.split(r'[;,]\s?', hhtype_field)


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


def hhtype_priority(hhtype):
    return HHTYPE_PRIORITIES.get(hhtype, 0)
