import os, csv, time
from .constants import TENSE
from requests_html import HTMLSession


BASIC_FIELDS = [
    "inf", "eng-hint", "hint-to-eng", "eng-1", "eng-3", "eng-p", "eng-inf", "eng-gerund"
]
FIELDS = [
    "inf", "gerund", "participle", 
    "eng-hint", "hint-to-eng", 
    "eng-inf", "eng-gerund", "eng-1", "eng-3", "eng-p", 
    "present-1s", "present-2s", "present-3s", "present-1p", "present-2p", "present-3p"
]
REQUIRED_FIELDS = [
    "inf", 
    "gerund", "participle", 
    "present-1s", "present-2s", "present-3s", "present-1p", "present-2p", "present-3p"
]
OPTIONAL_FIELDS = list(set(FIELDS) - set(REQUIRED_FIELDS))


URL = "https://european-portuguese.info/conjugator/{0}"


def session():
    return HTMLSession()


def get(infinitive, tense=TENSE.PRESENT, session=None):
    if tense == TENSE.PRESENT:
        tense = "Presente"
    # elif tense == TENSE.PERFECT:
    #     tense = "Pretérito Perfeito"
    # elif tense == TENSE.IMPERFECT:
    #     tense = "Pretérito Imperfeito"
    # elif tense == TENSE.FUTURE:
    #     tense = "Futuro"
    else:
        raise Exception("Tense not recognized or supported")

    if not session:
        sexxion = HTMLSession()
    page = session.get(URL.format(infinitive))
    page.html.render()

    warning = page.html.find("#warning", first=True)
    if warning and warning.text:
        return Warning(warning.text)

    tense_table = None
    conjugations = page.html.find("span.tense")
    for table in conjugations:
        if table.find("span.tense-name", first=True).text == "Presente":
            tense_table = table.find("span.persons-forms", first=True)
            break

    if not tense_table:
        return Warning("Unable to find {0} table @ {1}".format(tense, URL.format(infinitive)))

    tense_map = {}
    span_persons = tense_table.find("span.persons > span", first=False)
    span_forms = tense_table.find("span.forms > span", first=False)
    for i in range(len(span_persons)):
        tense_map[span_persons[i].text] = span_forms[i].text

    gerund_past_spans = page.html.find("#gerund-past > span", first=False)
    save_as = False
    for span in gerund_past_spans:
        if save_as:
            if save_as != "-":
                tense_map[save_as] = span.text
                save_as = False
        elif span.text.startswith("Gerúndio"):
            save_as = "gerund"
        elif span.text.startswith("Particípio"):
            save_as = "participle"
        else:
            save_as = "-"

    return tense_map


def build(card, tense_map):
    card["present-1s"] = tense_map["eu"]
    card["present-2s"] = tense_map["tu"]
    card["present-3s"] = tense_map["ele"]
    card["present-1p"] = tense_map["nós"]
    card["present-2p"] = tense_map["vós"]
    card["present-3p"] = tense_map["eles"]
    card["gerund"]     = tense_map["gerund"]
    card["participle"] = tense_map["participle"]
