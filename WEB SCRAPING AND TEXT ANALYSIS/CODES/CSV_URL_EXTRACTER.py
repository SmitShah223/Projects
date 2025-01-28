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

csv_filename = 'Input.xlsx - Sheet1.csv'  
url_data = extract_urls_from_csv(csv_filename)

# Print the extracted URL_ID and URL pairs
for url_id, url in url_data:
    print("URL_ID:", url_id)
    print("URL:", url)
    print()
