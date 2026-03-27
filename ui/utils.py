import tkinter as tk
import tkinter.filedialog
import win32api
import csv

from state.item import Item


def display_error(message, message_type="Error"):
    win32api.MessageBox(0, message, message_type)


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


def import_file(ui):
    filename = tk.filedialog.askopenfilename(initialdir="C://", title="Select file", filetype=(("CSV files", "*.csv"),("All files", "*.*")))
    if not filename:
        return None
    if filename[-4:] != ".csv":
        display_error("Imported files must be of .csv type.")
        return None

    csv_file_list = get_csv_as_list(filename, True)
    if csv_file_list:
        headers, items = csv_file_list
    else:
        display_error(f"An error occured when importing the file: {filename}")
        return None

    item_dicts = [{} for _ in range(len(items))]
    for i, item in enumerate(items):
        for j, header in enumerate(headers):
            if header:
                key = header[2:] if header[:1] == "C:" else header
                item_dicts[i][key] = item[j]
    ui.item_list.items = [Item.from_dict(d) for d in item_dicts]
    ui.show_items()
