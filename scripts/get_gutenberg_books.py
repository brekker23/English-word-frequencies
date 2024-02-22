import requests
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import string


def load_words():
    """
    Load a set of valid words from a file.

    Returns:
    valid_words (set): A set of valid words.
    """
    with open('words.txt') as word_file:
        valid_words = set(word_file.read().split())
    return valid_words


def check_english(text, verbose=False):
    """
    Check if the given text is in English.

    Args:
    text (str): The text to check.
    verbose (bool): Whether to print verbose output.

    Returns:
    bool: True if the text is in English, False otherwise.
    """
    if "Language: English" in text.split("***")[0]:
        return True
    else:
        return False
    

word_set = load_words()

word_values = {}

lock = threading.Lock()


def thread_function(i):
    """
    Retrieve a book from the Gutenberg website, process the text, and update the word_values dictionary.

    Args:
    i (int): The book ID.

    Raises:
    Exception: If the book retrieval fails.
    """
    try:
        print(f"getting book... https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt")
        text = requests.get(f"https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt").text
        if "<!DOCTYPE html>" in text:
            raise Exception
    except:
        print(i, " failed to retrieve a book")
        return
    if not check_english(text):
        print(i, " not english")
        return
    text = text.split("***")[2]
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.split(" ")
    with lock:
        for word in words:
            if word in word_set:
                word_values[word] = word_values.get(word, 0) + 1


def read_temp():
    """
    Read the temperature from a file.

    Returns:
    temp (float): The temperature in degrees Celsius.
    """
    with open("/sys/class/thermal/thermal_zone0/temp") as f: #read temp on arch linux
        temp = int(f.read()) / 1000
    return temp


def cool_down():
    """
    Wait until the temperature cools down below 65 degrees Celsius.
    """
    while read_temp() > 65:
        print("cooling down")
        time.sleep(5)
    

workers = 10

# Create a ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=workers) as executor:
    # Submit tasks to thread pool
    i = 0
    while True:
        cool_down()
        try:
            executor.submit(thread_function, i)
        except:
            print(i, " failed thread")
            continue
        i += 1
        if i > 75000:
            break


sorted_words = [k for k, _ in sorted(word_values.items(), key=lambda item: item[1], reverse=True)]
print(sorted_words[:100])

highest_val = word_values[sorted_words[0]]

word_count = sum(word_values.values())

with open("word_frequencies.txt", "w") as f:
    for word in sorted_words:
        f.write(f"{word} {word_values[word]/highest_val}\n")

with open("word_count.txt", "w") as f:
    for word in sorted_words:
        f.write(f"{word} {word_values[word]}\n")

with open("word_percentages.txt", "w") as f:
    for word in sorted_words:
        f.write(f"{word} {word_values[word]/word_count}\n")
