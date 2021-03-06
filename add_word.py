import os, csv, shutil
from bin import ask, guess, cardbank, builder
from bin.constants import VOWELS
import build_card_bank


def main():
    # start with infinitive form
    print("Enter Portuguese infinitive:")
    infinitive = input("> ").strip().lower()

    # check if already exists in card bank
    bank = []
    existing = False
    if os.path.exists("bank/card-bank-basic.csv"):
        bank = cardbank.read("bank/card-bank-basic.csv", build_forms=False)
        for card in bank:
            if card["inf"] == infinitive:
                existing = True
                break
    if existing:
        # if existing, confirm overwriting/revising
        if not ask.yes_no("'{0}' already exists. Overwrite?".format(infinitive)):
            exit()
    else:
        # otherwise, check valid infinitive by checking conjugator website accepts it
        print("Checking '{0}' is valid (may take a second)..".format(infinitive))
        session = builder.session()
        page = session.get(builder.URL.format(infinitive))
        page.html.render()
        warning = page.html.find("#warning", first=True)
        page.close()
        session.close()
        if warning and warning.text:
            print("Infinitive ({0}) invalid {1}\n{2}".format(infinitive, warning.text, builder.URL.format(infinitive)))
            exit()

    # main definition create process in here
    card = create_word(infinitive)
    
    # add card, appending if new, replacing if overwriting
    if not existing:
        bank.append(card)
    else:
        revise = False
        for i, oldcard in enumerate(bank):
            if oldcard["inf"] == card["inf"]:
                bank[i] = card
                revise = True
                break
        if not revise:
            raise Exception("Could not find existing card for revision")

    print("")

    # backup card bank basic (card bank with all basic definitions but not built out)
    if os.path.exists("bank/card-bank-basic.csv"):
        shutil.copyfile("bank/card-bank-basic.csv", "bank/card-bank-basic.bkp.csv")
        print("Old word list backed up as: bank/card-bank-basic.bkp.csv")

    # write new card bank basic
    with open("bank/card-bank-basic.csv", "w", newline="", encoding="utf-8") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=builder.BASIC_FIELDS)
        writer.writeheader()
        writer.writerows(bank)
    print("New word list written to: bank/card-bank-basic.csv")

    print("")

    # now build and write completed card bank with new card
    build_card_bank.add_build([card])


def create_word(infinitive):
    '''Create word definition via user interactions.'''

    # get 1st person singular English forms and determine number of forms
    eng_1s = ask_forms(type_str="present 1st person", prefix="I")
    len_forms = len(eng_1s)

    # get 3rd person singular English forms, but use guess/default of just adding '-s' to each 1st person form
    eng_3s_guesses = [guess.eng_plural(form) for form in eng_1s]
    eng_3s = ask_forms(type_str="present 3rd person", prefix="s/he", guess_forms=eng_3s_guesses, expected_length=len_forms)

    # get plural English forms (also 2nd person), use guess/default of 1st person forms
    eng_p = ask_forms(type_str="present plural", prefix="we/you/they", guess_forms=eng_1s, expected_length=len_forms)

    # get infinitive forms, use guess/default of 1st person forms
    eng_inf = ask_forms(type_str="infinitive", prefix="to", guess_forms=eng_1s, expected_length=len_forms)
    infinitives = eng_inf if eng_inf else eng_1s

    # guess gerund forms, use guess/default by adding '-ing' to infinitives (with one heuristic of dropping 
    # last 'e')
    guess_gerunds = [guess.eng_gerund(inf) for inf in infinitives]
    gerunds = ask_forms(type_str="gerund", prefix="I am", guess_forms=guess_gerunds, expected_length=len_forms)

    # guess past forms with -ed suffix to present 1st person singular
    guess_past = [guess.eng_past(form) for form in eng_1s]
    eng_past = ask_forms(type_str="past", prefix="I", guess_forms=guess_past, expected_length=len_forms)

    # guess past perfect forms as same as past forms
    guess_past = eng_past if eng_past else guess_past
    eng_past_perf = ask_forms(type_str="past", prefix="had", guess_forms=guess_past, expected_length=len_forms)

    # Limit English definitions used for from-English questions. That is, all definitions can be accepted as 
    # answers when asking to translate to-English, but when asking to translate to-Portuguese, limit English 
    # forms allowed to form question with.
    use_english_defs = 0
    if len_forms > 1:
        if ask.yes_no("Do you want to limit English translations for question formation?"):
            use_english_defs = ask.integer(
                question="Up to which definition (by position) should be included? ({0})".format("/".join(infinitives)), 
                nonzero=True, 
                positive=True, 
                maxvalue=len_forms
            )
            if use_english_defs == len_forms:
                use_english_defs = 0

    # Define optional hint and hint rules. See `english_to_portuguese()` and `portuguese_to_english()` in 
    # bin.tester for details on hint rules as that's where it comes into play. But common rules are 'from-eng'
    # (for only showing hint in English-to-Portuguese questions) and 'first-def', 'second-def', etc. for only 
    # showing hints with certain English definitions when used in question.
    hint = ""
    hint_rules = []
    if ask.yes_no("Do you want to add a hint/clarification note?"):
        print("Enter hint/clarification note.")
        hint = input("> ").strip()
    if hint:
        hint_to_eng = False
        hint_from_eng = False
        if ask.yes_no("Show the hint/clarification note in translate-to-Portuguese questions?"):
            hint_rules.append("from-eng")
            hint_from_eng = True
        if ask.yes_no("Show the hint/clarification note in translate-to-English questions?"):
            hint_rules.append("to-eng")
            hint_to_eng = True
        # if both are true then no point as shown in both
        if hint_from_eng and hint_to_eng:
            hint_rules = []
        # limiting hints to certain defintions
        elif hint_from_eng and len(infinitives) and ask.yes_no("Limit hint being shown only to specific English translations?"):
            hint_rules += ask_limit_hints(infinitives)

    # double-check all parameters
    print("Does the following all look correct?")
    if True:
        print("  Portuguese infinitive       => {0}".format(infinitive))
        print("  Infinitive form(s)          => to {0}".format("/".join(infinitives)))
        print("  1st person form(s)          => I {0}".format("/".join(eng_1s)))
        print("  3rd person form(s)          => s/he {0}".format("/".join(eng_3s if eng_3s else eng_3s_guesses)))
        print("  Plural form(s)              => we {0}".format("/".join(eng_p if eng_p else eng_1s)))
        print("  Gerund form(s)              => I am {0}".format("/".join(gerunds if gerunds else guess_gerunds)))
        print("  Past form(s)                => I {0}".format("/".join(eng_past if eng_past else guess_past)))
        print("  Past perfect form(s)        => I had {0}".format("/".join(eng_past_perf if eng_past_perf else guess_past)))
    if use_english_defs:
        print("  Limit form(s) for questions => {0}".format("/".join(infinitives[:use_english_defs])))
    if hint:
        print("  Hint/clarification          => {0}".format(hint))
        print("  Hint rules                  => {0}".format(";".join(hint_rules)))

    # if confirmed, finish, otherwise recurse (starting over with infinitive)
    if ask.yes_no():
        return {
            "inf":           infinitive, 
            "hint":          hint, 
            "hint-rules":    ";".join(hint_rules), 
            "use-eng-defs":  use_english_defs if use_english_defs else "", 
            "eng-inf":       "/".join(eng_inf) if eng_inf else "", 
            "eng-gerund":    "/".join(gerunds) if gerunds else "", 
            "eng-1":         "/".join(eng_1s), 
            "eng-3":         "/".join(eng_3s) if eng_3s else "", 
            "eng-p":         "/".join(eng_p) if eng_p else "", 
            "eng-past":      "/".join(eng_past) if eng_past else "", 
            "eng-past-perf": "/".join(eng_past_perf) if eng_past_perf else ""
        }

    print("\nOkay, let's start over..\n")
    return create_word(infinitive=infinitive)


