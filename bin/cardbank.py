from .constants import *
from . import guess
import os, csv, random



def read(card_bank_filepath, build_forms=True):
    '''Reads a CSV of card bank definitions and converts to list of dict types.
    Params:
        card_bank_filepath (str): Filepath to CSV.
        build_forms (bool, optional): If true, builds additional fields that are dynamic generated.
    Returns:
        List of word definitions (as list[dict]).
    '''
    card_bank = []
    with open(card_bank_filepath, "r", encoding="utf-8") as csvf:
        reader = csv.DictReader(csvf)
        card_bank = [card for card in reader if "inf" in card]

    if not build_forms:
        return card_bank

    for card in card_bank:
        # question formation and answer hint rules
        card["use-eng-defs"] = int(card["use-eng-defs"]) if card["use-eng-defs"] else 0
        if card["hint-rules"]:
            card["hint-rules"] = tuple(s.strip().lower() for s in card["hint-rules"].split(";"))
        else:
            card["hint-rules"] = tuple()
        # split by multiple forms
        card["eng-1"] = tuple(s.strip().lower() for s in card["eng-1"].split("/"))
        # split existing, or same as singular from singular 1st person forms
        if card["eng-inf"]:
            card["eng-inf"] = tuple(s.strip().lower() for s in card["eng-inf"].split("/"))
        else:
            card["eng-inf"] = card["eng-1"]
        # split existing, or dynamically create from singular 1st person forms
        if card["eng-3"]:
            card["eng-3"] = tuple(s.strip().lower() for s in card["eng-3"].split("/"))
        else:
            card["eng-3"] = tuple(guess.eng_plural(form) for form in card["eng-1"])
        # split existing, or same as singular 1st person forms
        if card["eng-p"]:
            card["eng-p"] = tuple(s.strip().lower() for s in card["eng-p"].split("/"))
        else:
            card["eng-p"] = card["eng-1"]
        # split existing, or dynamically create from singular 1st person forms
        if card["eng-past"]:
            card["eng-past"] = tuple(s.strip().lower() for s in card["eng-past"].split("/"))
        else:
            card["eng-past"] = tuple(guess.eng_plural(form) for form in card["eng-1"])
        # split existing, or same as standard past forms
        if card["eng-past-perf"]:
            card["eng-past-perf"] = tuple(s.strip().lower() for s in card["eng-past-perf"].split("/"))
        else:
            card["eng-past-perf"] = card["eng-past"]
        # split existing, or dynamically create from infinitive forms
        if card["eng-gerund"]:
            card["eng-gerund"] = tuple(s.strip().lower() for s in card["eng-gerund"].split("/"))
        else:
            card["eng-gerund"] = tuple(guess.eng_gerund(form) for form in card["eng-inf"])

    return card_bank


