import os, csv, time, shutil
from bin import cardbank
from bin import builder


def add_build(add_cards):
    '''Build card bank by specifically adding new cards.'''

    # process new cards to add
    if not add_cards:
        return
    add_card_map = {}
    for card in add_cards:
        add_card_map[card["inf"]] = card

    # read in existing card bank
    card_bank = []
    if os.path.exists("bank/card-bank-built.csv"):
        card_bank = cardbank.read("bank/card-bank-built.csv", build_forms=False)

    # start HTTP session for reuse
    session = builder.session()

    print("Building new card bank..")

    # rebuild card bank, starting with populating from existing
    new_cards = []
    updated_cards = []
    new_card_bank = []
    errored = []
    for card in card_bank:
        if card["inf"] not in add_card_map:
            # no change, just add existing card
            new_card_bank.append(card)
        else:
            # changed, replace with new card definition
            add_card = add_card_map[card["inf"]]
            del add_card_map[card["inf"]]
            _build_card_and_add(add_card, new_card_bank, new_cards, errored, session)

    # add all brand new cards
    for inf, card in add_card_map.items():
        _build_card_and_add(card, new_card_bank, new_cards, errored, session)

    finish_build(new_card_bank, new_cards, updated_cards, errored)


def build_from_difference(force_rebuild=[]):
    '''Build card bank by rectifying differences in card bank basic and built.'''

    # read card bank basic (card bank with all basic definitions but not built out)
    card_bank_basic = cardbank.read("bank/card-bank-basic.csv", build_forms=False)

    # read existing, card bank built
    existing = []
    if os.path.exists("bank/card-bank-built.csv"):
        existing = cardbank.read("bank/card-bank-built.csv", build_forms=False)
    existing_map = {}
    for card in existing:
        existing_map[card["inf"]] = card

    # start HTTP session for reuse
    session = builder.session()
    
    print("Building new card bank..")

    # build card bank from card bank basic
    new_cards = []
    updated_cards = []
    new_card_bank = []
    errored = []
    for card in card_bank_basic:
        # if already exists, check if requiring update only (unless in list of force rebuild)
        if (card["inf"] not in force_rebuild) and (card["inf"] in existing_map):
            existing_card = existing_map[card["inf"]]
            # if any of the built fields are different, something's wrong, rebuilt it entirely
            rebuild = False
            for field in builder.BUILT_FIELDS:
                if not field in existing_card or not existing_card[field]:
                    rebuild = True
                    break
            # if not rebuilding, just updat the supplied fields, which doesn't affect build fields
            update = False
            for field in builder.SUPPLIED_FIELDS:
                if rebuild:
                    break
                if field not in existing_card or existing_card[field] != card[field]:
                    update = True
                    existing_card[field] = card[field]
            # if no rebuild needed, append existing [and updated] card and continue
            if not rebuild:
                new_card_bank.append(existing_card)
                if update:
                    updated_cards.append(existing_card)
                continue
        # if doesn't exist or need rebuilding, rebuild card
        _build_card_and_add(card, new_card_bank, new_cards, errored, session)

    finish_build(new_card_bank, new_cards, updated_cards, errored)


def _build_card_and_add(card, new_card_bank, new_cards, errored, session=None):
    # get verb tenses
    tense_map = builder.get(card["inf"], session=session)
    # if warning returned, then invalid somehow
    if isinstance(tense_map, Warning):
        errored.append((card, str(tense_map)))
    # otherwise build card and append to card bank
    else:
        builder.build(card, tense_map)
        new_card_bank.append(card)
        new_cards.append(card)
    # don't spam the website
    time.sleep(1)


def finish_build(new_card_bank, new_cards, updated_cards, errored):
    '''Finish build, save card bank, and print information about build.'''
    print("")

    if not new_cards and not updated_cards and not errored:
        print("No changes")
        return
    
    if new_cards or updated_cards:
        # backup
        if os.path.exists("bank/card-bank-built.csv"):
            shutil.copyfile("bank/card-bank-built.csv", "bank/card-bank-built.bkp.csv")
            print("Old card bank backed up as: bank/card-bank-built.bkp.csv")
        # write new
        with open("bank/card-bank-built.csv", "w", newline="", encoding="utf-8") as csvf:
            writer = csv.DictWriter(csvf, fieldnames=builder.FIELDS)
            writer.writeheader()
            writer.writerows(new_card_bank)
        print("New card bank written to: bank/card-bank-built.csv")
    
    if new_cards:
        print("\nNew cards created:")
        for card in new_cards:
            print("  {0}".format(card["inf"]))
    
    if updated_cards:
        print("\nCards updated:")
        for card in updated_cards:
            print("  {0}".format(card["inf"]))

    if errored:
        print("\nError building card(s) for:")
        for pair in errored:
            print("  {0} : {1}".format(pair[0]["inf"], pair[1]))


# if called straight-up, build from difference between basic and build card bank
if __name__ == "__main__":
    build_from_difference()
