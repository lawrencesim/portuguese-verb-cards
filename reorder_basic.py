import os, csv
from bin import cardbank
from bin import builder

bank = cardbank.read("card-bank-basic.csv", build_forms=False)

for card in bank:
    for f in builder.BASIC_FIELDS:
        if not f in card:
            card[f] = ""


with open("card-bank-basic-reorder.csv", "w", newline="", encoding="utf-8") as csvf:
    writer = csv.DictWriter(csvf, fieldnames=builder.BASIC_FIELDS)
    writer.writeheader()
    writer.writerows(bank)