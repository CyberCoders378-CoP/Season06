

def main():
    with open("./data/battle_log.txt", "r") as file:
        data = file.readlines()

    hp = 250
    all_monsters = set()
    for line in data:
        words = line.split()


        if words[1] == "took":
            hp -= int(words[2])
            print(hp)
        elif words[1] == "hit":
            all_monsters.add(words[3])
        elif words[1]  == "takes":
            hp += int(words[5])
            hp = min(hp, 250)
            print(hp)

    print(f"Final Health after all battles: {hp}")
    print(f"Fought the following {len(all_monsters)} monsters: \n{all_monsters}")


if __name__ == "__main__":
    print("Hello 1a")
    main()
