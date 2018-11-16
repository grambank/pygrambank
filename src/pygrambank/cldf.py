from __future__ import print_function, unicode_literals
import time
from itertools import groupby
from collections import Counter, OrderedDict, defaultdict

from tqdm import tqdm
import pyglottolog
from clldutils.path import read_text, write_text, git_describe, Path
from clldutils.misc import lazyproperty
from clldutils.markup import Table
from pycldf import StructureDataset
from pycldf.sources import Source

from pygrambank import bib
from pygrambank import srctok
from pygrambank.sheet import Sheet
from pygrambank.api import Grambank


def itertable(lines):
    """
    Read a markdown table. Yields one OrderedDict per row.
    """
    header = None
    for i, line in enumerate(lines):
        assert line.strip().startswith('|') and line.strip().endswith('|')
        row = [c.strip() for c in line.split('|')][1:-1]
        if i == 0:
            header = row
        elif i == 1:
            assert set(line).issubset({'|', ':', '-', ' '})
        else:
            yield OrderedDict(zip(header, row))


def bibdata(sheet, e, lgks, unresolved):
    def clean_key(key):
        return key.replace(':', '_').replace("'", "")

    for row in sheet.rows:
        if row['Source']:
            refs, sources = [], []
            for key, pages in srctok.source_to_refs(row["Source"], sheet.glottocode, e, lgks, unresolved):
                typ, fields = e[key]
                ref = key = clean_key(key)
                if pages:
                    ref += '[{0}]'.format(','.join(pages))
                refs.append(ref)
                sources.append(Source(typ, key, **fields))

            row['Source'] = refs
            for src in sources:
                yield src


def iterunique(insheets):
    """
    For languages which have been coded multiple times, we pick out the best sheet.
    """
    for gc, sheets in groupby(sorted(insheets, key=lambda s: (s.glottocode, s.path.stem)), lambda s: s.glottocode):
        sheets = list(sheets)
        if len(sheets) == 1:
            yield sheets[0]
        else:
            print('\nSelecting best sheet for {0}'.format(gc))
            for i, sheet in enumerate(sorted(sheets, key=lambda s: len(s.rows), reverse=True)):
                print('{0} dps: {1} sheet {2}'.format(
                    len(sheet.rows), 'chosing' if i == 0 else 'skipping', sheet.path.stem))
                if i == 0:
                    yield sheet


def sheets_to_gb(api, glottolog, wiki, cldf_repos):
    for suffix in Sheet.valid_suffixes:
        for f in tqdm(sorted(api.sheets_dir.glob('*' + suffix)), desc=suffix):
            sheet = Sheet(f, glottolog, api.features)
            sheet.write_tsv()

    print('reading sheets from TSV')
    sheets = [Sheet(f, glottolog, api.features) for f in sorted(
        api.sheets_dir.glob('*.tsv'), key=lambda p: p.stem)]

    print('loading bibs')
    bibs = glottolog.bib('hh')
    bibs.update(api.bib)

    lgks = defaultdict(set)
    for key, (typ, fields) in bibs.items():
        if 'lgcode' in fields:
            for code in bib.lgcodestr(fields['lgcode']):
                if code in glottolog.languoids_by_ids:
                    lgks[glottolog.languoids_by_ids[code].id].add(key)

    # Chose best sheet for indivdual Glottocodes:
    sheets = list(iterunique(sheets))

    # Lookup sources for each sheet:
    dataset = StructureDataset.in_dir(cldf_repos / 'cldf')

    def describe_repos(r, org='glottobank'):
        return OrderedDict([
            ('dc:title', '{0}/{1}'.format(org, r.name)),
            ('dc:description', git_describe(r))])

    dataset.tablegroup.common_props['prov:wasDerivedFrom'] = [
        describe_repos(api.repos),
        describe_repos(glottolog.api.repos),
        describe_repos(wiki)
    ]
    dataset.tablegroup.common_props['prov:wasGeneratedBy'] = describe_repos(
        Path(__file__).parent.parent.parent)

    dataset.add_component('LanguageTable', 'contributed_datapoints', 'provenance', 'Family_name', 'Family_id')
    dataset.add_component('ParameterTable', 'patron', 'name_in_french', 'Grambank_ID_desc', 'bound_morphology')
    dataset.add_component('CodeTable')
    dataset['ValueTable', 'Value'].null = ['?']
    data = defaultdict(list)

    for fid, feature in sorted(api.features.items()):
        data['ParameterTable'].append(dict(
            ID=fid,
            Name=feature.name,
            Description=feature.description,
            patron=feature.patron,
            name_in_french=feature.name_french,
            Grambank_ID_desc=feature['Grambank_ID_desc'],
            bound_morphology=feature['bound_morphology']
        ))
        for code, desc in sorted(feature.domain.items(), key=lambda i: int(i[0])):
            data['CodeTable'].append(dict(
                ID='{0}-{1}'.format(fid, code),
                Parameter_ID=fid,
                Name=code,
                Description=desc,
            ))

    unresolved, coded_sheets = Counter(), {}
    for sheet in sheets:
        if not sheet.rows:
            print('ERROR: empty sheet {0}'.format(sheet.path))
            continue
        coded_sheets[sheet.glottocode] = sheet
        data['LanguageTable'].append(dict(
            ID=sheet.glottocode,
            Name=sheet.lgname,
            Glottocode=sheet.glottocode,
            contributed_datapoints=sheet.coder,
            provenance="{0} {1}".format(sheet.path.name, time.ctime(sheet.path.stat().st_mtime)),
            Family_name=sheet.family_name,
            Family_id=sheet.family_id,
            Latitude=sheet.latitude,
            Longitude=sheet.longitude,
            Macroarea=sheet.macroarea))
        dataset.add_sources(*list(bibdata(sheet, bibs, lgks, unresolved)))
        for row in sheet.rows:
            data['ValueTable'].append(dict(
                ID='{0}-{1}'.format(row['Feature_ID'], row['Language_ID']),
                Language_ID=sheet.glottocode,
                Parameter_ID=row['Feature_ID'],
                Code_ID='{0}-{1}'.format(row['Feature_ID'], row['Value']) if row['Value'] != '?' else None,
                Value=row['Value'],
                Comment=row['Comment'],
                Source=row['Source']
            ))

    dataset.write(**data)

    for k, v in reversed(unresolved.most_common()):
        print(k, v)

    return coded_sheets


