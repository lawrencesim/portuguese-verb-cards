from .constants import *
from .misc import pick_one
import os, csv, random


def read(card_bank_filepath, build_forms=True):
    card_bank = []
    with open(card_bank_filepath, "r", encoding="utf-8") as csvf:
        reader = csv.DictReader(csvf)
        card_bank = [card for card in reader]
    if not build_forms:
        return card_bank
    for card in card_bank:
        card["hint-to-eng"] = int(card["hint-to-eng"])
        # split by multiple versions (if existing)
        card["eng-1"] = card["eng-1"].split("/")
        # split existing, or infinitive form with 'to' prefix
        if card["eng-inf"]:
            card["eng-inf"] = card["eng-inf"].split("/")
        else:
            card["eng-inf"] = ["to {0}".format(verb) for verb in card["eng-1"]]
        # split existing, or third person form same as first period with +'s'
        if card["eng-3"]:
            card["eng-3"] = card["eng-3"].split("/")
        else:
            card["eng-3"] = [v+"s" for v in card["eng-1"]]
        # split existing, or plural form same as first person
        if card["eng-p"]:
            card["eng-p"] = card["eng-p"].split("/")
        else:
            card["eng-p"] = card["eng-1"]
        # gerund forms
        if card["eng-gerund"]:
            card["eng-gerund"] = card["eng-gerund"].split("/")
        else:
            variations = []
            for form in card["eng-inf"]:
                gerund = form.split(" ")[1:]
                if gerund[0][-1] == "e" and gerund[0][-2] != "e":
                    gerund[0] = gerund[0][:-1]
                gerund[0] = gerund[0] + "ing"
                variations.append(" ".join(gerund).strip())
            card["eng-gerund"] = variations
    return card_bank


def get_pronouns(person=PERSON.FIRST, singular=True):
    por = PRONOUNS[0 if singular else 1]
    eng = ENG_PRONOUNS[0 if singular else 1]
    if person == PERSON.FIRST or person == PERSON.SECOND:
        # first and second only have one form
        return {
            "portuguese": por[person], 
            "english": eng[person]
        }
    elif person != PERSON.THIRD:
        raise Exception("Unknown person given")
    # third person via random choice
    por = random.choice(por[3][1:])
    # check second person using third form, if singular match pronoun gender, or plural is basic
    if por.startswith("você"):
        eng = eng[2]
    elif singular:
        eng = eng[3][0 if por.startswith("ele") else 1]
    else:
        eng = eng[3]
    return {
        "portuguese": por, 
        "english": eng
    }


class CardBank:

    __num = -1
    cards = []
    estar_card = None

    def __init__(self, card_bank_filepath):
        assert isinstance(card_bank_filepath, str)
        assert os.path.exists(card_bank_filepath)
        self.cards = read(card_bank_filepath, build_forms=True)
        for card in self.cards:
            if card["inf"] == "estar":
                self.estar_card = card
        if not self.estar_card:
            raise Exception("No card found for 'estar' (to be)")

    def __len__(self):
        return len(self.cards)
    
    def __iter__(self):
        return iter(self.cards)

    def __getitem__(self, i):
        return self.cards[i]

    def get(self, index):
        assert isinstance(index, int)
        return self.cards[index]

    def get_card(self, query):
        if isinstance(query, dict):
            return query
        if isinstance(query, int):
            return self.cards[query]
        if isinstance(query, str):
            for card in self.cards:
                if card["inf"] == query:
                    return card
            raise Exception("Could not find card for: {0}".format(query))
        raise Exception("Unknown card query for type: {0}".format(type(query)))

    def get_verbs(self, card, person=PERSON.FIRST, singular=True, tense=TENSE.INFINTIVE):
        assert person in PERSON_VALUES
        assert tense in TENSE_VALUES

        verbs = {
            "person": person, 
            "singular": singular, 
            "plural": not singular, 
            "tense": tense, 
            "english": {}, 
            "portuguese": {}
        }

        pronouns = get_pronouns(person=person, singular=singular)
        card = self.get_card(card)

        verbs["portuguese"]["infinitive"] = card["inf"]
        verbs["portuguese"]["verb"] = self.get_portuguese_verb(card, person=person, singular=singular, tense=tense)
        verbs["portuguese"]["pronoun"] = pronouns["portuguese"]

        # check 2nd person using 3rd form, in which case english still should use 2nd form
        if pronouns["portuguese"].startswith("você"):
            person = PERSON.SECOND

        verbs["english"]["infinitive"] = card["eng-inf"]
        verbs["english"]["hint"] = card["eng-hint"]
        verbs["english"]["verb"] = self.get_english_verb(card, person=person, singular=singular, tense=tense)
        verbs["english"]["pronoun"] = pronouns["english"]

        verbs["hint-to-eng"] = card["hint-to-eng"]

        return verbs

    def get_portuguese_verb(self, card, person=PERSON.FIRST, singular=True, tense=TENSE.INFINTIVE):
        assert person in PERSON_VALUES
        assert tense in TENSE_VALUES

        card = self.get_card(card)

        if tense == TENSE.INFINTIVE:
            return card["inf"]
        if tense == TENSE.PRESENT or tense == TENSE.PRESENT_CONTINUOUS:
            attr = "present-"
        else:
            raise Exception("Unknown or unsupported tense given")

        if person == PERSON.FIRST:
            attr += "1"
        elif person == PERSON.SECOND:
            attr += "2"
        elif person == PERSON.THIRD:
            attr += "3"
        else:
            raise Exception("Unknown person given")
        attr += "s" if singular else "p"

        if tense == TENSE.PRESENT_CONTINUOUS:
            return "{0} {1}".format(self.estar_card[attr], card["gerund"])
        else:
            return card[attr]

    def get_english_verb(self, card, person=PERSON.FIRST, singular=True, tense=TENSE.INFINTIVE):
        assert person in PERSON_VALUES
        assert tense in TENSE_VALUES

        card = self.get_card(card)

        if tense == TENSE.INFINTIVE:
            return card["eng-inf"]

        if tense == TENSE.PRESENT:
            if not singular or person == PERSON.SECOND:
                return card["eng-p"]
            if person == PERSON.FIRST:
                return card["eng-1"]
            if person == PERSON.THIRD:
                return card["eng-3"]

        elif tense == TENSE.PRESENT_CONTINUOUS:
            if not singular or person == PERSON.SECOND:
                return [
                    "{0} {1}".format(pick_one(self.estar_card["eng-p"]), gerund)
                    for gerund in card["eng-gerund"]
                ]
            if person == PERSON.FIRST:
                return [
                    "{0} {1}".format(pick_one(self.estar_card["eng-1"]), gerund)
                    for gerund in card["eng-gerund"]
                ]
            if person == PERSON.THIRD:
                return [
                    "{0} {1}".format(pick_one(self.estar_card["eng-3"]), gerund)
                    for gerund in card["eng-gerund"]
                ]

        else:
            raise Exception("{0} tense currently unsupported for english".format(TENSE_NAMES[tense]))

        raise Exception("Unknown person given")
