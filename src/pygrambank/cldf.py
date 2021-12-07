import re
import shutil
import pathlib
import collections

import pyglottolog
from clldutils.misc import lazyproperty, nfilter
from pycldf.dataset import GitRepository
from pycldf.sources import Source

from pygrambank import bib
from pygrambank import srctok
from pygrambank.sheet import Sheet
from pygrambank.util import iterunique
from pygrambank.contributors import PHOTO_URI, ROLES

# FIXME: These should be fixed in the data!
INVALID = ['9', '.?']
FEATURE_METADATA = [
    'Grambank_ID_desc',
    'boundness',
    'Flexivity',
    'Gender/noun class',
    'locus of marking',
    'word order',
    'informativity',
]


def bibdata(sheet, values, e, lgks, unresolved):
    def clean_key(key):
        return key.replace(':', '_').replace("'", "")

    for row in values:
        if row.Source:
            row.Source_comment = row.Source
            refs, sources = collections.OrderedDict(), []
            uc = sum(list(unresolved.values()))
            res = srctok.source_to_refs(row.Source, sheet.glottocode, e, lgks, unresolved)
            if sum(list(unresolved.values())) > uc:  # pragma: no cover
                row.Source_comment += ' (source not confirmed)'
            for key, pages in res[0]:
                typ, fields = e[key]
                ref = key = clean_key(key)
                if ref not in refs:
                    refs[ref] = set()
                refs[ref] = refs[ref].union(pages or [])
                sources.append(Source(typ, key, **fields))

            row.Source = [
                '{}{}'.format(r, '[{}]'.format(','.join(sorted(p))) if p else '')
                for r, p in refs.items()]
            for src in sources:
                yield src


class Bibs(dict):
    def __init__(self, glottolog, api):
        dict.__init__(self, glottolog.bib('hh'))
        self.update(api.bib)

    def iter_codes(self):
        for key, (typ, fields) in self.items():
            if 'lgcode' in fields:
                for code in bib.lgcodestr(fields['lgcode']):
                    yield key, code


def refs(api, glottolog, sheet):
    glottolog = Glottolog(glottolog)
    languoid, lang = glottolog.api.languoid(sheet.glottocode), None

    # Determine the associated language-level languoid:
    if languoid.level.name == 'dialect':  # pragma: no cover
        for _, gc, _ in reversed(languoid.lineage):
            lang = glottolog.api.languoid(gc)
            if lang.level.name == 'language':
                break
    else:
        lang = languoid

    ids = set(nfilter([languoid.id, languoid.hid, languoid.iso, lang.id, lang.hid, lang.iso]))
    bibs = Bibs(glottolog, api)

    lgks = collections.defaultdict(set)
    for key, code in bibs.iter_codes():
        if code in ids:
            lgks[languoid.id].add(key)

    def source(key):
        type_, fields = bibs[key]
        return key, type_, fields.get('author', fields.get('editor', '-')), fields.get('year', '-')

    unresolved = collections.Counter()
    res = bibdata(sheet, list(sheet.iter_row_objects(api)), bibs, lgks, unresolved)
    return list(res), unresolved, [source(k) for k in lgks[languoid.id]]


def create(dataset, api, glottolog):
    shutil.copy(api.wiki / 'FAQ-(general).md', dataset.directory / 'FAQ.md')

    glottolog = Glottolog(glottolog)
    sheets = []
    for f in sorted(api.sheets_dir.glob('*.tsv'), key=lambda p: p.stem):
        if f.name not in api.exclude:
            sheet = Sheet(f)
            if sheet.glottocode in glottolog.languoids_by_glottocode:
                sheets.append(sheet)
            else:  # pragma: no cover
                print('skipping unknown Glottocode: {}'.format(f.name))
    sheets = [(s, list(s.iter_row_objects(api))) for s in sheets]

    # Chose best sheet for indivdual Glottocodes:
    print('selecting best sheets')
    sheets = list(iterunique(sheets, verbose=True))

    descendants = glottolog.descendants_map

    print('loading bibs')
    bibs = Bibs(glottolog, api)

    print('computing lang-to-refs mapping ...')
    lgks = collections.defaultdict(set)
    for key, code in bibs.iter_codes():
        if code in glottolog.languoids_by_ids:
            gc = glottolog.languoids_by_ids[code].id
            if gc in descendants:
                for cl in descendants[gc]:
                    lgks[cl].add(key)
            else:
                print('---non-language', code)  # pragma: no cover
    print('... done')

    dataset.add_provenance(
        wasGeneratedBy=GitRepository(
            'https://github.com/grambank/pygrambank',
            clone=pathlib.Path(__file__).parent.parent.parent),
    )
    create_schema(dataset)

    data, families = collections.defaultdict(list), set()

    for fid, feature in sorted(api.features.items()):
        d = dict(
            ID=fid,
            Name=feature.name,
            Description=feature.description,
            Patrons=feature.patrons,
        )
        d.update({k: feature.get(k, '') for k in FEATURE_METADATA})
        data['ParameterTable'].append(d)
        for code, desc in sorted(feature.domain.items(), key=lambda i: int(i[0])):
            data['CodeTable'].append(dict(
                ID='{0}-{1}'.format(fid, code),
                Parameter_ID=fid,
                Name=code,
                Description=desc,
            ))

    data['contributors.csv'] = [dict(
        ID=c.id,
        Name=c.name,
        Description=c.bio or '',
        Roles=c.roles,
        Photo=c.photo or '') for c in api.contributors]
    cids = set(d['ID'] for d in data['contributors.csv'])

    def coders(sheet, row):
        return sorted(set(sheet.coders).union(row.contributed_datapoint))

    unresolved, coded_sheets = collections.Counter(), {}
    for sheet, values in sorted(sheets, key=lambda i: i[0].glottocode):
        if not values:  # pragma: no cover
            print('ERROR: empty sheet {0}'.format(sheet.path))
            continue
        lang = glottolog.languoids_by_glottocode[sheet.glottocode]
        coded_sheets[sheet.glottocode] = sheet
        for c in sheet.coders:
            if c not in cids:  # pragma: no cover
                raise ValueError('unknown coder ID: {0} in {1}'.format(c, sheet.path))
        ld = dict(
            ID=sheet.glottocode,
            Name=lang.name,
            Glottocode=sheet.glottocode,
            Coders=sheet.coders,
            provenance=sheet.path.name,
        )
        ld.update(sheet.metadata(glottolog))
        data['LanguageTable'].append(ld)
        if ld['Family_level_ID']:
            families.add(ld['Family_level_ID'])  # pragma: no cover
        dataset.add_sources(*list(bibdata(sheet, values, bibs, lgks, unresolved)))
        for row in sorted(values, key=lambda r: r.Feature_ID):
            if (row.Value in INVALID) or ('source not confirmed' in row.Source_comment):
                continue  # pragma: no cover
            data['ValueTable'].append(dict(
                ID='{0}-{1}'.format(row.Feature_ID, sheet.glottocode),
                Language_ID=sheet.glottocode,
                Parameter_ID=row.Feature_ID,
                Code_ID='{0}-{1}'.format(row.Feature_ID, row.Value) if row.Value != '?' else None,
                Value=row.Value,
                Comment=row.Comment,
                Source=row.Source,
                Source_comment=row.Source_comment,
                Coders=coders(sheet, row),
            ))

    print('computing newick trees')
    data['families.csv'] = sorted([
        {
            'ID': gc,
            'Newick': glottolog.api.newick_tree(
                gc, template='{l.id}', nodes=glottolog.languoids_by_glottocode),
        } for gc in families], key=lambda d: d['ID'])
    dataset.write(**data)

    per_sheet = collections.defaultdict(list)
    for k, v in reversed(unresolved.most_common()):  # pragma: no cover
        print(k, v)
        per_sheet[k[-1]].append(k[:-1])
    print(sum(unresolved.values()))

    return coded_sheets


