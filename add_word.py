import os, csv
from bin import cardbank
from bin import builder


def ask_yes_no(question=""):
    if question:
        print(question)
    response = input("> ").strip().lower()
    if len(response) == 1:
        if response == "y":
            return True
        if response == "n":
            return False
    else:
        if response == "yes":
            return True
        if response == "no":
            return False
    print("Could not understand input, type `yes` or `no`.")
    return ask_yes_no(question)


print("Enter Portuguese infinitive:")
infinitive = input("> ").strip().lower()

bank = []
existing = False
if os.path.exists("card-bank-basic.csv"):
    bank = cardbank.read("card-bank-basic.csv", build_forms=False)
    for card in bank:
        if card["inf"] == infinitive:
            existing = True
            break
if existing:
    if not ask_yes_no("'{0}' already exists in card bank. Overwrite?".format(infinitive)):
        exit()
else:
    print("Checking '{0}' is valid..".format(infinitive))
    session = builder.session()
    page = session.get(builder.URL.format(infinitive))
    page.html.render()
    warning = page.html.find("#warning", first=True)
    if warning and warning.text:
        print("Infinitive ({0}) invalid {1}\n{2}".format(infinitive, warning.text, URL.format(infinitive)))
        exit()
    session = None


def ask_forms(type_str="", prefix="", guess_forms=None, expected_length=0, repeat=False):
    if repeat:
        if isinstance(repeat, str):
            print(repeat)
    else:
        if not guess_forms:
            question = "Enter English {0} verb form (add multiple separated by a forward-slash '/').".format(type_str)
        else:
            if len(guess_forms) == 1:
                question = "Does the following {0} verb form look correct?".format(type_str)
            else:
                question = "Do the following {0} verb forms look correct?".format(type_str)
            if prefix:
                question += "\n  {0} {1}".format(prefix, "/".join(guess_forms))
            else:
                question += "\n  {0}".format("/".join(guess_forms))
            if ask_yes_no(question):
                return ""
            question = "Enter unique {0} verb form[s] (add multiple separated by a forward-slash '/').".format(type_str)
        print(question)
    if prefix:
        forms = input("> {0} ".format(prefix))
    else:
        forms = input("> ")
    forms = [form.strip() for form in forms.split("/")]
    forms = [form for form in forms if len(form)]
    if not forms:
        print("Invalid input(s), try again..")
        return ask_forms(expected_length=expected_length, repeat=question)
    if expected_length and len(forms) != expected_length:
        print("Invalid input length, {0} variations expected, try again..".format(len(expected_length)))
        return ask_forms(expected_length=expected_length, repeat=question)
    return forms


eng_1s = ask_forms(type_str="present 1st person", prefix="I")
len_forms = len(eng_1s)

eng_3s_guesses = [form+"s" for form in eng_1s]
eng_3s = ask_forms(type_str="present 3rd person", prefix="s/he", guess_forms=eng_3s_guesses, expected_length=len_forms)

eng_p = ask_forms(type_str="present plural", prefix="we/you/they", guess_forms=eng_1s, expected_length=len_forms)

eng_inf = ask_forms(type_str="infinitive", prefix="to", guess_forms=eng_1s, expected_length=len_forms)

guess_gerunds = []
infinitives = eng_inf if eng_inf else eng_1s
for form in infinitives:
    gerund = form
    if len(gerund) >= 3 and gerund[-1] == "e" and gerund[-2] != "e":
        gerund = gerund[:-1]
    gerund = gerund + "ing"
    guess_gerunds.append(gerund)
gerunds = ask_forms(type_str="gerund", prefix="I am", guess_forms=guess_gerunds, expected_length=len_forms)

eng_hint = ""
hint_to_eng = False
if ask_yes_no("Do you want to add a hint/clarification note?"):
    print("Enter hint/clarification note.")
    eng_hint = input("> ").strip()
    hint_to_eng = ask_yes_no("Show the hint/clarification note in Portuguese to English tests?")

print("Does the following all look correct?")
print("  Portuguese infinitive  => {0}".format(infinitive))
print("  Infinitive form(s)     => to {0}".format("/".join(eng_inf if eng_inf else eng_1s)))
print("  1st person form(s)     => I {0}".format("/".join(eng_1s)))
print("  3rd person form(s)     => s/he {0}".format("/".join(eng_3s if eng_3s else eng_3s_guesses)))
print("  Plural form(s)         => we {0}".format("/".join(eng_p if eng_p else eng_1s)))
print("  Gerund form(s)         => I am {0}".format("/".join(gerunds if gerunds else guess_gerunds)))
if eng_hint:
    print("  Hint/clarification     => {0}".format(eng_hint))
    print("  Show hint 'to English' => {0}".format("yes" if hint_to_eng else "no"))

if not ask_yes_no():
    print("Please start over")
    exit()

eng_inf = ["to {0}".format(form) for form in eng_inf]
hint_to_eng = "1" if hint_to_eng else 0

if not existing:
    bank.append({
        "inf": infinitive, 
        "eng-inf": eng_inf, 
        "eng-1": eng_1s, 
        "eng-3": eng_3s, 
        "eng-p": eng_p, 
        "eng-gerund": gerunds, 
        "eng-hint": eng_hint, 
        "hint-to-eng": hint_to_eng
    })
else:
    for card in bank:
        if card["inf"] == infinitive:
            card["eng-inf"] eng_inf
            card["eng-1"] eng_1s
            card["eng-3"] eng_3s 
            card["eng-p"] eng_p 
            card["eng-gerund"] gerunds
            card["eng-hint"] eng_hint
            card["hint-to-eng"] hint_to_eng
            break

if os.path.exists("card-bank-basic.csv"):
    shutil.copyfile("card-bank-basic.csv", "card-bank-basic.bkp.csv")

with open("card-bank-basic.csv", "w", newline="", encoding="utf-8") as csvf:
    writer = csv.DictWriter(csvf, fieldnames=builder.BASIC_FIELDS)
    writer.writeheader()
    writer.writerows(bank)
