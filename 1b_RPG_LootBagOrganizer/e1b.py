import re


def to_copper(g=0, s=0, c=0) -> int:
    return g*100+s*10+c


def to_gsc(c) -> tuple[int, int, int]:
    g = c // 100
    c-= g*100

    s = c // 10
    c-= s*10

    return g, s, c


def summarize_all_winnings(loot) -> tuple[int, int, int]:
    copper_value = 0

    for item in loot:
        for all_values in loot[item][1]:
            copper_value += to_copper(all_values[0], all_values[1], all_values[2])

    return to_gsc(copper_value)


def summarize_winnings_bestof(loot):
    copper_value = 0

    for item in loot:
        best_value = 0
        for value_gsc in loot[item][1]:
            value_c = to_copper(value_gsc[0], value_gsc[1], value_gsc[2])

            if value_c > best_value:
                best_value = value_c

        copper_value += best_value

    return to_gsc(copper_value)


def detect_value(list_value):
    gold = 0
    silver = 0
    copper = 0

    gold = re.findall(r'\d+ gold', ", ".join(list_value))
    silver = re.findall(r'\d+ silver', ", ".join(list_value))
    copper = re.findall(r'\d+ copper', ", ".join(list_value))

    if len(gold) > 0:
        gold = int(gold[0].split()[0])
    else:
        gold = 0

    if len(silver) > 0:
        silver = int(silver[0].split()[0])
    else:
        silver = 0

    if len(copper) > 0:
        copper = int(copper[0].split()[0])
    else:
        copper = 0

    return gold, silver, copper


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
        valueInCopper = to_copper(valueGSC[0], valueGSC[1], valueGSC[2])
        loot[item][1].append(valueGSC)

    total_value = summarize_all_winnings(loot)
    print(f"The total value of all the loot in Gold, Silver and copper coins is {total_value}")

    total_value = summarize_winnings_bestof(loot)
    print(f"The total value of all the loot in Gold, Silver and copper coins is {total_value}")


if __name__ == "__main__":
    print("Hello 1b")
    main()