def ask_forms(type_str="", same_line=False, prefix="", guess_forms=None, expected_length=0, repeat=False):
    '''Ask verb forms question and parse input until acceptable answer given.'''
    if repeat:
        if isinstance(repeat, str):
            print(repeat)
    else:
        if not guess_forms:
            question = "Enter English {0} verb form[s] (add multiple separated by a forward-slash '/').".format(type_str)
        else:
            if len(guess_forms) == 1:
                question = "Does the following {0} verb form look correct?".format(type_str)
            else:
                question = "Do the following {0} verb forms look correct?".format(type_str)
            if prefix:
                question += "\n  {0} {1}".format(prefix, "/".join(guess_forms))
            else:
                question += "\n  {0}".format("/".join(guess_forms))
            if ask.yes_no(question):
                return ""
            question = "Enter unique {0} verb form[s] (add multiple separated by a forward-slash '/').".format(type_str)
        print(question)
    if prefix:
        input_forms = input("> {0} ".format(prefix))
    else:
        input_forms = input("> ")
    input_forms = [form.strip().lower() for form in input_forms.split("/")]
    input_forms = [form for form in input_forms if len(form)]
    if not input_forms:
        print("Invalid (empty) input, try again..")
        return ask_forms(expected_length=expected_length, repeat=question, prefix=prefix)
    if expected_length and len(input_forms) != expected_length:
        print("Invalid input length, {0} variations expected, try again..".format(expected_length))
        return ask_forms(expected_length=expected_length, repeat=question, prefix=prefix)
    return input_forms


def ask_limit_hints(infinitives):
    print("For which definitions (by number/position) do you want to limit it for? Type all that apply, separated by a comma, semicolon, or space.")
    print("  " + ", ".join("({0}) {1}".format(i+1, form) for i, form in enumerate(infinitives)))
    responses = input("> ").replace(";", " ").replace(",", " ").strip().lower().split()
    try:
        responses = list(set(int(x) for x in responses))
    except:
        print("Could not interpret response, make sure answers are numbers.")
        return ask_limit_hints(infinitives)
    num_defs = len(infinitives)
    if any(x <= 0 for x in responses):
        print("Invalid position found. Position values must be > 0.")
        return ask_limit_hints(infinitives)
    if any(x > num_defs for x in responses):
        print("Invalid position found. Position value found greater than length of definitions.")
        return ask_limit_hints(infinitives)
    add_rules = []
    hint_names_by_pos = ["", "first-def", "second-def", "third-def", "fourth-def", "fifth-def"]
    for x in responses:
        if x in hint_names_by_pos:
            add_rules += hint_names_by_pos[x]
    return add_rules


if __name__ == "__main__":
    main()
