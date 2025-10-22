import re


def to_copper(g=0, s=0, c=0) -> int:
    ...


def detect_value(list_value):
    gold = 0
    silver = 0
    copper = 0

    gold = re.findall(r'\d+ gold', ", ".join(list_value))
    silver = re.findall(r'\d+ silver', ", ".join(list_value))
    copper = re.findall(r'\d+ copper', ", ".join(list_value))

    if len(gold) > 0:
        gold = int(gold.split())
    else:
        gold = 0

    if len(silver) > 0:
        silver = int(silver.split())
    else:
        silver = 0

    if len(copper) > 0:
        copper = int(copper.split())
    else:
        copper = 0

    return (gold)

def main():
    with open("./data/loot_log.txt", "r") as file:
        data = file.readlines()

    loot = {}
    for line in data:
        parts = line.strip().split(', ')

        item = parts[0]
        print(f"Collected a {item}")

        if item not in loot:
            loot[item] = [0, []]

        loot[item][0] += 1
        valueGSC = detect_value(parts[1:])
        valueInCopper = to_copper(valueGSC)
        loot[item][1].append(valueGSC)
        loot[item][1].append(valueInCopper)


    print(loot)


if __name__ == "__main__":
    print("Hello e1b")
    main()
