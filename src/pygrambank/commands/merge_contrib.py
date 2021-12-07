"""

"""
import re
import pathlib
import collections

from nameparser import HumanName
from bs4 import BeautifulSoup as bs
from clldutils.clilib import PathType
from clldutils.markup import iter_markdown_tables

# flake8: noqa

NAME2ID = {
    'Hoju Cha': 'HC',
    'Roberto E. Herrera Miranda': 'RHE',
    'Yustinus Ghanggo Ate': 'YGA',
    'Farah El Haj Ali': 'FE',
}


def register(parser):
    parser.add_argument(
        '--html',
        type=PathType(type='file'),
        default=pathlib.Path('.') / '..' / '..' / '..' / 'glottobank.github.io' / 'people.html')


def iter_html_data(p):
    doc = bs(p.read_text(encoding='utf8'), features='html5lib')
    for div in doc.find_all('div', class_='gray-box'):
        name = div.find('strong')
        #print(name.get_text())
        #print(div.find('img')['src'] if div.find('img') else '---no photo---')
        #print(div.get_text().strip())
        yield (
            name.get_text().strip(),
            re.sub(r'\s+', ' ', div.get_text().strip()),
            div.find('img')['src'] if div.find('img') else None)


def get_row(contrib, md):
    res = collections.OrderedDict([
        ('id', contrib.id),
        ('Last name', contrib.last_name),
        ('First name', contrib.first_name),
        ('Contribution', contrib.contribution)])
    for k in ['Node', 'Status', 'Language competence', 'GitHub-username', 'email', 'photo', 'bio']:
        res[k] = md.get(k, '') or ''
    if res['photo']:
        res['photo'] = '<img src="https://glottobank.org/{}" width="100">'.format(res['photo'])
    assert not any('|' in v for v in res.values())
    return res


def run(args):
    roles = collections.Counter()
    for c in args.repos.contributors:
        roles.update([c.bio])
    for k, v in roles.most_common():
        print(k, v)
        break
    return

    bios = {r[0]: (r[1], r[2]) for r in iter_html_data(args.html)}

    # id | Last name | First name | Node | Status | Language competence | GitHub-username | email
    header, rows = next(iter_markdown_tables(args.repos.path('CONTRIBUTORS_details.md').read_text(encoding='utf8')))
    rows = [dict(zip(header, row)) for row in rows]
    rows = collections.OrderedDict([(r['id'], r) for r in rows])

    contribs = args.repos.contributors
    contribs = collections.OrderedDict([(r.id, r) for r in contribs])

    assert not set(rows) - set(contribs)
    lnames = {c.last_name: c.id for c in contribs.values()}
    fnames = {'{0.first_name} {0.last_name}'.format(c): c.id for c in contribs.values()}

    bios_by_id = {}
    for name in bios:
        if name in NAME2ID:
            bios_by_id[NAME2ID[name]] = bios[name]
            continue
        hname = HumanName(name)
        if hname.last in lnames:
            bios_by_id[lnames[hname.last]] = bios[name]
            continue
        full = '{0.first} {0.last}'.format(hname)
        if full in fnames:
            bios_by_id[fnames[full]] = bios[name]
            continue
        #print('---', name)

    for i, (cid, c) in enumerate(contribs.items()):
        bio, photo = bios_by_id.get(cid, (None, None))
        if bio:
            assert '\n' not in bio and ('|' not in bio)
        md = rows.get(cid, {})
        md['bio'] = bio
        md['photo'] = photo
        contrib = get_row(c, md)
        if i == 0:
            print(' | '.join(contrib.keys()))
            print(' | '.join([' --- ' for _ in range(len(contrib.keys()))]))
        print(' | '.join(contrib.values()))
