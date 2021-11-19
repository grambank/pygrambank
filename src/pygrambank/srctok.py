import re
from itertools import groupby

from clldutils.misc import nfilter, slug

from pygrambank import bib

REFS = {
    ('Strauß', 'n.d.', 'melp1238'): 's:Strauss:Melpa',
    ('Thurston', '1987', 'kuan1248'): 'hvw:Thurston:NBritain',
    ("Z'Graggen", '1969', 'geda1237'): 'hvld:Zgraggen:Madang',
    ('LeCoeur and LeCoeur', '1956', 'daza1242'): 's:LeCoeurLeCoeur:Teda-Daza',
    ('Lindsey', '2018', 'agob1244'): 'Lindsey2018',
    ('Lee', '2005a', 'mada1285'): 'Lee2005a',
    ('Lee', '2005b', 'mada1285'): 'Lee2005b',
}


def undiacritic(s):
    return slug(s, lowercase=False, remove_whitespace=False)


def amax(d, f=max):
    return f((v, k) for k, v in d.items())


def filterd(f, d):
    r = {}
    for k, v in d.items():
        if f(k):
            r[k] = v
    return r


def allmax(d, f=max):
    if not d:
        return {}
    (v, _) = amax(d, f=f)
    return filterd(lambda k: d[k] == v, d)


repageonly = re.compile(r"[\d+;\s\-etseqpassim.]+$")
pg = r"(?:\:\s*(?P<p>[\d\,\s\-]+))?"
year = r"(?:\d\d\d\d|no date|n.d.|[Nn][Dd])"

refullsrc = re.compile(r"^(?P<a>[^,]+),[^(\d]+[\s(](?P<y>" + year + r")\s*" + pg + r"\)?")

capitals = r'ÅA-Z\x8e\x8f\x99\x9aÉ'
resrc = re.compile(
    r"(?P<a>(?<![^\s(])[" + capitals + r"vd][a-z]*\D*[^\d,.])\.?\s\(?(?P<y>" +  # noqa: W504
    year + r")" + pg + r"\)?")

# Gwynn&Krishnamurti1985, p.144
altrefullsrc = re.compile(
    r"^(?P<a>[A-Z][a-zA-Z&]+)(?P<y>[0-9]{4}),\s+p\.\s*(?P<p>[\d,\s\-]+(?:ff?\.)?)$")


def iter_ayps(s, word_from_title=None):
    for x in s.replace("), ", "); ").split(";"):
        if (x.find("p.c.") != -1) and x.strip().startswith("p.c"):
            continue

        condensed = False
        x = x.strip()
        m = refullsrc.search(x)
        if not m:
            m = resrc.search(x)
        if not m:
            condensed = True
            m = altrefullsrc.search(x)
        if m:
            a, y, p = m.groups()
            if condensed:
                a = a.replace('&', ' and ')
            wft = a.find("_")
            if wft != - 1:
                word_from_title = a[wft + 1:].lower()
                a = a[:wft]
            yield (a, y, p.strip() if p else p, word_from_title)


def priok(ks, e):
    d = {
        k: (max([bib.hhtype_to_n[z] for z in bib.hhtype(e[k][1])]),
            bib.lgcodestr(e[k][1].get('inlg', "")) == ['eng'])
        for k in ks}
    return set(allmax(d).keys())


devon = ["De", "Da", "Van", "Von", "Van den", "Van der", "Von der", "El", "De la", "De", "d'"]
respa = re.compile(r"[\s,.\-]+")


def matchsingleauthor(ca, ba):
    firsttoken = (
        [x for x in respa.split(ca)
         if x.strip() and x[0].isupper() and x not in devon] + [""])[0]
    batokens = respa.split(ba)
    return firsttoken in batokens


resau = re.compile(r"\s*[&/]\s*| and ")


def matchauthor(a, fas, extraauthors):
    a = undiacritic(bib.pauthor(a)[0]['lastname'])
    bas = set([undiacritic(x['lastname']) for x in bib.pauthor(fas)] + extraauthors)
    for ca in resau.split(a):
        if not [ba for ba in bas if matchsingleauthor(ca, ba)]:
            return False
    return True


def iter_key_pages(lg, ayp, e, lgks):
    #
    # FIXME: only yield at most one match!?
    #
    a, y, p, wft = ayp
    if lg in lgks:
        for k in priok([
            k for k in lgks[lg]
            if e[k][1].get("year", "").find(y) != -1
                and (not wft or e[k][1].get("title", "").lower().find(wft) != -1)
                and matchauthor(a, e[k][1].get("author", ""), list(bib.iter_authors(k)))],
            e=e
        ):
            yield k, p


def source_to_refs(src, lgid, e, lgks, unresolved, fixrefs=None):
    fixrefs = fixrefs or REFS
    ays = list(iter_ayps(src))
    refs = sorted(
        set(ref for s in ays for ref in iter_key_pages(lgid, s, e, lgks)),
        key=lambda r: (r[0], r[1] or ''))
    src_comment = None
    if not refs:
        if repageonly.match(src):
            src = "[%s] default source:%s" % (lgid, src)
            print("PAGEONLY:", src, lgid)
        elif not (src.find("p.c") == -1
                  and src.find("personal communication") == -1
                  and src.find("pers comm") == -1
                  and src.find("pers. comm") == -1
                  and src.find("ieldnotes") == -1
                  and src.find("ield notes") == -1
                  and src.find("forth") == -1
                  and src.find("Forth") == -1
                  and src.find("ubmitted") == -1
                  and src.find("o appear") == -1
                  and src.find("in press") == -1
                  and src.find("in prep") == -1
                  and src.find("in prog") == -1
                  and not src.startswith("http")):
            src_comment = src
        else:
            if ays:
                for author, year, pages, word_from_title in ays:
                    if (author, year, lgid) in fixrefs:
                        refs.append((fixrefs[(author, year, lgid)], pages))
                    else:
                        unresolved.update([(author, year, lgid)])
            else:
                unresolved.update([(src, lgid)])
    return [(k, nfilter(r[1] for r in rs)) for k, rs in groupby(refs, lambda r: r[0])], src_comment
