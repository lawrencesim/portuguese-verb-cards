from .constants import *
from .misc import pick_one, compare_faster
import random


def random_parameters(exclude_tenses=None):
    '''Gets random parameters for verb form.
    Params:
        exclude_tenses (list[constant.TENSE], optional): If supplied, excludes these tenses from 
        consideration. Note if everything is excluded, then defaults to infintive.
    Returns:
        Dict with verb form parameters.
        - tense (constants.TENSE): Verb tense. Weighted to strongly prefer present tense over infinitive and 
          present-continuous.
        - singular (bool): True if singular form, False if plural.
        - person (constants.PERSON): Person. Weighted to prefer, from most to least, 3rd, 1st, 2nd. Note 3rd 
          form can result in Portuguese 'você[s]' in returned pronouns.
    '''
    tense_weights = list(DEFAULT_TENSE_WEIGHTS)
    if exclude_tenses:
        for exclude in exclude_tenses:
            tense_weights[TENSE_VALUES.index(exclude)] = 0
        weight_vals = tuple(set(tense_weights))
        if len(weight_vals) == 1 and weight_vals[0] == 0:
            weight_vals[0] = 1
    tense = random.choices(TENSE_VALUES, weights=tense_weights, k=1)[0]
    if tense == TENSE.INFINITIVE:
        return {
            "tense": tense, 
            "singular": True, 
            "person": PERSON.FIRST
        }
    singular = bool(random.getrandbits(1))
    pweights = [2,1,3]
    # 1st person singular imperative doesn't make sense
    if singular and (tense == TENSE.IMPERATIVE_AFM or tense == TENSE.IMPERATIVE_NEG):
        pweights[0] = 0
    return {
        "tense": tense, 
        "singular": singular, 
        "person": random.choices(PERSON_VALUES, weights=pweights, k=1)[0]
    }


def get_params(no_repeats=None, exclude_tenses=None):
    '''Get random parameters, with special constraints. Attempts to find unique parameters that satisfy these
    constraints in eight attempts, after which returns whatever latest parameters were, to avoid potential 
    infinite loop if constraints are too strict.
    Params:
        no_repeats (list[dict], optional): List of existing parameters. If supplied, 
        exclude_tenses (list[constant.TENSE], optional): If supplied, excludes these tenses from 
        consideration. Note if everything is excluded, then defaults to infintive.
    Returns:
        Dict with verb form parameters. See documentation for `random_parameters()` for details.
    '''
    variations = 8
    while variations > 0:
        params = random_parameters(exclude_tenses=exclude_tenses)
        variations -= 1
        if params and (not no_repeats or params not in no_repeats):
            break
    return params


def get_exclude_tenses(card, append_to=None):
    '''Get list of tenses to exclude. This is used to handle special cases of words that don't make sense in 
    certain tenses. E.g. 'poder' (to be) in imperative.
    Params:
        card (dict): ord/card definition from CardBank.
        append_to (list[constant.TENSE], optional): If supplied, existing list of tenses to append to
    Returns:
        List of tenses to exclude.
    '''
    exclude_tenses = append_to if append_to else []
    add_exclude = []

    # imperative doesn't make sense with 'to be able' (e.g. 'he must can')
    if card["inf"] == "poder":
        add_exclude = [TENSE.IMPERATIVE_AFM, TENSE.IMPERATIVE_NEG]
    # while technically possible, just awkward (e.g. 'I had had')
    elif card["inf"] == "ter" or card["inf"] == "haver":
        add_exclude = [TENSE.PERFECT]

    for exclude in add_exclude:
        if exclude not in exclude_tenses:
            exclude_tenses.append(exclude)
    return exclude_tenses


def question(cardbank, card, params, to_english):
    '''Ask question. Use this function as entry point to ask question.
    Params:
        cardbank (CardBank): CardBank instance.
        card (dict): Word/card definition from CardBank.
        params (dict): Verb form parameters with values for "person" (constants.PERSON), "singular" (bool), 
            and "tense" (constants.TENSE).
        to_english (bool): True is asking Portuguese-to-English translation. False for reverse.
    Returns:
        Results dict. See documentation for `english_to_portuguese()` or 
        `portuguese_to_english()` for details (same keys but slightly different value types).
    '''
    verbs = cardbank.get_verbs(
        card, 
        person=params["person"], 
        singular=params["singular"], 
        tense=params["tense"], 
        similars=(not to_english)
    )
    return _question(verbs, to_english)


