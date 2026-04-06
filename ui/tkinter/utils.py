import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import csv
import os


def display_error(message, message_type="Error"):
    tkinter.messagebox.showerror(message_type, message)


def get_csv_as_list(file, headers):
    try:
        with open(file) as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            final = []
            for row in reader:
                final.append(row)
        if headers:
            return [h.strip() for h in final[0]], final[1:]
        else:
            return final
    except:
        return None


def import_file(ui):
    filename = tk.filedialog.askopenfilename(initialdir=os.path.expanduser("~"), title="Select file", filetype=(("CSV files", "*.csv"),("All files", "*.*")))
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
