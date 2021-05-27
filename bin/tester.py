from .constants import *
from .misc import pick_one, compare
import random


def random_parameters():
    tense = random.choices(TENSE_VALUES, weights=[1,4,1], k=1)[0]
    if tense == TENSE.INFINTIVE:
        return {
            "tense": tense, 
            "singular": True, 
            "person": PERSON.FIRST
        }
    return {
        "tense": tense, 
        "singular": bool(random.getrandbits(1)), 
        "person": random.choices(PERSON_VALUES, weights=[2,1,3], k=1)[0]
    }


def get_params(no_repeats=None, no_continuous=False):
    variations = 4
    while variations > 0:
        params = random_parameters()
        if no_continuous and params["tense"] == TENSE.PRESENT_CONTINUOUS:
            params["tense"] = TENSE.PRESENT
        variations -= 1
        if params and (not no_repeats or params not in no_repeats):
            break
    return params


def question(cardbank, card, params, to_english):
    verbs = cardbank.get_verbs(
        card, 
        person=params["person"], 
        singular=params["singular"], 
        tense=params["tense"]
    )
    if to_english:
        result = portuguese_to_english(verbs)
    else:
        result = english_to_portuguese(verbs)
    if result["correct"]:
        if result["guess"] in result["answer"]:
            print("Correct!")
        else:
            print("Correct! But mind the accent(s): {0}".format(result["answer_format"]))
    else:
        print("Wrong! The answer is: " + result["answer_format"])
    return result


def english_to_portuguese(verbs):
    if verbs["tense"] == TENSE.INFINTIVE:
        if verbs["english"]["hint"]:
            guess = input("{0} ({1}) > (inf.) ".format(
                pick_one(verbs["english"]["infinitive"]), 
                verbs["english"]["hint"]
            ))
        else:
            guess = input("{0} > (inf.) ".format(pick_one(verbs["english"]["infinitive"])))
    else:
        if verbs["english"]["hint"]:
            guess = input("{0} {1} ({2}) > {3} ".format(
                verbs["english"]["pronoun"], 
                pick_one(verbs["english"]["verb"]), 
                verbs["english"]["hint"], 
                verbs["portuguese"]["pronoun"]
            ))
        else:
            guess = input("{0} {1} -- {2} ".format(
                verbs["english"]["pronoun"], 
                pick_one(verbs["english"]["verb"]), 
                verbs["portuguese"]["pronoun"]
            ))
    guess = guess.lower()
    return {
        "person": verbs["person"], 
        "singular": verbs["singular"], 
        "plural": verbs["plural"], 
        "tense": verbs["tense"], 
        "verbs": verbs, 
        "guess": guess, 
        "answer": verbs["portuguese"]["verb"], 
        "answer_format": (
            ("" if verbs["tense"] == TENSE.INFINTIVE else verbs["portuguese"]["pronoun"] + " ") + 
            verbs["portuguese"]["verb"]
        ), 
        "correct": compare(verbs["portuguese"]["verb"], guess)
    }


def portuguese_to_english(verbs):
    if verbs["tense"] == TENSE.INFINTIVE:
        if verbs["english"]["hint"] and verbs["hint-to-eng"]:
            guess = input("{0} ({1}) > to ".format(verbs["portuguese"]["infinitive"], verbs["english"]["hint"]))
        else:
            guess = input("{0} > to ".format(verbs["portuguese"]["infinitive"]))
    elif verbs["english"]["hint"] and verbs["hint-to-eng"]:
        guess = input("{0} {1} ({2}) > {3} ".format(
            verbs["portuguese"]["pronoun"], 
            verbs["portuguese"]["verb"], 
            verbs["english"]["hint"], 
            verbs["english"]["pronoun"]
        ))
    else:
        guess = input("{0} {1} -- {2} ".format(
            verbs["portuguese"]["pronoun"], 
            verbs["portuguese"]["verb"], 
            verbs["english"]["pronoun"]
        ))
    guess = guess.lower()
    answer = verbs["english"]["verb"]
    if verbs["tense"] == TENSE.INFINTIVE:
        answer = [a.split(" ")[1:] for a in answer]
    return {
        "person": verbs["person"], 
        "singular": verbs["singular"], 
        "plural": verbs["plural"], 
        "tense": verbs["tense"], 
        "verbs": verbs, 
        "guess": guess, 
        "answer": answer, 
        "answer_format": (
            ("to " if verbs["tense"] == TENSE.INFINTIVE else verbs["english"]["pronoun"]) + " " +
            " (or) ".join(answer)
        ), 
        "correct": compare(answer, guess)
    }