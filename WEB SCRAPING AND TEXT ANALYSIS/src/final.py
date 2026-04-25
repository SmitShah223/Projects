import csv
import re
import string
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXTRACTED_DIR = BASE_DIR / "data" / "extracted_articles"
CLEANED_DIR = BASE_DIR / "data" / "cleaned_articles"
OUTPUTS_DIR = BASE_DIR / "outputs"
RESOURCES_DIR = BASE_DIR / "resources" / "assignment_materials"
INPUT_CSV = RESOURCES_DIR / "Input.xlsx - Sheet1.csv"
POSITIVE_WORDS_FILE = RESOURCES_DIR / "positive-words.txt"
NEGATIVE_WORDS_FILE = RESOURCES_DIR / "negative-words.txt"
OUTPUT_CSV = OUTPUTS_DIR / "output.csv"


def extract_urls_from_csv(filename: Path):
    urls = []
    with filename.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url_id = row.get("URL_ID")
            url = row.get("URL")
            if url_id and url:
                urls.append((url_id, url))
    return urls


def calculate_average_sentence_length(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file:
        content = file.read()

    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", content)

    total_words = 0
    complex_words = 0
    syllable_count = 0
    personal_pronouns_count = 0
    total_characters = 0

    for sentence in sentences:
        words = sentence.split()
        total_words += len(words)
        for word in words:
            syllables = count_syllables(word)
            syllable_count += syllables
            if syllables > 2:
                complex_words += 1

            if word.lower() in ["i", "we", "my", "ours", "us"] and word != "US":
                personal_pronouns_count += 1

            total_characters += len(word)

    average_length = total_words / len(sentences) if sentences else 0
    complex_words_percentage = (complex_words / total_words) * 100 if total_words else 0
    fog_index = 0.4 * (average_length + complex_words_percentage)
    average_words_per_sentence = total_words / len(sentences) if sentences else 0
    average_word_length = total_characters / total_words if total_words else 0

    return (
        average_length,
        complex_words_percentage,
        fog_index,
        average_words_per_sentence,
        complex_words,
        syllable_count,
        personal_pronouns_count,
        average_word_length,
    )


def count_syllables(word: str) -> int:
    word = word.lower()
    if not word:
        return 0
    if word.endswith(("es", "ed")):
        return 0
    count = 0
    vowels = "aeiou"
    if word[0] in vowels and word[0] != "y":
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    return max(count, 0)


def count_cleaned_words(file_path_cleaned: Path) -> int:
    with file_path_cleaned.open("r", encoding="utf-8") as file:
        content = file.read()

    cleaned_content = re.sub(f"[{string.punctuation}]", "", content)
    return len(cleaned_content.split())


def count_positive_negative_words(
    cleaned_file_path: Path, positive_words_file_path: Path, negative_words_file_path: Path
):
    positive_score = 0
    negative_score = 0

    with cleaned_file_path.open("r", encoding="utf-8") as cleaned_file:
        cleaned_content = cleaned_file.read()
        words = cleaned_content.split()
        total_words = len(words)

    with positive_words_file_path.open("r", encoding="latin-1") as positive_words_file:
        positive_words = positive_words_file.read().splitlines()

    with negative_words_file_path.open("r", encoding="latin-1") as negative_words_file:
        negative_words = negative_words_file.read().splitlines()

    for word in positive_words:
        if word in cleaned_content:
            positive_score += 1

    for word in negative_words:
        if word in cleaned_content:
            negative_score += 1

    polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
    subjectivity_score = (positive_score + negative_score) / (total_words + 0.000001)

    return positive_score, negative_score, polarity_score, subjectivity_score


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    url_data = extract_urls_from_csv(INPUT_CSV)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(
            [
                "URL_ID",
                "URL",
                "POSITIVE SCORE",
                "NEGATIVE SCORE",
                "POLARITY SCORE",
                "SUBJECTIVITY SCORE",
                "AVG SENTENCE LENGTH",
                "PERCENTAGE OF COMPLEX WORDS",
                "FOG INDEX",
                "AVG NUMBER OF WORDS PER SENTENCE",
                "COMPLEX WORD COUNT",
                "WORD COUNT",
                "SYLLABLE PER WORD",
                "PERSONAL PRONOUNS",
                "AVG WORD LENGTH",
            ]
        )

        for url_id, url in url_data:
            file_path = EXTRACTED_DIR / f"{url_id}.txt"
            cleaned_file_path = CLEANED_DIR / f"cleaned_{url_id}.txt"
            (
                average_length,
                complex_words_percentage,
                fog_index,
                average_words_per_sentence,
                complex_words,
                syllable_count,
                personal_pronouns_count,
                average_word_length,
            ) = calculate_average_sentence_length(file_path)
            cleaned_word_count = count_cleaned_words(cleaned_file_path)
            positive_score, negative_score, polarity_score, subjectivity_score = count_positive_negative_words(
                cleaned_file_path, POSITIVE_WORDS_FILE, NEGATIVE_WORDS_FILE
            )
            csv_writer.writerow(
                [
                    url_id,
                    url,
                    positive_score,
                    negative_score,
                    polarity_score,
                    subjectivity_score,
                    average_length,
                    complex_words_percentage,
                    fog_index,
                    average_words_per_sentence,
                    complex_words,
                    cleaned_word_count,
                    syllable_count,
                    personal_pronouns_count,
                    average_word_length,
                ]
            )

    print("Data written to:", OUTPUT_CSV)


if __name__ == "__main__":
    main()
