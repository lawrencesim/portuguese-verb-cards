import os, csv, time
from bin import cardtest
from bin import builder


this_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(this_dir, ".."))
os.chdir(parent_dir)

built = cardtest.read("card-bank-built.csv", build_forms=False)
basic = cardtest.read("card-bank-basic.csv", build_forms=False)

missing = list(set((card["inf"] for card in basic)) - set((card["inf"] for card in built)))

if not len(missing):
    print("No missing verbs found")
    exit()

tense = TENSE.PRESENT
session = builder.session()

built = []
errored = []
for card in basic:
    if card["inf"] not in missing:
        built.append(card)
        continue
    tense_map = builder.get(card["inf"], tense=tense, session=session)
    if isinstance(tense_map, Warning):
        errored.append((card, str(tense_map)))
    else:
        builder.build(card, tense_map)
        built.append(card)
        print("{0} built".format(card["inf"]))
    time.sleep(0.25)


with open("card-bank-built-2.csv", "w", newline="", encoding="utf-8") as csvf:
    writer = csv.DictWriter(csvf, fieldnames=builder.FIELDS)
    writer.writeheader()
    writer.writerows(built)

for pair in errored:
    print("\nError building card for: {0}".format(pair[0]["inf"]))
    print(pair[1])
