

def main():
    with open("./data/battle_log.txt", "r") as file:
        data = file.readlines()

    hp = 250
    for line in data:
        words = line.split()

        if words[1].startswith("took"):
            hp -= int(words[2])
            print(hp)
        elif words[1].startswith("hit"):
            ...
        elif words[1].startswith("takes"):
            hp += int(words[5])
            hp = min(hp, 250)
            print(hp)

    print(f"Final Health after all battles: {hp}")


if __name__ == "__main__":
    print("Hello e1a")
    main()
