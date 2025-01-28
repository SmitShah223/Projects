from bs4 import BeautifulSoup
import requests
import csv

def extract_urls_from_csv(filename):
    urls = []
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url_id = row.get('URL_ID')
            url = row.get('URL')
            if url_id and url:
                urls.append((url_id, url))
    return urls

def extract_article(url,url_id):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract the title
        title_element = soup.find("h1")
        title = title_element.text.strip() if title_element else "Title not found"

        # Extract the main content
        main_content_element = soup.select_one(".td-container [role=main]")
        if main_content_element:
            content = ""
            paragraphs = main_content_element.find_all("p")
            for paragraph in paragraphs:
                content += paragraph.get_text(strip=True) + "\n"
        else:
            content = "Main content not found"
            print("Content not found of:", url_id)

        return title, content
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while accessing URL: {url}")
        print(f"Error message: {str(e)}")
        return None, None

csv_filename = 'Input.xlsx - Sheet1.csv'  
url_data = extract_urls_from_csv(csv_filename)

for url_id, url in url_data:
    article_title, article_content = extract_article(url,url_id)
    output_file = str(url_id) + ".txt"
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("Title: " + (article_title or "Title not found") + "\n")
        file.write("Content: " + (article_content or "Content not found") + "\n")

    print("Output saved to", output_file)
