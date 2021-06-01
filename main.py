import random
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

    test_card_indices = random.sample(range(0, num_cards), k=num_tests)
    tally = {
        "total": 0, 
        "correct": 0, 
        "wrong": 0, 
        "redo": []
    }
    n = 0
    for i in test_card_indices:
        n += 1
        tested = []
        params = False
        redo = False
        wrong_params = []
        to_english = bool(random.getrandbits(1))
        exclude_tenses = []

        card = bank[i]
        if card["inf"] == "poder":
            exclude_tenses = [TENSE.IMPERATIVE_AFM, TENSE.IMPERATIVE_NEG]

        print("Word {0} of {1}:".format(n, num_tests))

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
        n = 0

        for card, wrong_params in to_redo:
            n += 1
            tested = []
            params = False
            redo = False
            exclude_tenses = []

            if card["inf"] == "poder":
                exclude_tenses = [TENSE.IMPERATIVE_AFM, TENSE.IMPERATIVE_NEG]

            print("Redo word {0}:".format(n))

            # min. of 3 correct answers, but must end on a streak of at least 2 correct in a row
            streak = 2
            correct = 3
            while correct > 0 or streak > 0:
                to_english = False
                if len(wrong_params):
                    params = wrong_params.pop(0)
                    to_english = params["to_english"]
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
                    streak = 2

            print("")

            if redo:
                next_redo.append(card)
                break

        to_redo = next_redo
        next_redo = []


if __name__ == "__main__":
    main()
