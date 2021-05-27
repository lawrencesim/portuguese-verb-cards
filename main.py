import random
from bin import tester
from bin.cardbank import CardBank
from bin.constants import TENSE


def main():
    bank = CardBank("card-bank-built.csv")

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
        tested_continuous = False

        print("Word test {0} of {1}:".format(n, num_tests))

        for j in range(2):
            params = tester.get_params(no_repeats=tested, no_continuous=tested_continuous)
            result = tester.question(bank, i, params, to_english)
            tested.append(params)
            if params["tense"] == TENSE.PRESENT_CONTINUOUS:
                tested_continuous = True
            tally["total"] += 1
            if not result["correct"]:
                tally["wrong"] += 1
                redo = True
                wrong_params.append(params)
            else:
                tally["correct"] += 1
            if to_english:
                to_english = False

        print("")

        if redo:
            tally["redo"].append([bank[i], wrong_params])

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
            tested_continuous = False

            print("Redo word test {0}:".format(n))

            streak = 2
            correct = 3
            while correct > 0 or streak > 0:
                if not to_english and len(wrong_params):
                    params = wrong_params.pop(0)
                else:
                    params = tester.get_params(no_repeats=tested, no_continuous=tested_continuous)
                result = tester.question(bank, card, params, to_english)
                if result["correct"]:
                    tested.append(params)
                    if params["tense"] == TENSE.PRESENT_CONTINUOUS:
                        tested_continuous = True
                    correct -= 1
                    streak -= 1
                else:
                    streak = 2
                if to_english:
                    to_english = False

            print("")

            if redo:
                next_redo.append(card)
                break

        to_redo = next_redo
        next_redo = []


if __name__ == "__main__":
    main()
