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
    PRESENT=10, 
    PRESENT_CONTINUOUS=11, 
    IMPERFECT=20, 
    IMPERFECT_CONTINUOUS=21, 
    PERFECT=30, 
    FUTURE_SIMPLE=50, 
    FUTURE_FORMAL=52,
    FUTURE_COND=55, 
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
    1, # future simple
    0, # future formal
    0, # future conditional
    0, # imperative negative
    0  # imperative affirmative
)

TENSE_GROUPS = SimpleNamespace(
    INFINITIVE=(TENSE.INFINITIVE,), 
    PRESENT=(TENSE.PRESENT, TENSE.PRESENT_CONTINUOUS), 
    FUTURE=(TENSE.FUTURE_SIMPLE, TENSE.FUTURE_FORMAL, TENSE.FUTURE_COND), 
    PAST=(TENSE.IMPERFECT, TENSE.IMPERFECT_CONTINUOUS, TENSE.PERFECT), 
    IMPERFECT=(TENSE.IMPERFECT, TENSE.IMPERFECT_CONTINUOUS), 
    PERFECT=(TENSE.PERFECT), 
    IMPERATIVE=(TENSE.IMPERATIVE_NEG, TENSE.IMPERATIVE_AFM), 
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
    "ó": "o", 
    "õ": "o", 
    "ô": "o"
}
