def find_start(data):
    for y, row in enumerate(data):
        for x, tile in enumerate(row):
            if tile == 'P':
                return x, y

    return None


def parse_level(level):
    """
    Convert a list of strings (lines from file) into a 2D list of characters.
    Automatically strips newlines and ignores empty lines.
    """
    grid = []
    for line in level:
        row = list(line.rstrip("\n"))  # remove newline, then split into chars
        if row:  # skip empty lines
            grid.append(row)
    return grid


def main():
    with open("data/level.txt") as file:
        level = file.readlines()
    level = parse_level(level)

    with open("data/moves.txt") as file2:
        moves = file2.readlines()

    pos = find_start(level)
    new_pos = pos
    coins = 0

    #Remove the P from the level, we got it
    level[pos[1]][pos[0]] = '.'

    for move in moves:
        move = move.strip()
        new_pos = pos
        match move:
            case 'R':
                new_pos = (pos[0] + 1, pos[1])
            case 'L':
                new_pos = (pos[0] - 1, pos[1])
            case 'U':
                new_pos = (pos[0], pos[1] - 1)
            case 'D':
                new_pos = (pos[0], pos[1] + 1)

        match level[new_pos[1]][new_pos[0]]:
            case '.':
                pos = (new_pos[0], new_pos[1])
            case 'C':
                coins += 1
                pos = (new_pos[0], new_pos[1])
                level[pos[1]][pos[0]] = '.'
            case '#':
                ... #Do not assign the new position, this is a wall
            case _:
                ... # Should not happen

    print(f"Amongst my path into the Maze I've collected {coins} coins.")


def main_extended():
    print("Activating the tron trail...")

    with open("data/level.txt") as file:
        level = file.readlines()
    level = parse_level(level)

    with open("data/moves.txt") as file2:
        moves = file2.readlines()

    pos = find_start(level)
    new_pos = pos
    coins = 0

    #Remove the P from the level, we got it
    level[pos[1]][pos[0]] = '.'

    for move in moves:
        move = move.strip()
        new_pos = pos
        match move:
            case 'R':
                new_pos = (pos[0] + 1, pos[1])
            case 'L':
                new_pos = (pos[0] - 1, pos[1])
            case 'U':
                new_pos = (pos[0], pos[1] - 1)
            case 'D':
                new_pos = (pos[0], pos[1] + 1)

        match level[new_pos[1]][new_pos[0]]:
            case '.':
                level[pos[1]][pos[0]] = '-'
                pos = (new_pos[0], new_pos[1])
            case 'C':
                coins += 1
                level[pos[1]][pos[0]] = '-'
                pos = (new_pos[0], new_pos[1])
                level[pos[1]][pos[0]] = '.'
            case '#':
                ... #Do not assign the new position, this is a wall
            case '-':
                ... #Do not assign the new position, this is the tron trail
            case _:
                ... # Should not happen

    print(f"Amongst my path into the Maze I've collected {coins} coins.")



if __name__ == "__main__":
    main()
    main_extended()
