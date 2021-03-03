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


def psingleauthor(n):
    for p in AUTHOR_PATTERNS:
        match = p.match(n)
        if match:
            return lastvon(match.groupdict())
    return None


def pauthor(s):
    return nfilter(psingleauthor(a.strip()) for a in s.replace(" & ", " and ").split(' and '))


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


def iter_authors(key):
    """
    Generator yielding author names as encountered in a citation key.
    """
    if ':' in key:  # A citation key as used in hh.bib!
        n = key.split(':')[1]
    else:
        n = key
    acc = ''
    for i, c in enumerate(n):
        if c.isdigit():  # For citation keys of the form "Meier2018" we stop at the start of year.
            break
        if c.isupper() and acc not in ['Mac', 'De']:
            if acc:
                yield acc
            acc = c
        else:
            acc += c
    if acc:
        yield acc


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


def hhtype(f):
    rekillparen = re.compile(r" \([^)]*\)")
    respcomsemic = re.compile(r"[;,]\s?")
    return respcomsemic.split(rekillparen.sub("", f.get("hhtype", "unknown")))


oldwcrank = [
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

newwcs = {}
newwcs['handbook/overview'] = 'overview'
newwcs['some very small amount of data/information on a language'] = 'minimal'
newwcs['grammar sketch'] = 'grammar_sketch'
newwcs['new testament'] = 'new_testament'
newwcs['(typological) study of a specific feature'] = 'specific_feature'
newwcs['dialectologically oriented'] = 'dialectology'
newwcs['sociolinguistically oriented'] = 'socling'
newwcs['comparative-historical study'] = 'comparative'
newwcs['bibliographically oriented'] = 'bibliographical'
newwcs['ethnographic work'] = 'ethnographic'
newwcs['dictionary'] = 'dictionary'
newwcs['grammar'] = 'grammar'
newwcs['text'] = 'text'
newwcs['wordlist'] = 'wordlist'
newwcs['phonology'] = 'phonology'
newwcs['endangered language'] = 'endangered language'
newwcs['unknown'] = 'unknown'

wcrank = [newwcs[k] for k in oldwcrank]
hhtype_to_n = {x: len(wcrank) - i for i, x in enumerate(wcrank)}
