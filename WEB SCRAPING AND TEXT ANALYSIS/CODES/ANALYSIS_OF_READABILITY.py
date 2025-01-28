import re
import string

def calculate_average_sentence_length(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Split the content into sentences using regular expressions
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', content)

    # Calculate the total number of words and complex words
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

            # Count personal pronouns
            if word.lower() in ["i", "we", "my", "ours", "us"] and word != "US":
                personal_pronouns_count += 1

            # Calculate total characters
            total_characters += len(word)

    # Calculate the average sentence length
    if len(sentences) > 0:
        average_length = total_words / len(sentences)
    else:
        average_length = 0

    # Calculate the percentage of complex words
    if total_words > 0:
        complex_words_percentage = (complex_words / total_words) * 100
    else:
        complex_words_percentage = 0

    # Calculate the Fog Index
    fog_index = 0.4 * (average_length + complex_words_percentage)

    # Calculate the average number of words per sentence
    if len(sentences) > 0:
        average_words_per_sentence = total_words / len(sentences)
    else:
        average_words_per_sentence = 0

    # Calculate the average word length
    if total_words > 0:
        average_word_length = total_characters / total_words
    else:
        average_word_length = 0

    return average_length, complex_words_percentage, fog_index, average_words_per_sentence, complex_words, syllable_count, personal_pronouns_count, average_word_length

def count_syllables(word):
    # Count the number of syllables in a word
    word = word.lower()
    if word.endswith(('es', 'ed')):
        return 0  # Exceptions for words ending with "es" or "ed"
    count = 0
    vowels = 'aeiou'
    if word[0] in vowels and word[0] not in ['y']:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith('e'):
        count -= 1  # Exceptions for words ending with "e"
    return count

def count_cleaned_words(file_path_cleaned):
    with open(file_path_cleaned, "r", encoding="utf-8") as file:
        content = file.read()

    # Remove punctuation marks
    cleaned_content = re.sub(f"[{string.punctuation}]", "", content)

    # Split the content into words
    words = cleaned_content.split()

    # Count the number of cleaned words
    cleaned_word_count = len(words)

    return cleaned_word_count

def count_positive_negative_words(cleaned_file_path, positive_words_file_path, negative_words_file_path):
    positive_score = 0
    negative_score = 0
    polarity_score = 0

    with open(cleaned_file_path, "r", encoding="utf-8") as cleaned_file:
        cleaned_content = cleaned_file.read()
        words = cleaned_content.split()
        total_words = len(words)

    with open(positive_words_file_path, "r", encoding="latin-1") as positive_words_file:
        positive_words = positive_words_file.read().splitlines()

    with open(negative_words_file_path, "r", encoding="latin-1") as negative_words_file:
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


positive_words_file_path = "positive-words.txt"
negative_words_file_path = "negative-words.txt"

for i in range(37, 151):
    file_path = str(i) + ".txt"
    cleaned_file_path = "cleaned_" + str(i) + ".txt"
    average_length, complex_words_percentage, fog_index, average_words_per_sentence, complex_words, syllable_count, personal_pronouns_count, average_word_length = calculate_average_sentence_length(file_path)
    cleaned_word_count = count_cleaned_words(cleaned_file_path)
    positive_score, negative_score, polarity_score, subjectivity_score = count_positive_negative_words(cleaned_file_path, positive_words_file_path, negative_words_file_path)
    print("File:", file_path)
    print("Positive Score:", positive_score)
    print("Negative Score:", negative_score)
    print("Polarity Score:", polarity_score)
    print("Subjectivity Score:", subjectivity_score)
    print("Average Sentence Length:", average_length)
    print("Percentage of Complex Words:", complex_words_percentage)
    print("Fog Index:", fog_index)
    print("Average Number of Words Per Sentence:", average_words_per_sentence)
    print("Number of Complex Words:", complex_words)
    print("Number of Cleaned Words:", cleaned_word_count)
    print("Number of Syllables:", syllable_count)
    print("Personal Pronouns Count:", personal_pronouns_count)
    print("Average Word Length:", average_word_length)
    print()
