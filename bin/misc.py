import random
from .constants import SPECIAL_CHARS


def pick_one(from_list):
    if isinstance(from_list, str):
        return from_list
    elif len(from_list) == 1:
        return from_list[0]
    return random.choice(from_list)


def compare(answer, guess):
    guess = replace_special_chars(guess.lower().strip())
    if isinstance(answer, str):
        return guess == replace_special_chars(answer.lower().strip())
    for check in answer:
        if guess == replace_special_chars(check.lower().strip()):
            return True
    return False


def compare_faster(answer, guess):
    guess = replace_special_chars(guess)
    if isinstance(answer, str):
        return guess == answer or guess == replace_special_chars(answer)
    if guess in answer:
        return True
    for check in answer:
        if guess == replace_special_chars(check):
            return True
    return False


def replace_special_chars(in_str):
    for special, replace in SPECIAL_CHARS.items():
        in_str = in_str.replace(special, replace)
    return in_str
