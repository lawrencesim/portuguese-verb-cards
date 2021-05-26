from types import SimpleNamespace


PERSON = SimpleNamespace(FIRST=1, SECOND=2, THIRD=3)
TENSE = SimpleNamespace(INFINTIVE=0, PRESENT=1, PRESENT_CONTINUOUS=1.5)

PERSON_VALUES = tuple(getattr(PERSON, n) for n in dir(PERSON) if not n.startswith("_"))
TENSE_VALUES = tuple(getattr(TENSE, n) for n in dir(TENSE) if not n.startswith("_"))

PERSON_NAMES = {getattr(PERSON, n): n for n in dir(PERSON) if not n.startswith("_")}
TENSE_NAMES = {getattr(TENSE, n): n for n in dir(TENSE) if not n.startswith("_")}

PRONOUNS = (
    (None, "eu", "tu", ("você", "ele", "ela")), 
    (None, "nós", "vós", ("vocês", "eles", "elas"))
)
ENG_PRONOUNS = (
    (None, "I", "you", ("he", "she")), 
    (None, "we", "you(s)", "they")
)