class Glottolog(object):
    """
    A custom facade to the Glottolog API.
    """
    def __init__(self, repos):
        self.api = repos if isinstance(repos, pyglottolog.Glottolog) \
            else pyglottolog.Glottolog(repos)

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
        return {lang.id: lang for lang in self.languoids}

    @lazyproperty
    def descendants_map(self):
        res = collections.defaultdict(list)
        for lang in self.languoids:
            res[lang.id].append(lang.id)
            if lang.lineage:
                for _, gc, _ in lang.lineage:
                    res[gc].append(lang.id)
        return res

    @lazyproperty
    def languoids_by_ids(self):
        """
        We provide a simple lookup for the three types of identifiers for a Glottolog languoid,
        where hid takes precedence over ISO 639-3 code.
        """
        res = {}
        for lang in self.languoids:
            res[lang.id] = lang
            if lang.iso:
                res[lang.iso] = lang
        for lang in self.languoids:
            if lang.hid:
                res[lang.hid] = lang
        return res


def create_schema(dataset):
    table = dataset.add_table(
        'contributors.csv',
        'ID',
        'Name',
        'Description',
        {'name': 'Photo', 'valueUrl': PHOTO_URI},
        {
            'name': 'Roles',
            'separator': ', ',
            'datatype': {'base': 'string', 'format': '|'.join(re.escape(r) for r in ROLES)},
        },
    )
    table.common_props['dc:description'] = \
        "Grambank is a collaborative effort. The people listed in this table contributed by " \
        "coding languages or guiding the coding as feature patrons or by facilitating the " \
        "project through funding, technical assitance, etc."
    table.tableSchema.primaryKey = ['ID']

    table = dataset.add_component(
        'LanguageTable',
        {
            'name': 'Coders',
            'dc:description': 'References the contributors of the codings for this language',
            'separator': ';',
        },
        {
            'name': 'provenance',
            'dc:description': 'Name of the contributed file',
        },
        {
            'name': 'Family_name',
            'dc:description': 'Name of the top-level language family the variety belongs to',
        },
        {
            'name': 'Family_level_ID',
            'dc:description': 'Glottocode of the top-level language family',
        },
        {
            'name': 'Language_level_ID',
            'dc:description': 'Glottocode of the language-level languoid a variety belongs to - '
                              'in case of doalects',
        },
        'level',
        {
            'name': 'lineage',
            'separator': '/',
            'dc:description': 'list of ancestor groups in the Glottolog classification',
        },
    )
    table.common_props['dc:description'] = "Languageś and dialects for which Grambank has codings."
    table.add_foreign_key('Family_level_ID', 'families.csv', 'ID')
    table.add_foreign_key('Coders', 'contributors.csv', 'ID')

    dataset.add_component(
        'ParameterTable',
        {
            'name': 'Patrons',
            'separator': ' ',
            'dc:description': 'Grambank editors responsible for this feature',
        },
        *FEATURE_METADATA,
    )
    dataset.add_component('CodeTable')
    dataset.add_columns('ValueTable', 'Source_comment', {"name": "Coders", "separator": ";"})
    dataset['ValueTable', 'Value'].null = ['?']
    dataset['ValueTable'].add_foreign_key('Coders', 'contributors.csv', 'ID')
    dataset['ParameterTable'].add_foreign_key('Patrons', 'contributors.csv', 'ID')

    table = dataset.add_table(
        'families.csv',
        'ID',
        'Newick')
    table.tableSchema.primaryKey = ['ID']