def _question(verbs, to_english, dont_check_similars=False):
    '''Ask question. Split out to make recursion safe (logically, anyways). If the answer is deemed to be 
    wrong but understandable mistake with synonym, re-asks the question (only applies to questions in English-
    to-Portuguese).
    Params:
        verbs (dict): Verbs dictionary definition. See `cardbank.get_verbs()`.
        to_english (bool): True is asking Portuguese-to-English translation. False for reverse.
        dont_check_similars (bool): If True, doesn't allow mistakes for Portuguese synonyms. Only applicable 
            in English-to-Portuguese translations.
    Returns:
        Results dict. See documentation for `english_to_portuguese()` or 
        `portuguese_to_english()` for details (same keys but slightly different value types).
    '''
    result = portuguese_to_english(verbs) if to_english else english_to_portuguese(verbs)

    if result["correct"]:
        if to_english or result["guess"] in result["answers"]:
            print("Correct!")
        else:
            print("Correct! But mind the accent(s): {0}".format(answer_formatted(verbs, to_english)))
        return result
    
    if not to_english and not dont_check_similars and "similars" in verbs["portuguese"]:
        err_similar = False
        if result["guess"] in verbs["portuguese"]["similars"]:
            err_similar = True
        if not err_similar:
            for similar in verbs["portuguese"]["similars"]:
                if compare_faster(similar, result["guess"]):
                    err_similar = True
                    break
        if err_similar:
            print("Close! But you may be confusing the word with a similar synonym.")
            print("Check the hint (if available) and try again!")
            return _question(verbs, to_english, dont_check_similars=True)

    print("Wrong! The answer is: " + answer_formatted(verbs, to_english))
    return result


def english_to_portuguese(verbs):
    '''Ask question for Portuguese translation of English word.
    Params:
        verbs (dict): Verbs dictionary definition. See `cardbank.get_verbs()`.
    Returns:
        Results dict.
        - person (constants.PERSON): Person.
        - singular (bool): True if singular form, False if plural.
        - tense (constants.TENSE): Verb tense.
        - answers (tuple[str]): The correct answers (most of the time just one, but sometimes alt. spelling).
        - guess (str): User inputted guess (stripped and lowercased).
        - correct (bool): Whether answer was accepted.
    '''
    # certain english definitions are for answers only, remove from question construction choices
    pick_from = verbs["english"]["verbs"]
    if verbs["use-eng-defs"] and verbs["use-eng-defs"] < len(pick_from):
        pick_from = pick_from[:verbs["use-eng-defs"]]
    qverb = pick_one(pick_from)

    show_hint = False
    if verbs["hint"] and "from-eng" in verbs["hint-rules"]:
        # check index-selective rules
        index_selective = False
        qindex = verbs["english"]["verbs"].index(qverb)
        for i, order in enumerate(("first", "second", "third")):
            if "{0}-def".format(order) in verbs["hint-rules"]:
                index_selective = True
                if i == qindex:
                    show_hint = True
            if show_hint and index_selective:
                break
        # just generically show hint if no index-selective rule
        if not index_selective:
            show_hint = True

    prefix = [verbs["english"]["pronoun"]]
    answer_prefix = verbs["portuguese"]["pronoun"]
    if verbs["tense"] == TENSE.INFINITIVE:
        prefix = ["to"]
        answer_prefix = False
    elif verbs["tense"] == TENSE.PERFECT:
        prefix.append("had")
    elif verbs["tense"] == TENSE.FUTURE_SIMPLE:
        if not verbs["singular"] or verbs["person"] == PERSON.SECOND:
            prefix.append("are")
        elif verbs["person"] == PERSON.FIRST:
            prefix.append("am")
        else:
            prefix.append("is")
        prefix.append("going to")
    elif verbs["tense"] == TENSE.FUTURE_FORMAL:
        prefix.append("will")
    elif verbs["tense"] == TENSE.FUTURE_COND:
        prefix.append("would")
    elif verbs["tense"] == TENSE.IMPERATIVE_AFM:
        prefix.append("must")
    elif verbs["tense"] == TENSE.IMPERATIVE_NEG:
        prefix.append("must not")
        answer_prefix += "não"
    prompt = "{0} {1} {2}> {3}".format(
        " ".join(prefix), 
        qverb, 
        "({0}) ".format(verbs["hint"]) if show_hint else "", 
        answer_prefix + " " if answer_prefix else  ""
    )
    guess = input(prompt).strip().lower()

    return {
        "person":   verbs["person"], 
        "singular": verbs["singular"], 
        "plural":   verbs["plural"], 
        "tense":    verbs["tense"], 
        "answers":  verbs["portuguese"]["verbs"], 
        "guess":    guess, 
        "correct":  compare_faster(verbs["portuguese"]["verbs"], guess)
    }


