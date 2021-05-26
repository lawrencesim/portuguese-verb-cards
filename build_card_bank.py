import os, csv, time
from bin.constants import TENSE
from bin import cardtest
from bin import builder


this_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(this_dir, ".."))
os.chdir(parent_dir)

bank = cardtest.read("card-bank-basic.csv", build_forms=False)

existing = []
if os.path.exists("card-bank-built.csv"):
    existing = cardtest.read("card-bank-built.csv", build_forms=False)
existing_map = {}
for card in existing:
    existing_map[card["inf"]] = card

tense = TENSE.PRESENT
session = builder.session()

built = []
errored = []
for card in bank:

    if card["inf"] in existing_map:
        existing_card = existing_map[card["inf"]]
        rebuild = False
        for field in builder.REQUIRED_FIELDS:
            if not field in existing_card or not existing_card[field]:
                rebuild = True
                break
        for field in builder.OPTIONAL_FIELDS:
            if rebuild:
                break
            if field not in existing_card or existing_card[field] != card[field]:
                existing_card[field] = card[field]
        if not rebuild:
            built.append(existing_card)
            continue

    tense_map = builder.get(card["inf"], tense=tense, session=session)
    if isinstance(tense_map, Warning):
        errored.append((card, str(tense_map)))
    else:
        builder.build(card, tense_map)
        built.append(card)
        print("{0} built".format(card["inf"]))
    time.sleep(0.25)

with open("card-bank-built.csv", "w", newline="", encoding="utf-8") as csvf:
    writer = csv.DictWriter(csvf, fieldnames=builder.FIELDS)
    writer.writeheader()
    writer.writerows(built)

for pair in errored:
    print("\nError building card for: {0}".format(pair[0]["inf"]))
    print(pair[1])
