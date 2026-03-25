import csv
import json
import requests


ITEM_NUMBER_LENGTH = 12
WEBSITE_URL = "https://www.lovedjeans.co.uk"


def deleter_status_message(item_type):
    try:
        website_data = item_type.upload_data["website"]["item"]
        response = requests.post(WEBSITE_URL + "/is_deleter_running/", data={
            "username": website_data["username"],
            "password": website_data["password"]
        })
        if response.text == "True":
            return "Deleter Is Running"
        else:
            return "Deleter Not Running"
    except Exception as _:
        return "Deleter Not Running"


def load_json_file(file, name=None):
    with open(file, encoding="utf-8") as file:
        loaded = json.load(file)
        if name == "default":
            name = loaded["default"]
        return loaded[name] if name else loaded

def get_csv_as_list(file, headers):
    try:
        with open(file) as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            final = []
            for row in reader:
                final.append(row)
        if headers:
            return final[0], final[1:]
        else:
            return final
    except:
        return None

def write_csv(file, data):
    with open(file, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",")
        for row in data:
            csvwriter.writerow(row)

def split_list(to_split, length):
    for i in range(0, len(to_split), length):
        yield to_split[i:i + length]

def none_to_str(word):
    return "" if word is None else word

def in_to_cm(value):
    return str(round(int(value) * 2.5))

def remove_dupes(word, repeat=True):
    word_list = word.split(" ")
    dupe_list = []
    final_list = []
    for word in word_list:
        if not (word.lower() in dupe_list) and word:
            final_list.append(word)
            dupe_list.append(word.lower())
    if repeat:
        return remove_dupes(" ".join(final_list), False)
    return " ".join(final_list)

def check_int(num):
    try:
        num = str(int(num))
        return num if len(num) == ITEM_NUMBER_LENGTH else None
    except (ValueError, TypeError):
        return None

def split_numbers(nums):
    nums = nums.replace(" ", "")
    if "," in nums:
        return nums.split(",")
    elif ";" in nums:
        return nums.split(";")
    elif "\n" in nums:
        return nums.split("\n")
    else:
        return [nums[i:i+ITEM_NUMBER_LENGTH] for i in range(0, len(nums), ITEM_NUMBER_LENGTH)]

def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))