def portuguese_to_english(verbs):
    '''Ask question for English translation of Portuguese word.
    Params:
        verbs (dict): Verbs dictionary definition. See `cardbank.get_verbs()`.
    Returns:
        Results dict.
        - person (constants.PERSON): Person.
        - singular (bool): True if singular form, False if plural.
        - tense (constants.TENSE): Verb tense.
        - answers (tuple[str]): The correct answers (can be more than one possible translation).
        - guess (str): User inputted guess (stripped and lowercased).
        - correct (bool): Whether answer was accepted.
    '''
    show_hint = False
    if verbs["hint"] and "to-eng" in verbs["hint-rules"]:
        show_hint = True

    aux_verbs = None
    aux_verbs_alt = None

    if verbs["tense"] == TENSE.INFINITIVE:
        prompt = "{0} {1}> to ".format(
            verbs["portuguese"]["infinitive"], 
            "({0}) ".format(verbs["hint"]) if show_hint else ""
        )

    else:
        if verbs["tense"] == TENSE.PERFECT:
            if verbs["singular"] and verbs["person"] == PERSON.THIRD:
                aux_verbs = (("has","had"),)
            else:
                aux_verbs = (("have","had"),)
        elif verbs["tense"] == TENSE.FUTURE_SIMPLE or verbs["tense"] == TENSE.FUTURE_FORMAL:
            aux_verbs = (("will",),)
            if verbs["tense"] == TENSE.FUTURE_SIMPLE:
                if not verbs["singular"] or verbs["person"] == PERSON.SECOND:
                    alt_to_be = "are"
                elif verbs["person"] == PERSON.FIRST:
                    alt_to_be = "am"
                else:
                    alt_to_be = "is"
                aux_verbs_alt = ((alt_to_be,),("going",),("to",))
        elif verbs["tense"] == TENSE.FUTURE_COND:
            aux_verbs = (("would"),)
        elif verbs["tense"] == TENSE.IMPERATIVE_AFM:
            aux_verbs = (("must","should"),)
        elif verbs["tense"] == TENSE.IMPERATIVE_NEG:
            aux_verbs = (("must","should"),("not",))
            aux_verbs_alt = (("mustn't","shouldn't"),)

        prompt = "{0} {1} {2}> {3} ".format(
            verbs["portuguese"]["pronoun"], 
            pick_one(verbs["portuguese"]["verbs"]), 
            "({0}) ".format(verbs["hint"]) if show_hint else "", 
            verbs["english"]["pronoun"]
        )
        
    guess = input(prompt).strip().lower()

    correct = False
    if not aux_verbs:
        # no aux. verbs, just compare raw answer
        correct = compare_faster(verbs["english"]["verbs"], guess)
    if aux_verbs:
        # split words
        response_parts = guess.split(" ")
        verb_parts = response_parts
        # check against first variation
        for check_aux_verbs in (aux_verbs, aux_verbs_alt):
            if len(response_parts)-1 != len(check_aux_verbs):
                continue
            incorrect = False
            for i, words_at_loc in enumerate(check_aux_verbs):
                if response_parts[i] not in words_at_loc:
                    incorrect = True
                    break
            if not incorrect:
                correct = True
                response_parts = response_parts[len(check_aux_verbs):]
                break
        # finally check verb itself without aux. verbs
        if correct:
            correct = compare_faster(verbs["english"]["verbs"], " ".join(response_parts))

    return {
        "person":   verbs["person"], 
        "singular": verbs["singular"], 
        "plural":   verbs["plural"], 
        "tense":    verbs["tense"], 
        "answers":  verbs["english"]["verbs"], 
        "guess":    guess, 
        "correct":  correct
    }


def answer_formatted(verbs, to_english):
    '''Format answer for printing.
    Params:
        verbs (dict): Verbs dictionary definition. See `cardbank.get_verbs()`.
        to_english (bool): True to return in English. False for Portuguese.
    Returns:
        The string, formatted answer.
    '''
    if to_english:
        prefix = verbs["english"]["pronoun"]
        if verbs["tense"] == TENSE.INFINITIVE:
            prefix = "to"
        elif verbs["tense"] == TENSE.PERFECT:
            prefix += " had"
        elif verbs["tense"] == TENSE.FUTURE_SIMPLE or verbs["tense"] == TENSE.FUTURE_FORMAL:
            prefix += " will"
        elif verbs["tense"] == TENSE.FUTURE_COND:
            prefix += " would"
        elif verbs["tense"] == TENSE.IMPERATIVE_AFM:
            prefix += " should"
        elif verbs["tense"] == TENSE.IMPERATIVE_NEG:
            prefix += " should not"
        return "{0} {1}".format(prefix, " (or) ".join(verbs["english"]["verbs"]))
    else:
        corrects = " (or) ".join(verbs["portuguese"]["verbs"])
        if verbs["tense"] == TENSE.INFINITIVE:
            return corrects
        elif verbs["tense"] == TENSE.IMPERATIVE_NEG:
            return "{0} não {1}".format(verbs["portuguese"]["pronoun"], corrects)
        else:
            return "{0} {1}".format(verbs["portuguese"]["pronoun"], corrects)
