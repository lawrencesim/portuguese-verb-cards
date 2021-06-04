from .constants import VOWELS


def eng_plural(singular_form):
    words = singular_form.split(" ")
    if word[0][-1] == "s":
        words[0] += "es"
    else:
        words[0] += "s"
    return " ".join(words)


def eng_gerund(infinitive):
    words = infinitive.split(" ")
    if len(words[0]) >= 3 and words[0][-1] == "e" and words[0][-2] not in VOWELS:
        words[0] = words[0][:-1]
    words[0] = words[0] + "ing"
    return " ".join(words)


def eng_past(singular_form):
    words = singular_form.split(" ")
    for i, word in enumerate(words):
        if word == "is":
            words[i] = "are"
        elif word == "are":
            words[i] = "were"
    if words[0][-1] == "e":
        words[0] += "d"
    elif words[0][-1] == "y":
        words[0] = words[0][:-1] + "ied"
    else:
        words[0] += "ed"
    return " ".join(words)
