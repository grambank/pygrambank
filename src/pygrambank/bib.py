from __future__ import print_function
import re


def takeuntil(s, q, plus = 0):
    i = s.find(q)
    if i >= 0:
        return s[:i+plus]
    return s


def takeafter(s, q):
    i = s.find(q)
    if i >= 0:
        return s[i+len(q):]
    return s


reauthor = {}
reauthor[0] = re.compile("(?P<lastname>[^,]+),\s((?P<jr>[JS]r\.|[I]+),\s)?(?P<firstname>[^,]+)$")
reauthor[1] = re.compile("(?P<firstname>[^{][\S]+(\s[A-Z][\S]+)*)\s(?P<lastname>([a-z]+\s)*[A-Z\\\\][\S]+)(?P<jr>,\s[JS]r\.|[I]+)?$")
reauthor[2] = re.compile("(?P<firstname>\\{[\S]+\\}[\S]+(\s[A-Z][\S]+)*)\s(?P<lastname>([a-z]+\s)*[A-Z\\\\][\S]+)(?P<jr>,\s[JS]r\.|[I]+)?$")
reauthor[3] = re.compile("(?P<firstname>[\s\S]+?)\s\{(?P<lastname>[\s\S]+)\}(?P<jr>,\s[JS]r\.|[I]+)?$")
reauthor[4] = re.compile("\{(?P<firstname>[\s\S]+)\}\s(?P<lastname>[\s\S]+?)(?P<jr>,\s[JS]r\.|[I]+)?$")
reauthor[5] = re.compile("(?P<lastname>[A-Z][\S]+)$")
reauthor[6] = re.compile("\{(?P<lastname>[\s\S]+)\}$")
reauthor[7] = re.compile("(?P<lastname>[aA]nonymous)$")
reauthor[8] = re.compile("(?P<lastname>\?)$")
reauthor[9] = re.compile("(?P<lastname>[\s\S]+)$")


def psingleauthor(n, vonlastname = True):
    for i in sorted(reauthor.keys()):
        o = reauthor[i].match(n)
        if o:
            if vonlastname:
                return lastvon(o.groupdict())
            return o.groupdict()
    print("Couldn't parse name:", n)
    return None

anonymous = ['Anonymous', 'No Author Stated', 'An\'onimo', 'Peace Corps'] 

rebrackauthor = re.compile("([\s\S]+) \{([\s\S]+)\}$")

def pauthor(s):
    pas = [psingleauthor(a.strip()) for a in s.replace(" & ", " and ").split(' and ') if a.strip()]
    if [a for a in pas if not a]:
        print(s)
    return [a for a in pas if a]


reca = re.compile("\s*[,\&]\s*")

relu = re.compile("\s+|(d\')(?=[A-Z])")
recapstart = re.compile("\[?[A-Z]")
def lowerupper(s):
    parts = [x for x in relu.split(s) if x]
    lower = []
    upper = []
    for (i, x) in enumerate(parts):
        if not recapstart.match(x):
            lower.append(x)
        else:
            upper = parts[i:]
            break
    return (lower, upper)


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


def authoryear(k):
    typ, fields = k
    r = ""
    if 'author' in fields:
        authors = [x['lastname'] for x in pauthor(fields['author'])]
        r = ', '.join(authors[:-1]) + ' and ' + authors[-1]
    elif 'editor' in fields:
        authors = [x['lastname'] for x in pauthor(fields['editor'])]
        r = ', '.join(authors[:-1]) + ' and ' + authors[-1] + " (ed.)"
    if r.startswith(" and "):
        r = r[5:]
    return r + " " + fields.get('year', 'no date')

rebracketyear = re.compile("\[([\d\,\-\/]+)\]")
reyl = re.compile("[\,\-\/\s\[\]]+")

