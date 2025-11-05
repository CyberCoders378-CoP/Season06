import math


def is_shoot_in_target(target, shot):
    pos_x = int(target[0])
    pos_y = int(target[1])

    radius_bullseye = float(target[2])
    radius_inner = float(target[3])
    radius_outer = float(target[4])

    #Calculate hypothenuse
    distance = math.hypot(pos_x - float(shot[0]), pos_y - float(shot[1]))

    if distance <= radius_bullseye:
        return 10
    elif distance <= radius_inner:
        return 5
    elif distance <= radius_outer:
        return 3

    return 0


def main():
    with open("data/rings.txt") as fr:
        targets = fr.readlines()
        targets = [t.strip().split() for t in targets]

    with open("data/shots.txt") as fs:
        shots = fs.readlines()
        shots = [s.strip().split(",") for s in shots]

    total_score = 0
    log_shots = {}
    log_nb = {"Bullseye": 0, "Inner": 0, "Outer": 0}
    for i, shot in enumerate(shots):
        for target in targets:
            score = is_shoot_in_target(target, shot)

            match score:
                case 10:
                    log_shots[i] = "Bullseye"
                    log_nb["Bullseye"] += 1
                case 5:
                    log_shots[i] = "Inner"
                    log_nb["Inner"] += 1
                case 3:
                    log_shots[i] = "Outer"
                    log_nb["Outer"] += 1

            total_score += score

    print(f"Logs of all the shots individually: {log_shots}")
    print(f"Logs By Count: {log_nb}")


def main_extended():
    ...


if __name__ == "__main__":
    print("Hello e3a")
    main()
    main_extended()
