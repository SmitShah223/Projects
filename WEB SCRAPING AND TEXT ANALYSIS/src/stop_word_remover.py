from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXTRACTED_DIR = BASE_DIR / "data" / "extracted_articles"
CLEANED_DIR = BASE_DIR / "data" / "cleaned_articles"
STOP_WORDS_FILE = BASE_DIR / "resources" / "stop_words.txt"


def remove_stop_words(input_file_path: Path, stop_words_file_path: Path, output_file_path: Path):
    with stop_words_file_path.open("r", encoding="utf-8", errors="ignore") as stop_words_file:
        stop_words = set(stop_words_file.read().splitlines())

    with input_file_path.open("r", encoding="utf-8") as input_file:
        content = input_file.read()
        if "content not found" in content.lower():
            print("Content not found in:", input_file_path.name)

    modified_content = " ".join(
        word for word in content.split() if word.lower() not in stop_words
    )

    with output_file_path.open("w", encoding="utf-8") as output_file:
        output_file.write(modified_content)


def main() -> None:
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    for input_file_path in sorted(EXTRACTED_DIR.glob("*.txt")):
        output_file_path = CLEANED_DIR / f"cleaned_{input_file_path.stem}.txt"
        remove_stop_words(input_file_path, STOP_WORDS_FILE, output_file_path)
        print("Stop words removed from file:", input_file_path.name)
        print("Modified file saved as:", output_file_path.name)


if __name__ == "__main__":
    main()
