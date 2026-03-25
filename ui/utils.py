import tkinter as tk
import tkinter.filedialog
import win32api

import tools


def display_error(message, message_type="Error"):
    win32api.MessageBox(0, message, message_type)


def import_file(ui):
    filename = tk.filedialog.askopenfilename(initialdir="C://", title="Select file", filetype=(("CSV files", "*.csv"),("All files", "*.*")))
    if not filename:
        return None
    if filename[-4:] != ".csv":
        display_error("Imported files must be of .csv type.")
        return None

    csv_file_list = tools.get_csv_as_list(filename, True)
    if csv_file_list:
        headers, items = csv_file_list
    else:
        display_error(f"An error occured when importing the file: {filename}")
        return None

    ui.item_list.items = [{} for _ in range(len(items))]    # Never do [{}] * some number
    for i, item in enumerate(items):
        for j, header in enumerate(headers):
            if header:
                if header[:1] == "C:":
                    ui.item_list.items[i][header[2:]] = item[j]
                else:
                    ui.item_list.items[i][header] = item[j]
    ui.show_items()
