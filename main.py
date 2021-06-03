import math, random
from bin import tester
from bin.cardbank import CardBank
from bin.constants import TENSE


def main():
    bank = CardBank("bank/card-bank-built.csv", "bank/card-bank-similar.csv")

    num_cards = len(bank)
    num_tests = int(input("Number of words to test? (two questions per word) > "))
    if num_tests < 1:
        raise Exception("Must specify at least one test")
    elif num_tests > num_cards:
        num_tests = num_cards
        print("More tests than exists cards. Number of words set to max ({0}).".format(num_cards))

    print("")

    # get cards
    test_card_indices = random.sample(range(0, num_cards), k=num_tests)
    test_cards = []
    test_infs = []
    # add a few similars to test common mixups
    similars = []
    start_similars_at = math.ceil(num_tests*0.85)-1
    for n, i in enumerate(test_card_indices):
        card = None
        # add a few similars in the end, if applicable
        if n >= start_similars_at and len(similars):
            group = None
            while len(similars) and (not group or not len(group)):
                # pop off earliest group, clean up redundants
                group = [inf for inf in similars.pop(0) if inf not in test_infs]
            if group and len(group):
                card = bank[random.choice(group)]
        # if no similars, add from random list, add its similars
        if not card:
            card = bank[i]
            if "similars" in card and len(card["similars"]):
                similars.append(card["similars"])
        # add card
        test_cards.append(card)
        test_infs.append(card["inf"])

    # reshuffle
    random.shuffle(test_cards)

    tally = {
        "total": 0, 
        "correct": 0, 
        "wrong": 0, 
        "redo": []
    }
    for n, card in enumerate(test_cards):
        to_english = bool(random.getrandbits(1))
        exclude_tenses = []
        if card["inf"] == "poder":
            exclude_tenses = [TENSE.IMPERATIVE_AFM, TENSE.IMPERATIVE_NEG]

        print("Word {0} of {1}:".format(n+1, num_tests))

        tested = []
        wrong_params = []
        params = False
        redo = False
        for j in range(2):
            params = tester.get_params(no_repeats=tested, exclude_tenses=exclude_tenses)
            result = tester.question(bank, card, params, to_english)
            params["tense"] = result["tense"]
            params["person"] = result["person"]
            params["singular"] = result["singular"]
            tested.append(params)
            tally["total"] += 1
            if not result["correct"]:
                tally["wrong"] += 1
                redo = True
                params["to_english"] = to_english
                wrong_params.append(params)
                # don't retest present-continuous if corrected answered
                if params["tense"] == TENSE.PRESENT_CONTINUOUS:
                    exclude_tenses.append(params["tense"])
            else:
                tally["correct"] += 1
            # don't retest infinitive tense in any case
            if params["tense"] == TENSE.INFINITIVE:
                exclude_tenses.append(params["tense"])
            # don't retest in portuguese-to-english format in any case
            if to_english:
                to_english = False

        print("")

        if redo:
            tally["redo"].append([card, wrong_params])

    print("Words tested: {0}".format(num_tests))
    print("Total questions: {0}".format(tally["total"]))
    print("Total correct: {0}".format(tally["correct"]))
    print("Accuracy: {0:.0f}%".format(100*tally["correct"]/tally["total"]))

    print("")

    to_redo = tally["redo"]
    next_redo = []

    while len(to_redo):
        for n, (card, wrong_params) in enumerate(to_redo):
            tested = []
            params = False
            redo = False
            exclude_tenses = []

            if card["inf"] == "poder":
                exclude_tenses = [TENSE.IMPERATIVE_AFM, TENSE.IMPERATIVE_NEG]

            print("Redo word {0}:".format(n+1))

            # break conditions:
            # 1. At least 3 correct answers
            # 2. At least 2 correct in a row
            # 3. All wrong answers have been retested (minus to-english)
            streak = 2
            correct = 3
            new_incorrect = []
            while correct > 0 or streak > 0 or len(wrong_params) or len(new_incorrect):
                to_english = False
                was_retest = False
                if len(wrong_params):
                    params = wrong_params.pop(0)
                    to_english = "to_english" in params and params["to_english"]
                elif correct <= 0 and streak <= len(new_incorrect):
                    params = new_incorrect.pop(0)
                    was_retest = True
                else:
                    params = tester.get_params(no_repeats=tested, exclude_tenses=exclude_tenses)
                result = tester.question(bank, card, params, to_english)
                params["tense"] = result["tense"]
                params["person"] = result["person"]
                params["singular"] = result["singular"]
                if result["correct"]:
                    tested.append(params)
                    # don't retest certain tenses for this word, if correctly solved once
                    if params["tense"] == TENSE.PRESENT_CONTINUOUS or params["tense"] == TENSE.INFINITIVE:
                        exclude_tenses.append(params["tense"])
                    correct -= 1
                    streak -= 1
                else:
                    if not to_english and params not in new_incorrect:
                        new_incorrect.append(params)
                    streak = 2 if not was_retest else 1

            print("")

            if redo:
                next_redo.append(card)
                break

        to_redo = next_redo
        next_redo = []


if __name__ == "__main__":
    main()
