import os, csv, time
from .constants import TENSE, TENSE_NAMES, TENSE_VALUES
from requests_html import HTMLSession


KEY_FIELD = ("inf",)
SUPPLIED_FIELDS = (
    "hint", "hint-rules", "use-eng-defs", 
    "eng-inf", "eng-gerund", 
    "eng-1", "eng-3", "eng-p", 
    "eng-past", "eng-past-perf"
)
BUILT_FIELDS = (
    "gerund", "participle", 
    "present-1s", "present-2s", "present-3s", "present-1p", "present-2p", "present-3p", 
    "imperfect-1s", "imperfect-2s", "imperfect-3s", "imperfect-1p", "imperfect-2p", "imperfect-3p", 
    "perfect-1s", "perfect-2s", "perfect-3s", "perfect-1p", "perfect-2p", "perfect-3p", 
    "future-1s", "future-2s", "future-3s", "future-1p", "future-2p", "future-3p", 
    "futcond-1s", "futcond-2s", "futcond-3s", "futcond-1p", "futcond-2p", "futcond-3p", 
    "imp1-2s", "imp1-3s", "imp1-1p", "imp1-2p", "imp1-3p", 
    "imp0-2s", "imp0-3s", "imp0-1p", "imp0-2p", "imp0-3p"
)
FIELDS = KEY_FIELD + SUPPLIED_FIELDS + BUILT_FIELDS


URL = "https://european-portuguese.info/conjugator/{0}"

_TENSE_TABLE_NAMES = (
    "Presente", 
    "Pretérito Perfeito", 
    "Pretérito Imperfeito", 
    "Futuro", 
    "(Futuro do Pretérito)", 
    "Afirmativo", 
    "Negativo"
)
_TENSE_TABLE_MAP = {
    "Presente":              TENSE.PRESENT, 
    "Pretérito Perfeito":    TENSE.PERFECT, 
    "Pretérito Imperfeito":  TENSE.IMPERFECT, 
    "Futuro":                TENSE.FUTURE, 
    "(Futuro do Pretérito)": TENSE.FUTURE_COND, 
    "Afirmativo":            TENSE.IMPERATIVE_AFM, 
    "Negativo":              TENSE.IMPERATIVE_NEG
}


def session():
    '''Get HTTP session.'''
    return HTMLSession()


def get(infinitive, session=None):
    '''Get tense map using conjugator website and scraping.'''

    # open page
    if not session:
        session = HTMLSession()
    page = session.get(URL.format(infinitive))
    page.html.render()

    # check for warning if invalid/unrecognized infinitive
    warning = page.html.find("#warning", first=True)
    if warning and warning.text:
        return Warning(warning.text)

    # parse tense tables
    tense_tables = {}
    conjugations = page.html.find("span.tense")
    for table in conjugations:
        tense_name = table.find("span.tense-name", first=True).text
        # recognized tense name, skip 2nd/duplicate which are for subjective forms
        if tense_name in _TENSE_TABLE_NAMES and _TENSE_TABLE_MAP[tense_name] not in tense_tables:
            tense_tables[_TENSE_TABLE_MAP[tense_name]] = table.find("span.persons-forms", first=True)
    # check for missing tense tables
    missing = list(set(_TENSE_TABLE_MAP.values()) - set(tense_tables.keys()))
    if len(missing):
        return Warning("Unable to find {0} table(s) @ {1}".format(
            " and ".join([TENSE_NAMES[t] for t in missing]), 
            URL.format(infinitive))
        )

    # parse tense tables
    tense_maps = {}
    for tense, tense_table in tense_tables.items():
        tense_map = tense_maps[tense] = {}
        span_persons = tense_table.find("span.persons > span", first=False)
        span_forms = tense_table.find("span.forms > span", first=False)
        for i, span_person in enumerate(span_persons):
            tense_map[span_person.text] = span_forms[i].text

    # parse gerund and participle forms
    gerund_past_spans = page.html.find("#gerund-past > span", first=False)
    save_as = False
    for span in gerund_past_spans:
        if save_as:
            if save_as != "-":
                tense_maps[save_as] = span.text
                save_as = False
        elif span.text.startswith("Gerúndio"):
            save_as = "gerund"
        elif span.text.startswith("Particípio Passado"):
            save_as = "participle"
        else:
            save_as = "-"

    return tense_maps


def build(card, tense_maps):
    '''Expand card definition from tense map'''

    card["gerund"] = tense_maps["gerund"]
    card["participle"] = tense_maps["participle"]

    for tense, tense_map in tense_maps.items():
        # get tense key
        imperative = False
        if tense == TENSE.PRESENT:
            tense_key = "present"
        elif tense == TENSE.IMPERFECT:
            tense_key = "imperfect"
        elif tense == TENSE.PERFECT:
            tense_key = "perfect"
        elif tense == TENSE.FUTURE:
            tense_key = "future"
        elif tense == TENSE.FUTURE_COND:
            tense_key = "futcond"
        elif tense == TENSE.IMPERATIVE_AFM:
            imperative = True
            tense_key = "imp1"
        elif tense == TENSE.IMPERATIVE_NEG:
            imperative = True
            tense_key = "imp0"
        else:
            continue

        if not imperative:
            # 1st person singular imperative doesn't make sense
            card["{0}-1s".format(tense_key)] = tense_map["eu"]
        card["{0}-2s".format(tense_key)] = tense_map["tu"]
        card["{0}-3s".format(tense_key)] = tense_map["ele"]
        card["{0}-1p".format(tense_key)] = tense_map["nós"]
        card["{0}-2p".format(tense_key)] = tense_map["vós"]
        card["{0}-3p".format(tense_key)] = tense_map["eles"]