def get_pronouns(person=PERSON.FIRST, singular=True):
    '''Get pronoun forms. If multiple choices, picks one. Note that 3rd-person could result in 'você[s]' which
    Then appropriate maps to return 2nd person English form.
    Params:
        person (constants.PERSON): Which person to construct pronoun form for. Defaults to PERSON.FIRST.
        singular (bool): Defaults to True.
    Returns:
        Dictionary with "english" and "portuguese" pronoun forms.
    '''
    por = PRONOUNS[0 if singular else 1]
    eng = ENG_PRONOUNS[0 if singular else 1]
    # 1st and 2nd person only have one form
    if person == PERSON.FIRST or person == PERSON.SECOND:
        return {
            "portuguese": por[person], 
            "english": eng[person]
        }
    if person != PERSON.THIRD:
        raise Exception("Unknown person given")
    # 3rd person via random choice
    por = random.choice(por[3][1:])
    # check second person using 2nd form, if singular match pronoun gender, or plural is basic
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
    '''
    Card bank and handler. Is iterable. Can be accessed like list/tuple or dictionary by index or key value 
    (using Portuguese infinitive verb form).

    Params:
        card_bank_table (str): Filepath to CSV defining card bank.
        similar_table (str, optional): Optional filepath to CSV defining Portuguese synonyms.

    Attributes:
        [Note: attributes generally shouldn't be accessed or modified directly.]
        cards (tuple[dict]): Tuple of word cards.
        card_map (dict):  Dictionary of word cards by Portuguese infinitive.
        estar_card (dict): Card for 'estar', necessary for building other verb forms in certain tenses.
        similars (tuple[tuple[str]]): Similar groups of synonyms in Portuguese.
    '''
    cards = tuple()
    card_map = {}
    estar_card = None
    ir_card = None
    similars = tuple()

    def __init__(self, card_bank_table, similar_table=None):
        # read cards
        assert isinstance(card_bank_table, str)
        assert os.path.exists(card_bank_table)
        self.cards = tuple(read(card_bank_table, build_forms=True))
        # find estar and ir cards, needed for continuous and simple-future forms respectively
        for card in self.cards:
            self.card_map[card["inf"]] = card
            if card["inf"] == "estar":
                self.estar_card = card
            elif card["inf"] == "ir":
                self.ir_card = card
        if not self.estar_card:
            raise Exception("No card found for 'estar' (to be)")
        if not self.ir_card:
            raise Exception("No card found for 'ir' (to go)")
        # read similars, removing missing verbs from group
        if similar_table:
            assert isinstance(similar_table, str)
            assert os.path.exists(similar_table)
            similars = []
            with open(similar_table, "r", encoding="utf-8") as csvf:
                reader = csv.reader(csvf)
                for group in reader:
                    missing_infs = []
                    for infinitive in group:
                        if not infinitive in self.card_map:
                            missing_infs.append(infinitive)
                    for missing_inf in missing_infs:
                        group.remove(missing_inf)
                    similars.append(group)
            self.similars = tuple(tuple(group) for group in similars)
            # create/append similars to verb cards
            for group in self.similars:
                for infinitive in group:
                    if "similars" not in self.card_map[infinitive]:
                        self.card_map[infinitive]["similars"] = group
                    else:
                        self.card_map[infinitive]["similars"] = tuple(set(self.card_map[infinitive]["similars"] + group))
            # filter out same from similars attached to each card
            for card in self.cards:
                if "similars" in card:
                    card["similars"] = tuple(verb for verb in card["similars"] if verb != card["inf"])

    def __len__(self):
        return len(self.cards)
    
    def __iter__(self):
        return iter(self.cards)

    def __getitem__(self, i):
        if isinstance(i, int):
            return self.cards[i]
        if isinstance(i, str):
            return self.card_map[i]
        raise TypeError()

    def get(self, query):
        '''Get word card/definition.
        Params:
            query (int|str|dict): Either the index or infinitive form to search for the card by. Or if a 
                dict is given, assumes that is the card so returns itself.
        Returns:
            Dict with word card definitions.
        '''
        if isinstance(query, int):
            return self.cards[query]
        if isinstance(query, str):
            return self.card_map[query]
        if isinstance(query, dict):
            if query and query in self.cards:
                return query
            else:
                raise ValueError()
        raise TypeError()

    def get_verbs(self, card, person=PERSON.FIRST, singular=True, tense=TENSE.INFINITIVE, similars=False):
        '''Get verb definition. This includes the parameters, the English and Portuguese equivalents, hints, 
        hint rules, and other relevant information to create a test question. Note that supplied form 
        parameters will be automically changed if invalid (see returned dict).
        Params:
            card (dict): The word definition dict.
            person (constants.PERSON): The person to construct the verb form with. Defaults to PERSON.FIRST.
            singular (bool): Whether singular or plural form. Defaults to True.
            tense (constants.TENSE): The tense to construct the verb form for. Defaults to TENSE.INFINITIVE. 
                Note 'você[s]' may be result of 3rd person, but returned value will denote 2nd person.
            similars (bool, optional): If true, also pulls Portuguese synonyms. Defaults to False.
        Returns:
            Dict with verb definitions.
            - person (constants.PERSON): Person of verb form. Note 'você[s]' will be considered 2nd person but
              using 3rd person form in Portuguese.
            - singular (bool): True if singular form.
            - plural (bool): True if plural form.
            - tense (constants.TENSE): Tense of verb form.
            - portuguese (dict)
                - infinitive (str): Portuguese infinitive.
                - verb (str): Portuguese verb form.
                - pronoun (str): Portuguese pronoun.
                - [similars] (tuple[str]): If supplied, list of synonyms in equivalent verb form.
            - english (dict)
                - infinitive (tuple[str]): Tuple of all English translation infinitive forms.
                - verb (tuple[str]): Tuple of all English translation verb forms.
                - pronoun (str): English pronoun.
            - hint (str): Hint.
            - hint-rules (tuple[str]): Tuple of rules for showing hints.
            - use-eng-defs (int): Limits which English translations to use to form questions. A value of 0 
              means all English translations can be used to form an English-to-Portuguese question. Any 
              positive value means only up to this variation. E.g. if there are two translations allowed for
              translating Portuguese as looser translation, but only first, stricter translation should be 
              used to form a question asking for Portuguese translation.
        '''
        assert person in PERSON_VALUES
        assert tense in TENSE_VALUES

        # 1st person singular imperative is invalid, default to 2nd person singular
        if (tense == TENSE.IMPERATIVE_AFM or tense == TENSE.IMPERATIVE_NEG) and person == PERSON.FIRST and singular:
            person = PERSON.SECOND

        card = self.get(card)

        # special case, only makes sense in infinitive or third person
        special_case = False
        if card["inf"] == "acontecer":
            if tense != TENSE.INFINITIVE:
                special_case = True
                person = PERSON.THIRD
                singular = True

        verbs = {
            "person": person, 
            "singular": singular, 
            "plural": not singular, 
            "tense": tense, 
            "english": {}, 
            "portuguese": {}
        }
        pronouns = None

        # special case, only makes sense with 'it'
        if special_case:
            if card["inf"] == "acontecer":
                pronouns = {
                    "portuguese": "ele", 
                    "english": "it"
                }

        if not pronouns:
            pronouns = get_pronouns(person=person, singular=singular)

        verbs["portuguese"]["infinitive"] = card["inf"]
        verbs["portuguese"]["verbs"] = self.get_portuguese_verb(card, person=person, singular=singular, tense=tense)
        verbs["portuguese"]["pronoun"] = pronouns["portuguese"]

        if similars and "similars" in card and len(card["similars"]):
            verbs["portuguese"]["similars"] = tuple(
                self.get_portuguese_verb(self.card_map[inf], person=person, singular=singular, tense=tense)
                for inf in card["similars"]
                if inf != card["inf"]
            )

        # check 2nd person using 3rd form, in which case english still should use 2nd form
        # note pronouns already checked/adjusted for this in get_pronouns()
        if pronouns["portuguese"].startswith("você"):
            person = PERSON.SECOND

        verbs["english"]["infinitive"] = card["eng-inf"]
        verbs["english"]["verbs"] = self.get_english_verb(card, person=person, singular=singular, tense=tense)
        verbs["english"]["pronoun"] = pronouns["english"]

        verbs["hint"] = card["hint"]
        verbs["hint-rules"] = card["hint-rules"]
        verbs["use-eng-defs"] = card["use-eng-defs"]

        return verbs

    def get_portuguese_verb(self, card, person=PERSON.FIRST, singular=True, tense=TENSE.INFINITIVE):
        '''Get verb form in Portuguese.
        Params:
            card (dict): The word definition dict.
            person (constants.PERSON): The person to construct the verb form with. Defaults to PERSON.FIRST.
            singular (bool): Whether singular or plural form. Defaults to True.
            tense (constants.TENSE): The tense to construct the verb form for. Defaults to TENSE.INFINITIVE.
        Returns:
            The Portuguese verb form.
        '''
        assert person in PERSON_VALUES
        assert tense in TENSE_VALUES

        card = self.get(card)

        imperative = False
        if tense == TENSE.INFINITIVE:
            # return as tuple, but leave original infinitive unchanged
            return (card["inf"],)
        if tense == TENSE.PRESENT or tense == TENSE.PRESENT_CONTINUOUS:
            attr = "present-"
        elif tense == TENSE.IMPERFECT or tense == TENSE.IMPERFECT_CONTINUOUS:
            attr = "imperfect-"
        elif tense == TENSE.PERFECT:
            attr = "perfect-"
        elif tense == TENSE.FUTURE_SIMPLE:
            attr = "present-"
        elif tense == TENSE.FUTURE_FORMAL:
            attr = "future-"
        elif tense == TENSE.FUTURE_COND:
            attr = "futcond-"
        elif tense == TENSE.IMPERATIVE_AFM:
            imperative = True
            attr = "imp1-"
        elif tense == TENSE.IMPERATIVE_NEG:
            # helper word 'não' will be included in answer prompt
            imperative = True
            attr = "imp0-"
        else:
            raise Exception("Unknown or unsupported tense given")

        # can/able doesn't have imperative form
        if imperative and card["inf"] == "poder":
            raise Exception("No imperative form of 'poder' (to be able)")

        if person == PERSON.FIRST:
            if imperative and singular:
                raise Exception("Invalid form - imperative 1st person singular")
            attr += "1"
        elif person == PERSON.SECOND:
            attr += "2"
        elif person == PERSON.THIRD:
            attr += "3"
        else:
            raise Exception("Unknown person given")
        attr += "s" if singular else "p"

        if tense == TENSE.PRESENT_CONTINUOUS or tense == TENSE.IMPERFECT_CONTINUOUS:
            # in continuous forms, estar aux. verb required, always return tuple
            return ("{0} {1}".format(self._get_verb(self.estar_card, attr)[0], card["gerund"]),)
        elif tense == TENSE.FUTURE_SIMPLE:
            # ir + infinitive
            return ("{0} {1}".format(self._get_verb(self.ir_card, attr)[0], card["inf"]),)
        else:
            return self._get_verb(card, attr)

    def _get_verb(self, card, attr):
        '''Ensures all verbs returned as tuple. Note not necessary for English and building dynamic forms 
        already checks for this.
        Params:
            card (dict): The word definition dict.
            attr (str): Key to retrieve from card.
        Returns:
            Tuple of string verb forms.
        '''
        if isinstance(card[attr], str):
            card[attr] = tuple(card[attr].split("/"))
        return card[attr]

    def get_english_verb(self, card, person=PERSON.FIRST, singular=True, tense=TENSE.INFINITIVE):
        '''Get verb forms in English. Note, all possible translations given, so result will be a tuple.
        Params:
            card (dict): The word definition dict.
            person (constants.PERSON): The person to construct the verb form with. Defaults to PERSON.FIRST.
            singular (bool): Whether singular or plural form. Defaults to True.
            tense (constants.TENSE): The tense to construct the verb form for. Defaults to TENSE.INFINITIVE.
        Returns:
            The English verb form(s). Note this will return a tuple[str], even if only one form, for different
            possible translations. Note that aux. verbs (e.g. had/will/should) will not be included so that 
            tester code can check variations of acceptable answers (e.g. had/have or should/must). This does 
            not apply to 'to be' (always included) needed in special cases (e.g. 'was able') and continuous 
            forms (e.g. 'are eating').
        '''
        assert person in PERSON_VALUES
        assert tense in TENSE_VALUES

        card = self.get(card)

        if tense == TENSE.INFINITIVE:
            # 'to' prefix will be included in answer prompt (portuguese infinitives are obvious)
            return card["eng-inf"]

        elif tense == TENSE.PRESENT:
            if not singular or person == PERSON.SECOND:
                return card["eng-p"]
            if person == PERSON.FIRST:
                return card["eng-1"]
            if person == PERSON.THIRD:
                return card["eng-3"]

        elif tense >= TENSE.FUTURE_SIMPLE and tense <= TENSE.FUTURE_COND:
            # future always uses singular forms
            # aux. verbs will be checked elsewhere for future tenses (will/would)
            # special case for 'to be' or 'to be able'
            if card["inf"] in ("ser", "estar", "poder"):
                return card["eng-inf"]
            else:
                return card["eng-1"]

        elif tense == TENSE.IMPERFECT:
            if not singular or person == PERSON.SECOND:
                forms = list(card["eng-past"])
                # special case cause only one instance I know where past singular/plural differs
                for i, form in enumerate(forms):
                    words = form.split(" ")
                    for j, word in enumerate(words):
                        if word == "is":
                            words[j] = "are"
                        elif word == "are":
                            words[j] = "were"
                    forms[i] = " ".join(words)
            return tuple(forms)

        elif tense == TENSE.PERFECT:
            # aux. verb will be checked elsewhere for perfect tense (had)
            return card["eng-past-perf"]

        elif tense == TENSE.PRESENT_CONTINUOUS:
            # aux. verb required, e.g. "am/is/are eating"
            if not singular or person == PERSON.SECOND:
                return tuple(
                    "{0} {1}".format(self.estar_card["eng-p"][0], gerund)
                    for gerund in card["eng-gerund"]
                )
            if person == PERSON.FIRST:
                return tuple(
                    "{0} {1}".format(self.estar_card["eng-1"][0], gerund)
                    for gerund in card["eng-gerund"]
                )
            if person == PERSON.THIRD:
                return tuple(
                    "{0} {1}".format(self.estar_card["eng-3"][0], gerund)
                    for gerund in card["eng-gerund"]
                )

        elif tense == TENSE.IMPERFECT_CONTINUOUS:
            # aux. verb required, e.g. "was/were working"
            if not singular or person == PERSON.SECOND:
                return tuple(
                    "{0} {1}".format(self.estar_card["eng-past-p"][0], gerund)
                    for gerund in card["eng-gerund"]
                )
            if person == PERSON.FIRST:
                return tuple(
                    "{0} {1}".format(self.estar_card["eng-past-1"][0], gerund)
                    for gerund in card["eng-gerund"]
                )
            if person == PERSON.THIRD:
                return tuple(
                    "{0} {1}".format(self.estar_card["eng-past-3"][0], gerund)
                    for gerund in card["eng-gerund"]
                )

        elif tense == TENSE.IMPERATIVE_AFM or tense == TENSE.IMPERATIVE_NEG:
            # aux. verb will be checked elsewhere (must/must not/should/should not)
            return card(["eng-p"])

        else:
            raise Exception("{0} tense currently unsupported for english".format(TENSE_NAMES[tense]))

        raise Exception("Unknown person given")
