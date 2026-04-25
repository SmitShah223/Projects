import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCES_DIR = BASE_DIR / "resources" / "assignment_materials"
INPUT_CSV = RESOURCES_DIR / "Input.xlsx - Sheet1.csv"


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


def main() -> None:
    url_data = extract_urls_from_csv(INPUT_CSV)
    for url_id, url in url_data:
        print("URL_ID:", url_id)
        print("URL:", url)
        print()


if __name__ == "__main__":
    main()
