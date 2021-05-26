import random


def pick_one(from_list):
    if isinstance(from_list, str):
        return from_list
    return random.choice(from_list)


def compare(answer, guess):
    guess = replace_special_chars(guess.lower().strip())
    if isinstance(answer, str):
        return guess == replace_special_chars(answer.lower().strip())
    for check in answer:
        if guess == replace_special_chars(check.lower().strip()):
            return True
    return False


def replace_special_chars(in_str):
    return in_str.replace("á", "a").replace("ã", "a")\
                 .replace("ç", "c")\
                 .replace("é", "e").replace("ê", "e").replace("ê", "e")\
                 .replace("í", "i")\
                 .replace("ó", "o")
