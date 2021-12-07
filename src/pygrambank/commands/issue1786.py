"""

"""
import functools
import itertools

from clldutils.misc import slug

# flake8: noqa

DATAPOINTS = """
GB068 | Edelsten & Lijongwa (2010: 40, 67-71) | Compare adjectival concord and verbal concord. | ndam1239
GB069 | Edelsten & Lijongwa (2010: 40, 67-71) | Compare adjectival concord and verbal concord. | ndam1239
GB069 | Hansson (2017:893) | Adjectives are for the most part stative verbs, but when used attributively they must be preceded either by adjectival prefix 'jɔ-', or by a reduplicated syllable of the head noun; the two constructions denote temporary and inherent properties respectively. | akha1245
GB069 | Hargus (2007:319-321, 557-563) | Property concepts are expressed in a variety of different ways; some are considered descriptive or neuter verbs and inflect as such, and some fall into one of 3 subclasses of adjective. Only the latter can be used attributively | babi1235
GB069 | Cook (2013:395) | Only two property words - k'an 'new' and jed 'old' - can be used attributively; all other descriptive property concepts are expressed as stative verbs. | chil1280
GB069 | Solnit (1997:5-6, 186-190, 253-258) | There is no true class of 'adjectives' in Kayah, rather stative or property verbs. In order to be used attributively, they (whether property word or verbal modifier) must be placed within a postposed relative clause. Moreover, there is no verbal inflection in the language, and thus no morphology which the two might share. | east2342
GB069 | Goossen (1995:19, 106); Williams (2009:115); Young & Morgan (1987:189) | There is no independent class of adjectives in Navajo, only stative or 'adjectival' verbs; they cannot be used attributively. | nava1243
GB069 | Woodbury (2018:143) | There are no adjectives, only stative verbs expressing property meaning; these cannot be used attributively. | onon1246
GB069 | Cook (1984:67, 100, 157) | There is no seperate class of adjectives. Property concepts are expressed either by 'neuter' verbs, or by nominal qualifiers, derivational affixes which are often derived from the corresponding neuter verb themselves. | sars1236
GB068 | Kamanda-Kola 2003: 279-289 | Stative verbs can be derived from adjectives by changing tone. | mono1270
GB069 | McWhorter and Good (2012:107) | Since there is almost no verbal morphology, I code 0 because of the differential reading of verbs and property words under reduplication. | sara1340
GB068 | de Vries (1993:31, 36) | Verbs can, however, be productively derived from adjectives (p. 14) | komb1274
GB068 | van de Kerke (2009:316-317) | There are some tendencies but, e.g., verbal negation is not allowed | leco1242
GB069 | Sibomana (2008:28-29) | Though many are derived from verbs | zarm1239
GB069 | Robinson 2008: 135 | Adjectives that do not inflect for aspect exist | dupa1235
GB069 | Johnston 1980: 161 | Very small set of core adjectives does not behave like verbs | naka1262
GB069 | Shultz (1997:18-19) | There are very few (if any) true adjectives. They do not have any verbal features. Other property words which are based on verb roots behave also differently than verbs when used attributively. | komc1235
GB069 | Blood (1999:15-16); Mbibeh (1996:89) | The few existing adjectives are derived from stative verbs. These derived forms do not behave like verbs. | okuu1243
GB069 | Valentine (2001:342-347, 592) | All property concepts can act like verbs and then they require the same morphology as intransitive verbs. However, many concepts can also be expressed as so-called prenouns, deriving a new word by prefixing to the noun. These are considered as core adjectives here. | otta1242
GB068 | Smith (1979:84-85) | Both take no morphology. | seda1262
GB069 | Smith (1979:84-85) | Both take no morphology. | seda1262
GB069 | Todd (1970:64-68, 112, 144-152, 201, 203, 239-240) | Some concepts are expressed as verbs, but not all of them. | seve1240
GB069 | Andrews (1994:87-89, 93-95); Boling (1981:118) | The concepts which can be expressed as so-called prenouns are considered as core adjectives here. All other property concepts require verbal morphology. | shaw1249
GB069 | Engelkemier (2010:18-21, 25) | There is very limited verbal morphology (reciprocal, causative). Adjectives are considered stative verbs and seem to have no marking at all in attributive position. | west2397
GB069 | Segerer, G (2013 p.c.) | It could be analyzed as a participle | kera1248
GB068 | Fofana 2002:121 | There are however a few adjectival roots (""be black and white"" for example). | pula1263
GB069 | Doris Richter. (forthcoming) A Grammar of Mbembe.:134-151 | They are often derived from verbs in a participle form. | tigo1236
GB068 | Nashipu (2005:125-128) | True 'non-derived' adjectives do not appear to be used predicatively. | baba1264
GB068 | Sommer (2010:291); Zorc (1967:71) | There is no disction between verbal and adjectival roots. When there is the prefix 'ma-' and the translation is predicative. Adnominal property words take the linker 'nga'. | bant1288
GB068 | Singh (2000:144-146, 152-153, 201) | ""Adjective is derived from the verbal roots. In this case, prefix e- is used as a formative particle and the nominalizer -pa is suffixed to the verbal root"" p.145 | chot1239
GB069 | Singh (2000:144-146, 152-153, 201) | ""Adjective is derived from the verbal roots. In this case, prefix e- is used as a formative particle and the nominalizer -pa is suffixed to the verbal root"" p.145 | chot1239
GB068 | Toba (1984:27, 30-31) | There is no separate class of adjectives - they are derived from verbs. | khal1275
GB069 | Toba (1984:27, 30-31) | There is no separate class of adjectives - they are derived from verbs. | khal1275
GB069 | Foulkes (1915:218-219) | There is no bound marking (but there is a preceding particle 'kō' which creates a ""substantive"".) | ngas1240
GB068 | Crowther (1864:12-13, 15) | No adjectival or verbal inflection. | nupe1254
GB069 | Crowther (1864:11-13, 15); Kawu (2002:209-214) | No adjectival or verbal inflection. | nupe1254
GB068 | Tiwari (1971:76, 88, 123, 127-130) | No definable class of adjectives, only verbs convey property concepts. | rong1266
GB069 | Tiwari (1971:76, 88, 123, 127-130) | No definable class of adjectives, only verbs convey property concepts. | rong1266
GB068 | Kobayashi 2012:29 | no TAM marking; person marking is possible (p.29) | saur1249
GB068 | Barkman (2014:60, 81-83, 115-118) | No separate word class for adjectives is found, but attributive verbs function as such. | para1302
GB069 | Barkman (2014:60, 81-83, 115-118) | No separate word class for adjectives is found, but attributive verbs function as such. | para1302
GB068 | Shelden (1989:xxi-149) | Galela use a kind of relative clause headed by a stative verb, or also uses participial forms of stative verbs. There are no adjectives in this language. | gale1259
GB069 | Shelden (1989:xxi-149) | Galela use a kind of relative clause headed by a stative verb, or also uses participial forms of stative verbs. There are no adjectives in this language. | gale1259
GB069 | Cai (2016:110-111, 117) | Neither take marking. | honi1244
GB068 | Omar 1983:256 | Take an adjectival prefix to mark the predicative function of the adjective. | lotu1250
GB069 | Jenny (2005:109) | Verbal infix turns stative verbs into attributive adjectives. | monn1252
GB068 | Codrington & Palmer 1896:xvii | Not always | mota1237
GB069 | Codrington & Palmer 1896:xvii | Not always | mota1237
GB069 | Robson (2011:110) | Most adj are derived from verbs, very small number are not. They do not seem to take markings like verbs do however. | njan1240
GB068 | Beltrame (1877: 15-16) | Adjectives take no inflection. | asoa1238
GB069 | Beltrame (1877: 15-16) | Adjectives take no inflection. | asoa1238
GB068 | De Rendinger (1949: 181) | There is no adjectival morphology. | bolg1251
GB069 | De Rendinger (1949: 181) | There is no adjectival morphology. | bolg1251
GB068 | Lesage 2020:264 | They are always derived from verbs. They do not take the morphology nouns take in predicative position, so in that sense they're more akin to verbs than to nouns. But they are still radically different from verbs. They are not marked for tense, aspect and negation, for instance. | kamm1249
GB069 | Lesage 2020: 173-177 | They are always derived from verbs. So the stem is always a verb. They do not take any verbal inflection, however. | kamm1249
GB069 | Lord 2016: 44, 34 | Although there is no discussion on verbs used attributively, see example 57. | yora1241
GB068 | Bon 2014:1-628 | Acc. to Bon (2014), property words are statif verbs, however, there is no verbal morphology on either verbs or adjectives. | bulo1242
GB069 | Bon 2014:1-628 | Acc. to Bon (2014), property words are statif verbs, however, there is no verbal morphology on either verbs or adjectives. | bulo1242
GB068 | Cammenga 2002:499-500 | Only one example of a color term in a copula construction, in this case without verbal morphology. All other terms without examples and glosses. | gusi1247
GB068 | Jenny and Mccormick 2015:539 | Although property concepts are expressed by verbs, they do not take any morphology. | oldm1242
GB069 | Jenny and Mccormick 2015:539 | Although property concepts are expressed by verbs, they do not take any morphology. | oldm1242
GB068 | Svantesson 1988:101 | Adjectives are stative verbs but there is no morphology. | uuuu1243
GB069 | Svantesson 1988:101 | Adjectives are stative verbs but there is no morphology. | uuuu1243
GB069 | Prentice 1971: 32-33, 190-193 | The relator used with adjectives can be omitted. | timu1262
GB068 | Bennett, C. E. (1908:34-43) | some core adjectives do e.s. Rubere (cf. Rau 2009: esp. 114-115, 123-125) | lati1261
GB069 | Dillon 1994:23 | Attributive adjectives have no affixes. | tata1257
GB069 | Paudyal (2015:72-75,162) | ""extremely few descriptive adjectives in Chintang"" (Paudyal 2015:73): | chhi1245
GB069 | Field 1997:267-272 | “[adjectives] do not take verbal morphology unless they are derived as verbs” (p271) | dong1285
GB069 | Kratochvíl 2007:92 | In constrast to other verbs, stative verbs do not require embedding in a relative clause with the intersective linker ba (CSEQ). | abui1241
GB068 | Holzknecht 1986:106-108 | mentions two Types of adj: Type 1 includes shape, age, dimension and value = 'bare'adjectives, attributively and predicatively; Type II have some value, but further propensities, and these are stative verbs in predicative position. | adze1240
GB069 | Holzknecht 1986 | This answer holds for Type I; Type II require verb-like treatment = nominalization by Participle /-an/. | adze1240
GB068 | Conrad and Wogiga 1991:33, 37 | Class 6 = Stative verbs have object suffix for S; Non-statives: S prefix | buki1249
GB068 | Green 1987; Glasgow 1981; Glasgow 1980; Green 2003 | Adjectives agree with their modifier in class, case, person, number and gender. Agreement markers used are the same as for verbs. Adjectives differ from verbs in that they do not take TAM marking and adjectives take case markers (Green:8). | bura1267
GB068 | Bunye & Yap 1971a; Bunye & Yap (1971b); Payne 1994; Valkama 2000 | Differ from verbs in not taking voice marking | cebu1242
GB069 | Bunye & Yap 1971a; Bunye & Yap (1971b); Payne 1994; Valkama 2000 | Differ from verbs in not taking voice marking | cebu1242
GB068 | Scott 1978 | but all utterances require final MOOD, e.g. IND /=e/. GS: You gave N. Since –e is a mood suffix that completes an utterance on verbs, and on non-verbs when they end (usually short) utterances, my answer would be Y. (You already referenced Scott 1978:84).\|\|GR: Yes, but no Tense & P/N! | fore1270
GB069 | Dougherty 1983:92 | apparently not; no TAM marking (p. 92) | futu1245
GB068 | Wolfenden 1971 | Distinct from verbs in that they don't take the voice marking. | hili1240
GB069 | Wolfenden 1971 | Distinct from verbs in that they don't take the voice marking. | hili1240
GB069 | Haiman 1980:266 | most adjectives are analyzed as nouns | huaa1250
GB068 | Donohue and San Roque 2004:39, 41 | adjectives, unlike verbs, begin with consonant, and lack S prefix when predicative | kris1246
GB068 | Franklin 1971; Franklin 1978; Franklin 1981; Yarapea 2001 | áá rúdu 'man is short'= 'It is a short man' or 'He is a man who is short'; Such predicative use may use an existential verb as pia 'sit' (p.87; See also Franklin 1981). KF: There are adjectives that act like verbs in predicative positions:. Aa epe-ae = The man who is good... | west2599
GB068 | Vuillermet 2012: 544 | there are predicative adjectives which usually take special morphology. The author mentions a dozen occurences whre predicative adjectives display unexpected verbal morphology, but it is not a general characteristic of property words. | esee1248
GB069 | Dai (2009:71-72, 76-77) | What is labelled as adjectives are mostly stative verbs which form relative clauses with an auxiliary particle in order to be used attributively; same with regular verbs. Though there are also examples in which these property words act like true adjectives and do not require the formation of a relative clause. | enuu1235
GB069 | Dai and Li (2007:127, 138) | Attributive verbs must form a relative clause. This appears optional with property words. Relative clauses are formed with the genitive particle ta55 and therefore not considered as morphological. | lash1243
GB069 | Chen, Wan and Lai (1986:41, 43-44); Deepadung, Rattanapitak and Buakaw (2015:1076, 1092) | Most property words appear to be stative verbs though not explicitly described as such in Chen et al (1986). There is a group of adjectives that form a relative clause when used attributively (like verbs) but there are also examples of adjectives that simply occur after the noun. The formation of the relative clauses however, is syntactical (word order) and does involve any morphological markers. Deepadung et al (2015) however describes the property words as adjectival stative verbs. | ruch1235
GB068 | Kossmann (2013:129) | There are no adjectives. | ghad1239
GB069 | Kossmann (2013:129) | There are no adjectives. | ghad1239
GB069 | el Hannouche (2008:66, 73) | Adjectives inflect for feminine gender and plural; participles have no inflection for these categories. | ghom1257
GB069 | Jauncey (2011:184, 275) | There is no morphologically distinguishable adjective word class in Tamambo adjectival meaning is expressed by verbs. | malo1243
GB068 | Ryding (2005:240, 438) | Adjectives in predicative use agree with the subject in gender and number. Verbal predicates also agree in person and inflect for TAME. | stan1318
GB068 | Schnell (2011:67, 72) | There are only three adjectives in Vera'a and those are not considered a grammatically definable class. Properties are expressed by property verbs. | vera1241
GB069 | Schnell (2011:67,72) | There are only three adjectives in Vera'a and those are not considered a grammatically definable class. Properties are expressed by property verbs. | vera1241
GB068 | Juldasev (1981:169); Poppe (1964:87-88) | Nominals are either unmarked used predicatively or take a predicative suffix indicating person and number as well as a plural number agreement suffix. Poppe (1964:87): there is no number agreement. Number of the S/A argument is not marked on the verb -> number marked on the adjective cannot be considered “acting like verbs” | bash1264
GB068 | Sumbatova (2012:39, 41, 56-57) | Examples do not provide evidence. | land1256
GB069 | Sumbatova (2012:26-61); Sumbatova (1999:533) | Examples do not provide evidence. | land1256
GB068 | Blackings (2003:106) | “There is no morphological diflerence between attributive and predicative adjectives.” | madi1260
GB069 | Blackings (2003:106) | “There is no morphological diflerence between attributive and predicative adjectives.” | madi1260
GB069 | Payne and Payne (2013:283) | There is no distinct class of adjectives in Panare; some descriptive are nouns, some are adverbs (see Payne and Payne 2013:281-282) | enap1235
GB068 | Reichle (1981:85) | Adjectives are described as ""adjective-verbs"" and must be followed by modifier tak in a predicative construction. Transitive verbs in predicate position do not require this. | bawm1236
GB068 | Rubino (2005:311, 313, 316) | There are also stative verbs but predicative adjectives receive no stative marking. | bayb1234
GB069 | Blust (1999:321-365) | Adjectives are stative verbs in this language and so aren't used attributively. | kulo1237
GB068 | Ding (1998:92) | Verbs in predicative position are labelled 'descriptive verbs' but do not have a different form. | nort2723
GB068 | Fabre (2016) | There is no adjectival word class. | niva1238
GB069 | Fabre (2016) | There is no adjectival word class. | niva1238
GB069 | Palancar (2009) | There is no adjectival word class. | quer1236
GB068 | Moser (2004: 845ff) | there is no attributive copula, most adnominal attribution is expressed through relative clauses and predicative attribution through stative verbs. The small group of core adjectives do not seem to take verbal morphology when used predicatively. | seri1257
GB068 | Einarsson 1976:116 | However, they can take on verbal morphology (""X greens""). | icel1247
GB068 | Hantgan 2014:37f | Not entirely clear from the examples. There are also verbal adjectives, however they differ from adjectives in their formal behaviour. | tief1242
GB068 | Dempwolff n.d.:37-39 | Predicative adjectives can occasionally take TAM suffixes, however, this creates a change in meaning consistent with the TAM marking; in most cases, predicative adjectives are treated like predicative nominals. | geda1237
GB069 | Meng 2018:85, 119-122 | Verbs do not take affixes/'morphological treatment' | taul1251
GB068 | Naden 1988:29-30 | Adjectives cannot be used predicatively | fare1241
GB069 | Betty Snell 1978; Snell, Betty E. 1998; José Pío Aza 2005 | only some, there are different adj classes.Datapoint inherited from Danielsen’s work in the database of South American Indigenous Language Structures (SAILS). | mach1267
GB069 | Constenla Umaña 1991:190 | only in negative clauses | wapi1253
GB068 | Hellwig 2011:9 | no adjectives | goem1240
GB069 | Hellwig 2011:9 | no adjectives | goem1240
GB068 | Innes 1967:105 | no adjectives | mend1266
GB069 | Innes 1967:105 | no adjectives | mend1266
GB068 | Hellenthal 2010:210 | adjectives are derived from verbs | shek1245
GB069 | Hellenthal 2010:210 | adjectives are derived from verbs | shek1245
GB068 | Dum-Tragut (2009: 116); Zorc (1995: 265-268) | Adjectives can be used in attributive and predicative functions. In both functions they do not agree with the noun(s) in number and case. | nucl1235
GB069 | Dum-Tragut (2009: 116) | Adjectives can be used in attributive and predicative functions. In both functions they do not agree with the noun(s) in number and case. | nucl1235
GB068 | Haspelmath 1993:116 | The (verbal) predicative suffix -da used to be attached to adjectives, but this is no longer the case in the modern standard language. | lezg1247
GB069 | Peterson (2011:126-127) | Although there is no separate lexical class of adjectives, contentive morphemes require a different morphosyncactic treatment as verbs in attributive position. | khar1287
GB069 | Nagaya 2012: 175-200 | Similar to verbs, adjectival verbs need to be nominalized when used attributively. However, these nominalizers are not used productively by regular verbs anymore. Regular verbs use a nominalizer borrowed from Indonesian most of the time. | lewo1244\
""".split('\n')


