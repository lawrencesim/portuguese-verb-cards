import os, csv, time, shutil
from bin.constants import TENSE
from bin import cardbank
from bin import builder


def add_build(add_cards):
    if not add_cards:
        return

    add_card_map = {}
    for card in add_cards:
        add_card_map[card["inf"]] = card

    card_bank = []
    if os.path.exists("card-bank-built.csv"):
        card_bank = cardbank.read("card-bank-built.csv", build_forms=False)

    session = builder.session()

    print("Building new card bank..")

    new_cards = []
    new_card_bank = []
    errored = []
    for card in card_bank:
        if card["inf"] not in add_card_map:
            new_card_bank.append(card)
        else:
            add_card = add_card_map[card["inf"]]
            del add_card_map[card["inf"]]
            _add(add_card, new_card_bank, new_cards, errored, session)

    for inf, card in add_card_map.items():
        _add(card, new_card_bank, new_cards, errored, session)

    finish_build(new_card_bank, new_cards, errored)


def build_from_difference(force_rebuild=[]):
    card_bank = cardbank.read("card-bank-basic.csv", build_forms=False)

    existing = []
    if os.path.exists("card-bank-built.csv"):
        existing = cardbank.read("card-bank-built.csv", build_forms=False)
    existing_map = {}
    for card in existing:
        existing_map[card["inf"]] = card

    session = builder.session()
    
    print("Building new card bank..")

    new_cards = []
    new_card_bank = []
    errored = []
    for card in card_bank:
        # if already exists, check if requiring update only (unless in list of force rebuild)
        if (card["inf"] not in force_rebuild) and (card["inf"] in existing_map):
            rebuild = False
            existing_card = existing_map[card["inf"]]
            for field in builder.REQUIRED_FIELDS:
                if not field in existing_card or not existing_card[field]:
                    rebuild = True
                    break
            for field in builder.OPTIONAL_FIELDS:
                if rebuild:
                    break
                if field not in existing_card or existing_card[field] != card[field]:
                    existing_card[field] = card[field]
            # if not rebuilding, only updating, just appending existing after update and next iteration
            if not rebuild:
                new_card_bank.append(existing_card)
                continue
        _add(card, new_card_bank, new_cards, errored, tense, session)

    finish_build(new_card_bank, new_cards, errored)


def _add(card, new_card_bank, new_cards, errored, session=None):
    tense_map = builder.get(card["inf"], tense=TENSE.PRESENT, session=session)
    if isinstance(tense_map, Warning):
        errored.append((card, str(tense_map)))
    else:
        builder.build(card, tense_map)
        new_card_bank.append(card)
        new_cards.append(card)
    time.sleep(0.25)


def finish_build(new_card_bank, new_cards, errored):
    print("")
    
    if os.path.exists("card-bank-built.csv"):
        shutil.copyfile("card-bank-built.csv", "card-bank-built.bkp.csv")
        print("Old card bank backed up as: card-bank-built.bkp.csv")

    with open("card-bank-built.csv", "w", newline="", encoding="utf-8") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=builder.FIELDS)
        writer.writeheader()
        writer.writerows(new_card_bank)

    print("New card bank written to: card-bank-built.csv")
                
    print("\nNew cards created:")
    for card in new_cards:
        print("  {0}".format(card["inf"]))

    if errored:
        print("\nError building card(s) for:")
        for pair in errored:
            print("  {0} : {1}".format(pair[0]["inf"], pair[1]))


if __name__ == "__main__":
    build_from_difference()
