# main.py
from Engine import Engine
from AI import AI
from Loader import Loader
import importlib


def main():
    engine = Engine()
    ai = AI()
    loader = Loader(41017)

    stream = loader.stream_decrypt_lines(f"tracks/TRK_41017.trk")
    dodges = engine.run_game(stream, ai.choose_move)

    print(f"DODGES:{dodges}")
    # Students submit `user`, `track`, `dodges`. Your grader returns the flag.


if __name__ == "__main__":
    main()