def split_dp(line):
    parts = line.split('|')
    # Comments may contain "|", so we have to be a bit careful when parsing markdown table rows:
    return (
        parts[0].strip(),  # What comes before the first "|"
        parts[1].strip(),  # Between first and second "|"
        '|'.join(parts[2:-1]).strip(),  # Between second and last "|"
        parts[-1].strip()  # After last "|"
    )


DATAPOINTS = [split_dp(row) for row in DATAPOINTS if row]
DATAPOINTS = sorted(DATAPOINTS, key=lambda i: (i[-1], i[0]))
# Turn datapoints into nested dicts. This allows us to keep track of everything we found by deleting
# the corresponding entry.
DATAPOINTS = {
    # glottocode: {feature_id: comment ...}
    gc: {dp[0]: dp[2] for dp in dps}
    for gc, dps in itertools.groupby(DATAPOINTS, lambda i: i[-1])}


def fixer(datapoints, row):
    """
    :param datapoints: `dict` mapping feature IDs of datapoints to fix for a glottocode to comments.
    :param row: A `dict` of (column, value) pairs, representing a row in a sheet.
    """
    if row['Feature_ID'] in datapoints:
        # Here's a feature that might need fixing. Check if the comment is as expected:
        # (Since there may be more sheets per glottocode, we must make sure to not fix in the
        # wrong sheets.)
        # Sluggifying the comment strings makes for a simple "fuzzy" matching.
        if slug(row['Comment']) == slug(datapoints[row['Feature_ID']]):
            assert row['Value'] == '0'
            row['Value'] = '?'
            row['Comment'] = ''
            # We delete the datapoint to be able to check for completeness of the fixing lateron.
            del datapoints[row['Feature_ID']]
    return row


def run(args):
    for sheet in args.repos.iter_sheets():
        if sheet.glottocode in DATAPOINTS:
            # A sheet that might contain datapoints to fix!
            sheet.visit(
                row_visitor=functools.partial(
                    fixer,
                    DATAPOINTS[sheet.glottocode],  # We pass in the dict of features to fix.
                ))

    # Make sure we fixed all datapoints:
    for gc, dps in DATAPOINTS.items():
        assert not dps
