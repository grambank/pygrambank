from __future__ import print_function
import re
from itertools import groupby

from clldutils.misc import nfilter

from pygrambank import bib


def amax(d, f=max):
    return f((v, k) for (k, v) in d.items())


def filterd(f, d):
    r = {}
    for (k,v) in d.items():
        if f(k):
            r[k] = v
    return r


def allmax(d, f=max):
    if not d:
        return {}
    (v, _) = amax(d, f=f)
    return filterd(lambda k: d[k] == v, d)


repageonly = re.compile("[\d+\;\s\-etseqpassim\.]+$")
pg = "(?:\:\s*(?P<p>[\d\,\s\-]+))?"
year = "(?:\d\d\d\d|no date|n.d.|[Nn][Dd])"
refullsrc = re.compile("^(?P<a>[^,]+)\,[^\(\d]+[\s\(](?P<y>)\s*" + pg + "\)?")
resrc = re.compile("(?P<a>(?<![^\s\(])[A-Zvd][a-z]*\D*[^\d\,\.])\.?\s\(?(?P<y>" + year + ")" + pg + "\)?")


def iter_ayps(s):
    for x in s.replace("), ", "); ").split(";"):
        if (x.find("p.c.") != -1) and x.strip().startswith("pc"):
            continue

        m = refullsrc.search(x)
        if not m:
            m = resrc.search(x)
        if m:
            a, y, p = m.groups()
            yield (a, y, p.strip() if p else p)


def priok(ks, e):
    d = {
        k: (max([bib.hhtype_to_n[z] for z in bib.hhtype(e[k][1])]),
            bib.lgcodestr(e[k][1].get('inlg', "")) == ['eng'])
        for k in ks}
    return set(allmax(d).keys())


devon = ["De", "Da", "Van", "Von", "Van den", "Van der", "Von der"]
respa = re.compile("[\s\,\,\.\-]+")
def matchsingleauthor(ca, ba):
    firsttoken = ([x for x in respa.split(ca) if x.strip() and x[0].isupper() and x not in devon] + [""])[0]
    batokens = respa.split(ba)
    return firsttoken in batokens


resau = re.compile("\s*[\&\/]\s*| and ")
def matchauthor(a, fas, extraauthors = []):
    a = bib.pauthor(a)[0]['lastname'] #undiacritic already done
    bas = set([x['lastname'] for x in bib.pauthor(fas)] + extraauthors)
    for ca in resau.split(a):
        if not [ba for ba in bas if matchsingleauthor(ca, ba)]:
            return False
    return True


def iter_key_pages(lg, ayp, e, lgks):
    a, y, p = ayp
    if lg in lgks:
        for k in priok([
            k for k in lgks[lg]
            if e[k][1].get("year", "").find(y) != -1
                and matchauthor(a, e[k][1].get("author", ""), bib.key_to_authors(k))],
            e=e
        ):
            yield k, p


def source_to_refs(src, lgid, e, lgks, unresolved):
    ays = list(iter_ayps(src))
    refs = sorted(
        set(ref for s in ays for ref in iter_key_pages(lgid, s, e, lgks)),
        key=lambda r: (r[0], r[1] or ''))
    if not refs:
        if repageonly.match(src):
            src = "[%s] default source:%s" % (lgid, src)
            print("PAGEONLY:", src, lgid)
        elif not (src.find("p.c") == -1
                  and src.find("personal communication") == -1
                  and src.find("ieldnotes") == -1
                  and src.find("forth") == -1
                  and src.find("Forth") == -1
                  and src.find("ubmitted") == -1
                  and src.find("o appear") == -1
                  and src.find("in press") == -1
                  and src.find("in prog.") == -1
                  and not src.startswith("http")):
            pass
        else:
            if ays:
                unresolved.update([(ay[0], ay[1], lgid) for ay in ays])
            else:
                unresolved.update([(src, lgid)])
    return [(k, nfilter(r[1] for r in rs)) for k, rs in groupby(refs, lambda r: r[0])]
