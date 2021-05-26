import os, csv
from bin import cardtest
from bin import builder

bank = cardtest.read("card-bank-basic.csv", build_forms=False)

for card in bank:
    for f in builder.BASIC_FIELDS:
        if not f in card:
            card[f] = "" if f != "hint-to-eng" else "1"


with open("card-bank-basic-reorder.csv", "w", newline="", encoding="utf-8") as csvf:
    writer = csv.DictWriter(csvf, fieldnames=builder.BASIC_FIELDS)
    writer.writeheader()
    writer.writerows(bank)