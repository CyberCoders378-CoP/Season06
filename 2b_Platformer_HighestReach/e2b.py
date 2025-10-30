from time import sleep
from SonicPlayer import SonicPlayer
from SonicMap import SonicMap



def load_commands(filename):
    with open(filename, "r") as f:
        return [line.rstrip("\n").split() for line in f]


def main():
    sonic_map = SonicMap("data/map.txt")
    player = SonicPlayer(sonic_map)

    commands = load_commands("data/commands.txt")

    for command in commands:
        player.manage(command)
        player.print_debug()
        sleep(0.01)

    print(f" Last position of Sonic=({player.x:.2f},{player.y:.2f})")


if __name__ == "__main__":
    print("Hello Episode 2b - Medium")
    main()
