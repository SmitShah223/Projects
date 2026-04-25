# Web Scraping and Text Analysis

This project performs article extraction, stop-word removal, and readability or sentiment-style scoring over a set of URLs supplied in a reference CSV.

## Contents

- `src/` - Python scripts for URL extraction, article scraping, stop-word removal, readability analysis, and final CSV generation
- `data/extracted_articles/` - scraped raw article text files
- `data/cleaned_articles/` - stop-word filtered article text files
- `outputs/output.csv` - generated output metrics
- `resources/assignment_materials/` - assignment instructions, lexicons, stop-word lists, and the source URL sheet
- `resources/stop_words.txt` - consolidated stop-word file generated during repository cleanup

## Workflow

1. Run `src/article_text_extractor.py` to fetch article text from the URL sheet.
2. Run `src/stop_word_remover.py` to create the cleaned article corpus.
3. Run `src/final.py` to generate the consolidated output CSV.

## Notes

- The scripts were updated to use project-relative paths so the new folder layout remains runnable.
- The original notes mentioned that URL IDs `44`, `57`, and `144` returned missing pages during scraping.
