import sys, math, random
from bin import tester
from bin.cardbank import CardBank
from bin.constants import TENSE, TENSE_VALUES, TENSE_GROUPS


def main(options=None):
    options = options if options else {}

    # option to limit tenses to group specified
    default_tense_group = False
    default_exclude_tenses = []
    if "tense" in options:
        try:
            default_tense_group = getattr(TENSE_GROUPS, options["tense"].upper())
        except:
            raise Exception("Bad argument. Tense group '{0}' is invalid.".format(options["tense"]))
        default_exclude_tenses = [tense for tense in TENSE_VALUES if tense not in default_tense_group]

    # option to set num of questions
    num_questions = 2
    if default_tense_group == TENSE_GROUPS.INFINITIVE:
        num_questions = 1
    elif "num-questions" in options:
        num_questions = int(options["num-questions"])
        if num_questions < 1:
            raise Exception("Bad argument. Number of questions must be at least 1.")

    # read card bank
    bank = CardBank("bank/card-bank-built.csv", "bank/card-bank-similar.csv")

    # ask number of words to test
    num_cards = len(bank)
    num_tests = int(input("Number of words to test? ({0} questions per word) > ".format(num_questions)))
    if num_tests < 1:
        raise Exception("Must specify at least one test")
    elif num_tests > num_cards:
        num_tests = num_cards
        print("More tests than exists cards. Number of words set to max ({0}).".format(num_cards))

    print("")

    # get cards
    all_card_indices = range(0, num_cards)
    test_card_indices = random.sample(all_card_indices, k=num_tests)
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
            # special case to exclude (pick random replacement)
            if default_tense_group == TENSE_GROUPS.INFINITIVE and card["inf"] == "poder":
                card = None
                ibreak = 100
                while not card and ibreak > 0:
                    i = random.choice(all_card_indices)
                    ibreak -= 1
                    if i not in test_card_indices and bank[i]["inf"] not in test_infs:
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
        exclude_tenses = tester.get_exclude_tenses(card, default_exclude_tenses[:])

        print("Word {0} of {1}:".format(n+1, num_tests))

        tested = []
        wrong_params = []
        params = False
        redo = False
        for j in range(num_questions):
            # make sure we're not excluding everything..
            if len(exclude_tenses) == len(TENSE_VALUES):
                exclude_tenses = default_exclude_tenses[:]
            # test with random parameters
            params = tester.get_params(no_repeats=tested, exclude_tenses=exclude_tenses)
            result = tester.question(bank, card, params, to_english)
            # because test may change params, if they don't make sense, use latest before appending
            params["tense"] = result["tense"]
            params["person"] = result["person"]
            params["singular"] = result["singular"]
            # add to tally
            tested.append(params)
            tally["total"] += 1
            if not result["correct"]:
                tally["wrong"] += 1
                redo = True
                params["to_english"] = to_english
                wrong_params.append(params)
            else:
                tally["correct"] += 1
                # don't retest present-continuous if correctly answered
                if params["tense"] == TENSE.PRESENT_CONTINUOUS:
                    exclude_tenses.append(params["tense"])
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
    
    if "skip-retest" in options:
        return

    print("")

    to_redo = tally["redo"]
    next_redo = []

    while len(to_redo):
        for n, (card, wrong_params) in enumerate(to_redo):
            tested = []
            params = False
            redo = False
            exclude_tenses = tester.get_exclude_tenses(card, default_exclude_tenses[:])

            print("Redo word {0}:".format(n+1))

            # break conditions:
            # 1. At least 3 correct answers
            # 2. At least 2 correct in a row
            # 3. All wrong answers have been retested (minus to-english)
            streak = 2
            correct = 3
            new_incorrect = []
            while correct > 0 or streak > 0 or len(wrong_params) or len(new_incorrect):

                if len(exclude_tenses) == len(TENSE_VALUES):
                    exclude_tenses = default_exclude_tenses[:]

                to_english = False
                was_retest = False
                if len(wrong_params):
                    # start with wrong parameters from original test
                    params = wrong_params.pop(0)
                    to_english = "to_english" in params and params["to_english"]
                elif correct <= 0 and streak <= len(new_incorrect):
                    # if nearing break conditions, retest new incorrects from this retrest
                    params = new_incorrect.pop(0)
                    was_retest = True
                else:
                    # get new, random parameters
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
                    # de-increment towards break conditions
                    correct -= 1
                    streak -= 1
                else:
                    # add to resting incorrects (with some exceptions)
                    if not to_english and not was_retest:
                        new_incorrect.append(params)
                    # if on retests, can end up single streak, otherwise need to end on 2-streak
                    streak = 2 if not was_retest else 1

            print("")

            if redo:
                next_redo.append(card)
                break

        to_redo = next_redo
        next_redo = []


if __name__ == "__main__":
    args = {}
    rename = {
        "h": "help", 
        "t": "tense", 
        "n": "num-questions", 
        "s": "skip-retest"
    }
    in_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("-"):
            if in_arg:
                args[in_arg] = True
            in_arg = arg.lstrip("-").rstrip()
            if in_arg in rename:
                in_arg = rename[in_arg]
        else:
            args[in_arg] = arg.strip()
            in_arg = None
    if in_arg:
        args[in_arg] = True
    if "help" in args:
        print("""
------------------------------------------------------------------------------
Portuguese Verb Cards
------------------------------------------------------------------------------
Created this script to test Portuguese verbs as I didn't like most flash card
software. Test a set of randomly chosen Portuguese verbs in different forms 
and tenses. 

Answer checking rules:
  - Special characters are not required, and will be dynamically matched to 
    standard English vowel (though hint to mind the accents will appear).
  - Wrong answer due to synonym will be given one more chance to try again.
  - While there is some support for alternative helper verbs, generally stick
    to 'has', had', or 'have' (perfect); 'will' (future); 'would' (future 
    conditional); and 'must' or 'must not' (imperative).

The script may also be provided with a few special parameters. Parameter names
are prefixed by a hyphen. Parameters that require a value should be follow by 
the value passed as that parameter.

    -h | -help          What you're using right now! Shows help information.
    -t | -tense         To limit testing to a specific tense, follow with the 
                        tense group name. Recognized values are 'infinitive', 
                        'present', 'future', 'past', 'imperfect', 'perfect', 
                        and 'imperative'.
    -n | -num-questions Default num. of questions per word (not including  
                        retest section) is two. Use this to increase or 
                        decrease.
    -s | -skip-retest   Add this parameter to skip the retest portion.
""")
    else:
        main(args)
