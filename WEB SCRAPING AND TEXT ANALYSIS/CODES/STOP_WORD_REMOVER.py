def remove_stop_words(input_file_path, stop_words_file_path, output_file_path,i):
    # Read the stop words from the file
    with open(stop_words_file_path, "r",encoding="utf-8") as stop_words_file:
        stop_words = stop_words_file.read().splitlines()

    # Read the content of the file to be modified
    with open(input_file_path, "r",encoding="utf-8") as input_file:
        content = input_file.read()
        if "content not found" in content or "Content not found" in content:
            print("Content not found in:",i)
    # Remove the stop words from the content
    modified_content = ' '.join(word for word in content.split() if word.lower() not in stop_words)

    # Write the modified content to the output file
    with open(output_file_path, "w",encoding="utf-8") as output_file:
        output_file.write(modified_content)

# File paths
for i in range(37, 151):
    input_file_path = str(i) + ".txt"
    output_file_path = "cleaned_" + str(i) + ".txt" 
    stop_words_file_path = "STOP_WORDS.txt"

    # Remove stop words from the file
    remove_stop_words(input_file_path, stop_words_file_path, output_file_path,i)

    print("Stop words removed from file:", input_file_path)
    print("Modified file saved as:", output_file_path)