def update_wiki(coded_sheets, glottolog, wiki):
    def todo_table(rows):
        print('formatting todo')
        table = Table('Language', 'iso-639-3', 'Reserved By', 'Comment')
        for row in rows:
            row = list(row.values())
            for code in row[1].split('/'):
                glang = glottolog.languoids_by_ids.get(code.strip())
                if glang and glang.id in coded_sheets:
                    print('NOWDONE: {0}'.format(row))
                    break
            else:
                table.append(row)

        def sortkey(row):
            prio = 0
            if 'SCCS' in row[-1]:
                prio += 2
            if 'One-per-family' in row[-1]:
                prio += 1
            return -prio, row[0]

        return '\n' + table.render(sortkey=sortkey) + '\n'

    def done_table(rows):
        print('formatting done')
        table = Table('Language', 'iso-639-3', 'Done By')
        for sheet in sorted(coded_sheets.values(), key=lambda s: s.lgname):
            table.append([sheet.lgname, '{0} / {1}'.format(sheet.glottocode, sheet.lgid), sheet.coder])
        return '\n' + table.render() + '\n'

    doc = wiki / 'Languages-to-code.md'
    newmd, todo, done, in_todo, in_done = [], [], [], False, False
    for line in read_text(doc, encoding='utf-8-sig').splitlines():
        if line.strip() == '##':
            continue

        if in_todo or in_done:
            if line.strip().startswith('## '):  # Next section!
                if in_done:
                    func, lines = done_table, done  # pragma: no cover
                else:  # if in_todo
                    func, lines = todo_table, todo

                newmd.append(func(list(itertable(lines))))
                newmd.append(line)
                in_todo = False
                in_done = False
            else:
                if line.strip():
                    # Aggregate table lines.
                    (done if in_done else todo).append(line)
        else:
            newmd.append(line)

        if line.strip().startswith('## Priority'):
            print('aggregating todo')
            in_todo = True

        if line.strip().startswith('## Finished'):
            print('aggregating done')
            in_done = True

    if in_done and done:
        newmd.append(done_table(done))

    write_text(doc, '\n'.join(newmd))


class Glottolog(object):
    """
    A custom facade to the Glottolog API.
    """
    def __init__(self, repos):
        self.api = pyglottolog.Glottolog(repos)

    def bib(self, key):
        """
        Retrieve entries of a Glottolog BibTeX file.

        :param key: filename stem of the BibTeX file, e.g. "hh" for "hh.bib"
        :return: dict mapping citation keys to (type, fields) pairs.
        """
        return {
            e.key: (e.type, e.fields)
            for e in self.api.bibfiles['{0}.bib'.format(key)].iterentries()}

    @lazyproperty
    def languoids(self):
        return list(self.api.languoids())

    @lazyproperty
    def languoids_by_glottocode(self):
        return {l.id: l for l in self.languoids}

    @lazyproperty
    def languoids_by_ids(self):
        """
        We provide a simple lookup for the three types of identifiers for a Glottolog languoid,
        where hid takes precedence over ISO 639-3 code.
        """
        res = {}
        for l in self.languoids:
            res[l.id] = l
            if l.iso:
                res[l.iso] = l
        for l in self.languoids:
            if l.hid:
                res[l.hid] = l
        return res


def create(repos, glottolog_repos, wiki, cldf_repos):
    grambank = Grambank(repos, wiki)
    glottolog = Glottolog(glottolog_repos)
    coded_sheets = sheets_to_gb(
        grambank,
        glottolog,
        wiki,
        cldf_repos)
    update_wiki(coded_sheets, glottolog, wiki)
