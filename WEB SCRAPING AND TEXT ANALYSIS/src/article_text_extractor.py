import csv
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted_articles"
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


def extract_article(url: str, url_id: str):
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title_element = soup.find("h1")
        title = title_element.text.strip() if title_element else "Title not found"

        main_content_element = soup.select_one(".td-container [role=main]")
        if main_content_element:
            paragraphs = main_content_element.find_all("p")
            content = "\n".join(paragraph.get_text(strip=True) for paragraph in paragraphs)
        else:
            content = "Main content not found"
            print("Content not found for:", url_id)

        return title, content
    except requests.exceptions.RequestException as exc:
        print(f"Error occurred while accessing URL: {url}")
        print(f"Error message: {exc}")
        return None, None


def main() -> None:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    url_data = extract_urls_from_csv(INPUT_CSV)

    for url_id, url in url_data:
        article_title, article_content = extract_article(url, url_id)
        output_file = EXTRACTED_DIR / f"{url_id}.txt"
        with output_file.open("w", encoding="utf-8") as file:
            file.write("Title: " + (article_title or "Title not found") + "\n")
            file.write("Content: " + (article_content or "Content not found") + "\n")

        print("Output saved to", output_file)


if __name__ == "__main__":
    main()
