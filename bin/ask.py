
def _ask(question, same_line):
    if not question:
        return input("> ").strip().lower()
    if same_line:
        return input(question).strip().lower()
    else:
        print(question)
        return input("> ").strip().lower()


def basic(question="", same_line=False, allow_empty=False):
    response = _ask(question, same_line)
    if response or allow_empty:
        return response
    print("You did not specify a response. Try again.")
    return basic(question, same_line, allow_empty)

def yes_no(question="", same_line=False):
    '''Ask yes/no question and parse input until acceptable answer given.'''
    response = _ask(question, same_line)
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
    print("Could not understand response, type `yes` or `no`.")
    return yes_no(question, same_line)


def integer(question="", same_line=False, positive=False, nonzero=False, minvalue=None, maxvalue=None):
    '''Ask integer question and parse input until acceptable answer given.'''
    response = _ask(question, same_line)
    try:
        response = int(response)
        if nonzero and response == 0:
            print("Response must be nonzero.")
            return integer(question, same_line, positive, nonzero, minvalue, maxvalue)
        elif positive and response < 0:
            print("Response must be a positive number.")
            return integer(question, same_line, positive, nonzero, minvalue, maxvalue)
        elif minvalue is not None and response < minvalue:
            print("Response is less than maximum allowed value of {0}.".format(minvalue))
            return integer(question, same_line, positive, nonzero, minvalue, maxvalue)
        elif maxvalue is not None and response > maxvalue:
            print("Response is greater than maximum allowed value of {0}.".format(maxvalue))
            return integer(question, same_line, positive, nonzero, minvalue, maxvalue)
        else:
            return response
    except:
        print("Could interpret your response as a whole number.")
        return integer(question, same_line, positive, nonzero, minvalue, maxvalue)

