# main.py
from Engine import Engine
from AI import AI
from Loader import Loader


def main():
    ai = AI()
    engine = Engine(start_x = ai.choose_start())
    loader = Loader(41017)

    stream = loader.stream_decrypt_lines(f"tracks/TRK_41017.trk.enc")
    nb_movements, path = engine.run_game(stream, ai.choose_move)
    ai.exit()

    print(f"# Movements:{nb_movements}")
    print(f"Path:{path}")


if __name__ == "__main__":
    main()
