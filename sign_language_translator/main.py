import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from data_collection.collect_data import main as collect_main
from preprocessing.preprocess import main as preprocess_main
from training.train_model import main as train_main
from training.evaluate import main as evaluate_main
from realtime.realtime_translator import main as realtime_main


def main() -> None:
    parser = argparse.ArgumentParser(description="ASL Sign Language Translator Pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("collect", help="Collect hand landmark data")
    subparsers.add_parser("preprocess", help="Preprocess raw data")
    subparsers.add_parser("train", help="Train the model")
    subparsers.add_parser("evaluate", help="Evaluate the model")
    subparsers.add_parser("realtime", help="Run real-time translator")

    args, remaining = parser.parse_known_args()

    if args.command == "collect":
        sys.argv = [sys.argv[0]] + remaining
        collect_main()
    elif args.command == "preprocess":
        sys.argv = [sys.argv[0]] + remaining
        preprocess_main()
    elif args.command == "train":
        sys.argv = [sys.argv[0]] + remaining
        train_main()
    elif args.command == "evaluate":
        sys.argv = [sys.argv[0]] + remaining
        evaluate_main()
    elif args.command == "realtime":
        sys.argv = [sys.argv[0]] + remaining
        realtime_main()


if __name__ == "__main__":
    main()
