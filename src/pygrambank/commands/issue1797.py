"""

"""
import itertools
import functools

# flake8: noqa

DATAPOINTS = """\
GB146 | Double check with Daria if there really is no concstruction of this type. | Mishchenko, Daria (p.c. 2013) | HS_loma1260.tsv
GB146 | Double check with Elena if there really is no such construction | Perekhvalskaya, Elena (p.c 2013) | HS_mwan1250.tsv
GB146 | Double check with Daria if there really is no concstruction of this type. | Mishchenko, Daria (p.c. 2013) | HS_toma1245.tsv
GB171 | Double check page source | Harvey (2002:194-195) | JLA_gaga1251.tsv
GB333 | Double check with team on weds | Omar 1983:203 | JLA_rung1259.tsv
GB334 | Double check with team on weds | Omar 1983:203 | JLA_rung1259.tsv
GB335 | Double check with team on weds | Omar 1983:203 | JLA_rung1259.tsv
GB333 | Double check with team on weds | Omar 1983:233-234 | JLA_tamb1254.tsv
GB334 | Double check with team on weds | Omar 1983:233-234 | JLA_tamb1254.tsv
GB335 | Double check with team on weds | Omar 1983:233-234 | JLA_tamb1254.tsv
GB304 | I think so? Double check this with Jeremy. Someone killed himself a deer./ A deer got himself killed. | Saxton (1982:144) | JLA_toho1245.tsv
GB026 | Double check figure 4. | Boxwell (1990:160) | JLA_weri1253.tsv
GB158 | Acc. to Wals no, but double check Sapir (1922), then source entire grammar and delete this comment. | Sapir (1922:215-234); Nevin (1976:237-247) | JLA_yana1271.tsv
GB159 | Acc. to Wals no, but double check Sapir (1922), then source entire grammar and delete this comment. | Sapir (1922:215-234); Nevin (1976:237-247) | JLA_yana1271.tsv
GB160 | Acc. to Wals no, but double check Sapir (1922), then source entire grammar and delete this comment. | Sapir (1922:215-234); Nevin (1976:237-247) | JLA_yana1271.tsv
GB401 | Double check this page against the wiki. Labile verb mentioned. | Gijn (2006: 145) | JLA_yura1255.tsv
GB117 | double-check use of pa, p. 253 | Lee 1975:253 | MD-GR-RSI_kosr1238.tsv
GB074 | I think that all of the adpositions are postpositions, but I found something recently that looks like a preposition. I have to double-check. For now, though, let's go with no. | Robinson 2007 | MD-GR-RSI_roto1249.tsv
GB257 | Requires further research to double-check. | Caroline Hendy p.c. (2018) | NP_wiru1244.tsv
GB312 | Requires further research to double-check. | Caroline Hendy p.c. (2018) | NP_wiru1244.tsv
GB330 | double check this | Heath 1999:195 | RB_koyr1240.tsv
GB021 | I think. According to the grammar there are different markers for definite and indefinite non-topics ('objects'), but the examples are confusing. | Wolfenden 1971 | MD-GR-RSI_hili1240.tsv
GB118 | I think | Haiman 1980 | MD-GR-RSI_huaa1250.tsv
GB105 | [XXX CHECK] The dative is used for animates, and recipients are a priori animate I think; GR: I would think that DAT is not Direct Object | Donohue 2004 | MD-GR-RSI_kris1246.tsv
GB075 | I think so [e.g. aape in the dictionary] | Hurd and Hurd 1966; Hurd and Hurd 1970; Hurd 1977 | MD-GR-RSI_naas1242.tsv
GB053 | I'm not sure, but I think it might. It seems that everything in the fourth noun class is animate. | Robinson 2007 | MD-GR-RSI_roto1249.tsv
GB115 | I'm not sure about reflexive vs. reciprocal. I think they share the same marker. Is that a yes for this one then? Agree | Robinson 2007 | MD-GR-RSI_roto1249.tsv
GB146 | I think | NA | MD-GR-RSI_savo1255.tsv
GB160 | adjectives I think. Several word classes show reduplication. See the long note in the separate file TelefolComm.doc' | Healey 1964; Healey 1965; Healey 1965; Healey 1965; Healey 1966; Healey 1964; Healey 1977; Healey 1962; Healey 1974 | MD-GR-RSI_tele1256.tsv
GB086 | I think so, anyway, with iemo | NA | MD-GR-RSI_touo1238.tsv
GB038 | I think they are | Sagna 2008:118 | SVM_band1340.tsv
GB081 | I think it's not a real infix | Strom 2013:248 | SVM_nden1248.tsv
GB105 | [XXX CHECK] The dative is used for animates, and recipients are a priori animate I think; GR: I would think that DAT is not Direct Object | Donohue 2004 | MD-GR-RSI_kris1246.tsv
GB133 | CHECK GRAMMAR In irrealis clauses with the verb 'lack' SOV is the only order possible, and hence pragmatically unmarked p. 750. But the example given might as well be interpreted as a possessive construction: nia ina=n lalek (3sg mother=GEN lack) 'she has no mother'. In the questionnaire for ENUS II, Van Klinken describes these constructions as object incorporation giving apparent SOV order. | van Engelenhoven and Williams-van-Klinken 2005 | MD-GR-RSI_tetu1245.tsv
GB113 | MIINA CHECKS | Miina Norvik, p.c. | RK-MN_livv1244.tsv
GB123 | check | Churchward 1953:217 | HW_tong1325.tsv
GB103 | check | Rasoloson and Rubino 2005 | MD-GR-RSI_plat1254.tsv
GB134 | check | Rasoloson and Rubino 2005 | MD-GR-RSI_plat1254.tsv
GB119 | check | Van Staden 2000 | MD-GR-RSI_tido1248.tsv
GB135 | check and get back | Agbetsoamedo 2014 | HS_sele1249.tsv
GB105 | check grammar | van Engelenhoven and Williams-van-Klinken 2005 | MD-GR-RSI_tetu1245.tsv
GB027 | check grammar. | van Engelenhoven and Williams-van-Klinken 2005 | MD-GR-RSI_tetu1245.tsv
GB069 | check marking of adjectives; this may just be a matter of analysis or frequency: argument cross-referencing is optional; if affixed the adjective could always be interpreted as heading a relative clause, but it could also be the simple absence of marking. | Van Staden 2000 | MD-GR-RSI_tido1248.tsv
GB401 | check pg 73 | Churchward 1953:73 | HW_tong1325.tsv
GB026 | Double check figure 4. | Boxwell (1990:160) | JLA_weri1253.tsv
GB171 | Double check page source | Harvey (2002:194-195) | JLA_gaga1251.tsv
GB330 | double check this | Heath 1999:195 | RB_koyr1240.tsv
GB401 | Double check this page against the wiki. Labile verb mentioned. | Gijn (2006: 145) | JLA_yura1255.tsv
GB146 | Double check with Daria if there really is no concstruction of this type. | Mishchenko, Daria (p.c. 2013) | HS_loma1260.tsv
GB146 | Double check with Daria if there really is no concstruction of this type. | Mishchenko, Daria (p.c. 2013) | HS_toma1245.tsv
GB146 | Double check with Elena if there really is no such construction | Perekhvalskaya, Elena (p.c 2013) | HS_mwan1250.tsv
GB333 | Double check with team on weds | Omar 1983:203 | JLA_rung1259.tsv
GB334 | Double check with team on weds | Omar 1983:203 | JLA_rung1259.tsv
GB335 | Double check with team on weds | Omar 1983:203 | JLA_rung1259.tsv
GB333 | Double check with team on weds | Omar 1983:233-234 | JLA_tamb1254.tsv
GB334 | Double check with team on weds | Omar 1983:233-234 | JLA_tamb1254.tsv
GB335 | Double check with team on weds | Omar 1983:233-234 | JLA_tamb1254.tsv
GB070 | GS: You gave N. I suggest Y, since nae-ba a-m-uw-e (I-focus him-give-I indic) ‘I give him’ is distinguished from nae-‘pa na-m-iy-e (I-focus me-give-he) ‘he gives me’ not only in the verb, but also how the focal marker is formed: class N when subject, class Q when benefactor. I see no such clear example in Scott 1978, but check out p.104 #170 Oblique cases). GR: but this still doesn't count as case marking in my view; it is only a focus marker that changes. | Scott 1978:104 | MD-GR-RSI_fore1270.tsv
GB304 | I think so? Double check this with Jeremy. Someone killed himself a deer./ A deer got himself killed. | Saxton (1982:144) | JLA_toho1245.tsv
GB150 | Jeremy will check in collection of narratives | Luo 2008 | JC_yong1276.tsv
GB159 | KM: Don't think so. (I'll check on it.) | McElhanon 1970; McElhanon 1972 | MD-GR-RSI_sele1250.tsv
GB057 | MD: check that this isn't NA | Davies 1992 | MD-GR-RSI_ramo1244.tsv
GB058 | MD: check that this isn't NA | Davies 1992 | MD-GR-RSI_ramo1244.tsv
GB082 | Nick said - checking with Hedvig re Mawng productivity | Pym and Larrimore 1979 | RSI_iwai1244.tsv
GB257 | Requires further research to double-check. | Caroline Hendy p.c. (2018) | NP_wiru1244.tsv
GB312 | Requires further research to double-check. | Caroline Hendy p.c. (2018) | NP_wiru1244.tsv
GB313 | SY: check for pages | Barth (2019) | SY_matu1261.tsv
GB171 | Check 160 | Guo (2010:1-196) | MY_youn1235.tsv
GB074 | Check in locative and instrumental enclitics which seem to mark oblique cases, count here for prep and post. | Campbell (2006:v-115) | JLA_urni1239.tsv
GB075 | Check in locative and instrumental enclitics which seem to mark oblique cases, count here for prep and post. | Campbell (2006:v-115) | JLA_urni1239.tsv
GB150 | Check other sources. | Deal (2010:1-460); Crook (1999:2-498); Cash (2004:1-72) | JLA_nezp1238.tsv
GB327 | Check pp. 38-39. Relative clause is mentioned there but the gloss is rather useless. | Piau (1985:1-147) | ER_kuma1280.tsv
GB025 | Check the example under interrogative: savai malamalapopore nake (...) | Ray (1926:373) | DB_akei1237.tsv
GB171 | Check this. | Hayward (1984:191-192) | JLA_arbo1245.tsv
GB329 | Check with Jeremy. | Gerner (2013:65) | JLA_sich1238.tsv
GB330 | Check with Jeremy. | Gerner (2013:92) | JLA_sich1238.tsv
GB331 | Check with Jeremy. | Gerner (2013:93) | JLA_sich1238.tsv
GB327 | Check! | Reichle (1981:91-94) | RHA_bawm1236.tsv
GB037 | Checking required | Yihan Chen, Rebecca Dixon and Caroline Hendy p.c. (2018) | NP_wiru1244.tsv
GB252 | Checking required | Yihan Chen, Rebecca Dixon and Caroline Hendy p.c. (2018) | NP_wiru1244.tsv
GB253 | Checking required | Yihan Chen, Rebecca Dixon and Caroline Hendy p.c. (2018) | NP_wiru1244.tsv
GB256 | Checking required | Yihan Chen, Rebecca Dixon and Caroline Hendy p.c. (2018) | NP_wiru1244.tsv
GB265 | Not mentioned in the Deal grammar. Check others. | Deal (2010:1-460); Crook (1999:2-498); Cash (2004:1-72) | JLA_nezp1238.tsv
GB266 | Not mentioned in the Deal grammar. Check others. | Deal (2010:1-460); Crook (1999:2-498); Cash (2004:1-72) | JLA_nezp1238.tsv
GB270 | Not mentioned in the Deal grammar. Check others. | Deal (2010:1-460); Crook (1999:2-498); Cash (2004:1-72) | JLA_nezp1238.tsv
GB273 | Not mentioned in the Deal grammar. Check others. | Deal (2010:1-460); Crook (1999:2-498); Cash (2004:1-72) | JLA_nezp1238.tsv
GB275 | Not mentioned in the Deal grammar. Check others. | Deal (2010:1-460); Crook (1999:2-498); Cash (2004:1-72) | JLA_nezp1238.tsv
GB276 | Not mentioned in the Deal grammar. Check others. | Deal (2010:1-460); Crook (1999:2-498); Cash (2004:1-72) | JLA_nezp1238.tsv
GB285 | Not mentioned.. requires only a question particle? Check this. | Stephen Matthews and Virginia Yip. 1994. Cantonese: A Comprehensive Grammar | JLA_yuec1235.tsv"""
DATAPOINTS = sorted((i.split('|')[-1].strip(), i.split('|')[0].strip()) for i in DATAPOINTS.split('\n'))
DATAPOINTS = {fname: set(i[1] for i in dps) for fname, dps in itertools.groupby(DATAPOINTS, lambda i: i[0])}


def fixer(fids, row):
    if row['Feature_ID'] in fids:
        fids.remove(row['Feature_ID'])
        if row['Value'] != '?':
            row['Value'] = '?'
            print('Value changed')
        row['Comment'] = ''
    return row


def run(args):
    for sheet in args.repos.iter_sheets():
        if sheet.path.name in DATAPOINTS:
            sheet.visit(
                row_visitor=functools.partial(
                    fixer,
                    DATAPOINTS[sheet.path.name],
                ))

    for gc, dps in DATAPOINTS.items():
        assert not dps
