import tkinter as tk
import tkinter.filedialog
import win32api
import csv


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

    ui.item_list.load(headers, items)
    ui.show_items()
