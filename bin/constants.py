from types import SimpleNamespace


PERSON = SimpleNamespace(FIRST=1, SECOND=2, THIRD=3)
PERSON_VALUES = tuple(sorted(getattr(PERSON, n) for n in dir(PERSON) if not n.startswith("_")))
PERSON_NAMES = {getattr(PERSON, n): n for n in dir(PERSON) if not n.startswith("_")}

PRONOUNS = (
    (None, "eu", "tu", ("você", "ele", "ela")), 
    (None, "nós", "vós", ("vocês", "eles", "elas"))
)
ENG_PRONOUNS = (
    (None, "I", "you", ("he", "she")), 
    (None, "we", "you(s)", "they")
)

TENSE = SimpleNamespace(
    INFINITIVE=0, 
    PRESENT=1, 
    PRESENT_CONTINUOUS=1.5, 
    IMPERFECT=2, 
    IMPERFECT_CONTINUOUS=2.5, 
    PERFECT=3, 
    FUTURE=5, 
    FUTURE_COND=6, 
    IMPERATIVE_NEG=90, 
    IMPERATIVE_AFM=91
)
TENSE_VALUES = tuple(sorted(getattr(TENSE, n) for n in dir(TENSE) if not n.startswith("_")))
TENSE_NAMES = {getattr(TENSE, n): n for n in dir(TENSE) if not n.startswith("_")}

DEFAULT_TENSE_WEIGHTS = (
    1, # infinitive
    4, # present
    1, # present continuous
    0, # imperfect
    0, # imperfect continuous
    0, # perfect
    0, # future
    0, # future conditional
    0, # imperative negative
    0  # imperative affirmative
)

VOWELS = ("a", "e", "i", "o", "u")

SPECIAL_CHARS = {
    "á": "a", 
    "ã": "a", 
    "ç": "c", 
    "é": "e", 
    "ê": "e", 
    "ê": "e", 
    "í": "i", 
    "ó": "o"
}