refields = re.compile('\s*(?P<field>[a-zA-Z\_\d]+)\s*=\s*[{"](?P<data>.*)[}"],\n')
refieldsnum = re.compile('\s*(?P<field>[a-zA-Z\_\d]+)\s*=\s*(?P<data>\d+),\n')
refieldsacronym = re.compile('\s*(?P<field>[a-zA-Z\_\d]+)\s*=\s*(?P<data>[A-Za-z]+),\n')
refieldslast = re.compile('\s*(?P<field>[a-zA-Z\_\d]+)\s*=\s*[\{\"]?(?P<data>[^\n]+?)[\}\"]?(?<!\,)[$\n]')
retypekey = re.compile("@(?P<type>[a-zA-Z]+){(?P<key>[^,\s]*)[,\n]")
reitem = re.compile("@[a-zA-Z]+{[^@]+}")

trf = '@Book{g:Fourie:Mbalanhu,\n  author =   {David J. Fourie},\n  title =    {Mbalanhu},\n  publisher =    LINCOM,\n  series =       LWM,\n  volume =       03,\n  year = 1993\n}'

reka = re.compile("([A-Z]+[a-z]*)|(?<![a-z])(de|di|da|du|van|von)")


def key_to_authors(k):
    n = takeuntil(takeafter(k, ":"), ":")
    js = [i for i in range(len(n)) if n[i].isupper()] + [len(n)]
    auths = []
    i = 0
    for j in js:
        auths = auths + [n[i:j]]
        i = j
    return [auth for auth in auths if auth.strip()]
    

reabbs = re.compile('@[Ss]tring\{(?P<abb>[A-Za-z]+)\s*\=\s*[\{\"](?P<full>[^\\n]+)[\}\"]\}\\n')

reabbrep1 = re.compile("\s*\=\s*([A-Za-z]+)\,\n")
reabbrep2 = re.compile("\s*\=\s*([A-Za-z]+)\s*\#\s*\{")
reabbrep3 = re.compile("\}\s*\#\s*([A-Za-z]+)\s*\#\s*\{")
reabbrep4 = re.compile("\}\s*\#\s*([A-Za-z]+)\,\n")

resplittit = re.compile("[\(\)\[\]\:\,\.\s\-\?\!\;\/\~\=]+")
resplittittok = re.compile("([\(\)\[\]\:\,\.\s\-\?\!\;\/\~\=\'" + '\"' + "])")

def addcitekey(p):
    t, f = p
    f["key"] = authoryear((t, f))
    return (t, f)


rerpgs = re.compile("([xivmcl]+)\-?([xivmcl]*)")
repgs = re.compile("([\d]+)\-?([\d]*)")

rewrdtok = re.compile("[a-zA-Z].+")
reokkey = re.compile("[^a-z\d\-\_\[\]]")

renamelgcode = re.compile("(?P<name>[^\[]+)\s+\[(?P<iso>[a-z][a-z][a-z]|NOCODE\_[A-Z][^\s\]]+)\]")
hooks = ["=", "probably", "possibly", "looks like", "geographically", "count", "counts"]
rehooksplit = re.compile("|".join(["\s%s\s" % hook for hook in hooks]))

repginter = re.compile("([Pp][Pp]\.?\~?\s?[\d\s\-\,]+)")

reisobrack = re.compile("\[([a-z][a-z][a-z]|NOCODE\_[A-Z][^\s\]]+)\]")
recomma = re.compile("[\,\/]\s?")
reiso = re.compile("[a-z][a-z][a-z]$|NOCODE\_[A-Z][^\s\]]+$")


def lgcodestr(lgcstr):
    lgs = reisobrack.findall(lgcstr)
    if lgs:
        return lgs
    
    parts = [p.strip() for p in recomma.split(lgcstr)]
    codes = [p for p in parts if reiso.match(p)]
    return codes


def hhtype(f):
    rekillparen = re.compile(" \([^\)]*\)")
    respcomsemic = re.compile("[;,]\s?")
    return respcomsemic.split(rekillparen.sub("", f.get("hhtype", "unknown")))


oldwcrank = ['grammar', 'grammar sketch', 'dictionary', '(typological) study of a specific feature', 'phonology', 'text', 'new testament', 'wordlist', 'comparative-historical study', 'some very small amount of data/information on a language', 'endangered language', 'sociolinguistically oriented', 'dialectologically oriented', 'handbook/overview', 'ethnographic work', 'bibliographically oriented', 'unknown']

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
hhtype_to_n = dict([(x, len(wcrank)-i) for (i, x) in enumerate(wcrank)])
