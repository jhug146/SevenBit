"""
Tools file stores the UI class and two useful functions import_file and get_csv_as_list
"""
import tkinter as tk
import tkinter.font
import tkinter.filedialog

from PIL import Image
from PIL.ImageTk import PhotoImage
import win32api
import csv
import json

from upload_display import ScrollableFrame


ITEM_NUMBER_LENGTH = 12

class UI:
    CONDITION_HEADERS = ("Condition 1", "Condition 2", "Condition 4 (Free Text)")
    def __init__(self, item_type):
        self.item_type = item_type
        self.upload_type = 0
        self.window = tk.Tk()
        self.window.title("SevenBit")
        self.scrw, self.scrh = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.window.geometry(f"{int(self.scrw * 0.8)}x{int(self.scrh * 0.8)}")
        self.window.iconphoto(False, PhotoImage(file="images/icon.png"))

        self.main_frame = tk.Frame(self.window, width=self.scrw, height=self.scrh)
        self.main_frame.pack()

        self.middle_frame = tk.Frame(self.main_frame, width=self.scrw * 0.58, height=self.scrh)
        self.right_frame = tk.Frame(self.main_frame, width=self.scrw * 0.42, height=self.scrh)
        self.options_frame = tk.Frame(self.middle_frame, width=self.scrw * 0.65, height=self.scrh * 0.2)
        self.table_frame = tk.Frame(self.middle_frame, borderwidth=1, width=self.scrw * 0.65, height=self.scrh * 0.8)
        self.header_frame = tk.Frame(self.table_frame, width=self.scrw * 0.65, height=self.scrh / 400)
        self.bar_frame = tk.Frame(self.header_frame, width=self.scrw * 0.1, height=self.scrh / 400)

        self.console_font = self.make_font(10)
        self.small_font = self.make_font(12)
        self.big_font = self.make_font(16)

        frames = (
            (self.middle_frame, 0, 0),
            (self.right_frame, self.scrw * 0.58, 0),
            (self.options_frame, 0, 0),
            (self.table_frame, 0, 100),
            (self.header_frame, 0, 0),
            (self.bar_frame, 200, 0)
        )
        for frame in frames:
            frame[0].place(x=frame[1], y=frame[2])

        headers_list = (
            ("Image", 5, 0),
            ("Title", 76, 1),
            ("SKU", 19, 2),
            ("Price", 19, 3)
        )
        for headers in headers_list:  # Item table headers
            tk.Label(self.header_frame, text=headers[0], relief="solid", borderwidth=1, width=headers[1], height=int(self.scrh / 400), bg="#e5e5e5").grid(row=0, column=headers[2])

        img = Image.open("images/refresh.png")
        img = img.resize((28,28))
        self.refresh_image = PhotoImage(img)
        self.refresh_button = tk.Button(self.table_frame, image=self.refresh_image, command=self.refresh_table)
        self.refresh_button.place(x=1025, y=0)

    def init_buttons(self, func_list):
        button_details = (
            ("#133ea1", "Import", 0, 5, 0),
            ("#133e72", "Upload", 1, 5, 50),
            ("#128f89", "Download", 2, 155, 0),
            ("#117f89", "Accounts", 3, 155, 50),
            ("#129691", "Item Type", 4, 305, 0),
            ("#123f69", "Upload Mode", 5, 305, 50)
        )
        for details in button_details:
            tk.Button(self.options_frame, font=self.big_font, bg=details[0], fg="white", width=10, text=details[1], relief="ridge", command=func_list[details[2]]).place(x=details[3], y=details[4])

    def set_upload_attr(self, upload):
        self.upload = upload

    def make_font(self, size):
        return tkinter.font.Font(self.window, family="Helvetica", size=size)

    def outline_item(self, items, red):
        """
        Outlines the given items in either red or blue.
        :param items: list or integer
        :param red: boolean
        :return: None
        """
        if red:
            for frame in self.frames_list:
                frame.configure(bg="black")
            for frame in items:
                self.frames_list[frame].configure(bg="red")
        else:
            for frame in self.frames_list:
                frame.configure(bg="black")
            self.frames_list[items].configure(bg="blue")

    def view_item(self, n):
        """
        Displays editable information for item n on the right side of the screen
        :param n: integer
        :return: None
        """
        self.item_number = n
        def change_item(up, current):
            """
            Changes the item being currently viewed up or down
            :param up: boolean
            :param current: integer
            :return: None
            """
            if 0 <= current < len(self.item_specifics):
                if up:
                    if (current + 1) < len(self.item_specifics):
                        self.view_item(current+1)
                else:
                    if (current - 1) >= 0:
                        self.view_item(current-1)
            else:
                self.view_item(0)

        self.outline_item(n, False)
        try:
            clear_widget(self.img_frame)
        except:
            pass
        try:
            clear_widget(self.specifics_frame)
        except:
            pass

        self.window.bind("<Down>", lambda x: change_item(1, n))
        self.window.bind("<Up>", lambda x: change_item(0, n))

        self.til_frame = tk.Frame(self.right_frame, width=self.scrw*0.42, height=self.scrh*0.25)
        self.til_frame.place(x=0, y=0)
        self.img_frame = tk.Frame(self.right_frame, width=self.scrw*0.42, height=self.scrh*0.25)
        self.img_frame.place(x=0, y=225)
        self.specifics_frame = tk.Frame(self.right_frame, width=self.scrw*0.4, height=self.scrh*0.45)
        self.specifics_frame.place(x=0, y=475)

        def show_images():
            """
            Displays the images of the current item and allows the users to delete images and edit their order
            :return: None
            """
            for widget in self.img_frame.winfo_children():
                widget.destroy()

            def reorder(number):
                """
                Re-orders the current images by moving the selected image and the following image to the beggining of the images
                :param number: integer
                :return: None
                """
                if number < len(img_paths)-1:
                    popped1 = img_paths.pop(number)
                    popped2 = img_paths.pop(number)
                    img_paths.insert(0, popped2)
                    img_paths.insert(0, popped1)

                    self.item_specifics[n]["Path"] = ";".join(img_paths) + ";"
                    show_images()

            def delete_image(number):
                """
                Deletes the image in the specified location
                :param number: integer
                :return: None
                """
                if len(img_paths) > 4:
                    img_paths.pop(number)
                    self.item_specifics[n]["Path"] = ";".join(img_paths) + ";"
                    show_images()

            def place_image(path, row, col, count):
                """
                Places the specified image using the .grid() layout system
                :param path: string
                :param row: integer
                :param col: integer
                :param count: integer
                :return: None
                """
                if "http" in path:
                    return None
                img = Image.open(path).resize((110, 110), Image.LANCZOS)
                imgr = PhotoImage(img)
                box = tk.Label(self.img_frame, image=imgr)
                box.image = imgr
                box.grid(row=row, column=col)
                box.bind("<Button 1>", lambda x=count: reorder(count))
                box.bind("<Button 3>", lambda x=count: delete_image(count))

            img_paths = self.item_specifics[n]["Path"].split(";")
            if img_paths[-1] == "":
                img_paths.pop()

            for i, img in enumerate(img_paths):
                if i < 6:
                    place_image(img, 0, i, i)
                else:
                    place_image(img, 1, i-6, i)

        def save_current():
            """
            Save the current layout of the images
            :return: None
            """
            middle = []
            for i,condition_box in enumerate(condition_boxes):
                self.item_specifics[n][self.CONDITION_HEADERS[i]] = condition_box.get("1.0", "end").strip().strip("\n")
                middle.append(condition_box.get("1.0", "end").strip().strip("\n"))

            self.item_specifics[n]["eBay Condition Description"] = self.item_type.upload_data["condition_opening"] + " ".join(middle) + self.item_type.upload_data["condition_closing"]
            for detail in var_dict.keys():
                self.item_specifics[n][detail] = var_dict[detail].get()

            self.refresh_table()

        def single_item_upload():
            self.upload.start_upload(1, self.item_specifics[n]["SKU"])

        displayed_details = self.item_type.upload_data["display_order"]

        var_dict = {}
        titles = tuple(self.item_specifics[n].keys())

        headers = (
            ("Title", "Title:", 0, 0, 0, 20, 73),
            ("Fixed Price eBay", "Price:", 50, 185, 100, 185, 10),
            ("SKU", "SKU:", 400, 185, 450, 185, 10)
        )
        for (list_pos, label, x1, y1, x2, y2, width) in headers:
            var_dict[list_pos] = tk.StringVar(value=self.item_specifics[n][list_pos])
            tk.Label(self.til_frame, font=self.small_font, text=label).place(x=x1, y=y1)
            tk.Entry(self.til_frame, font=self.small_font, textvariable=var_dict[list_pos], width=width).place(x=x2, y=y2)

        condition_boxes = []
        tk.Label(self.til_frame, font=self.small_font, text="Conditions:").place(x=0, y=45)
        for i in range(3):
            con_box = tk.Text(self.til_frame, font=self.small_font, width=73, height=2)
            con_box.insert(1.0, self.item_specifics[n][self.CONDITION_HEADERS[i]])
            con_box.place(x=0, y=65+(i*40))
            condition_boxes.append(con_box)

        for i,label in enumerate(titles):
            if label in displayed_details:
                var_dict[label] = tk.StringVar(value=self.item_specifics[n][titles[i]])
                tk.Label(self.specifics_frame, font=self.small_font, text=label[3:]).grid(row=i+1, column=0)
                tk.Entry(self.specifics_frame, textvariable=var_dict[label], font=self.small_font, width=60).grid(row=i+1, column=1)

        tk.Button(self.right_frame, text="Save Changes", relief="ridge", font=self.big_font, pady=10, padx=10, command=save_current, bg="#139490", fg="white").place(x=50, y=955)
        tk.Button(self.right_frame, text="Upload Item", relief="ridge", font=self.big_font, pady=10, padx=10, command=single_item_upload, bg="#123da5", fg="white").place(x=500, y=955)
        show_images()

    def refresh_table(self):
        """
        Refreshs the main table of items
        :return: None
        """
        if hasattr(self, "item_specifics"):
            if type(self.item_specifics) is list:
                self.show_items()
                self.view_item(0)

    def show_items(self):
        try:
            for child in self.content_frame.winfo_children():
                child.destroy()
        except:
            pass

        self.frames_list = []
        self.scroll_height = len(self.item_specifics) * 42   # Height of scroll bar

        self.content_scroll = ScrollableFrame(self.table_frame, self.scroll_height, "#e5e5e5", self.scrw * 0.55)
        self.content_scroll.place(x=0, y=35)
        self.content_frame = tk.Frame(self.content_scroll.scrollable_frame, width=1000, height=2000)
        self.content_frame.place(x=0, y=0)

        for c,item in enumerate(self.item_specifics):
            item_frame = tk.Frame(self.content_frame, width=round(self.scrw * 0.9), height=round(self.scrh / 200), borderwidth=1, relief="solid")
            self.frames_list.append(item_frame)
            item_frame.grid(row=c, column=0)
            for detail in ((0, "Path", self.scrh / 150), (1, "Title", self.scrw / 25), (2, "SKU", self.scrw / 100), (3, "Fixed Price eBay", self.scrw / 100)):
                if detail[1] != "Path":
                    tk.Label(item_frame, relief="solid", borderwidth=1, text=item[detail[1]], height=round(self.scrh / 500), width=round(detail[2])).grid(row=0, column=detail[0])
                else:
                    try:
                        self.place_table_image(item_frame, item[detail[1]].split(";")[0]).grid(row=0, column=0)
                    except FileNotFoundError:
                        display_error(f"Error loading image: {item[detail[1]].split(';')[0]}")

            tk.Button(item_frame, font=self.small_font, relief="ridge", text="View", height=1, width=round(self.scrw / 100), command=lambda x=c: self.view_item(x)).grid(row=0, column=4)

    def get_options(self, upload_obj, start=""):
        """
        Brings up a menu with the different upload options which are:
        normal - Starts from the first item in the file
        specific - Uploads only the specified SKUs
        start_point - Starts from the specified SKU
        :param upload_obj: EbayUpload object
        :param start: string
        :return: None
        """
        self.options_win = tk.Toplevel(self.window)
        self.options_win.geometry("350x115")
        self.options_win.title("Upload Options")
        self.options_win.iconphoto(False, PhotoImage(file="images/icon.png"))

        def normal():
            self.options_win.destroy()
            upload_obj.start_upload(0, None)

        def specific():
            self.options_win.destroy()
            upload_obj.start_upload(1, self.specific_var.get())

        def start_point():
            self.options_win.destroy()
            upload_obj.start_upload(2, self.start_point_var.get(), self.end_point_var.get())

        tk.Button(self.options_win, width=15, bg="#146e72", fg="white", font=self.small_font, text="Normal Upload", command=normal).place(x=5, y=5)

        self.specific_var = tk.StringVar()
        self.specific_entry = tk.Entry(self.options_win, width=30, textvariable=self.specific_var)
        self.specific_entry.place(x=155, y=45)
        tk.Button(self.options_win, width=15, bg="#142e65", fg="white", font=self.small_font, text="Specific Items", command=specific).place(x=5, y=40)
        self.specific_entry.bind("<Return>", lambda x: specific())

        self.start_point_var = tk.StringVar(value=start)
        self.end_point_var = tk.StringVar(value=None)

        self.start_point_entry = tk.Entry(self.options_win, width=15, textvariable=self.start_point_var)
        self.end_point_entry = tk.Entry(self.options_win, width=15, textvariable=self.end_point_var)
        self.start_point_entry.place(x=155, y=80)
        self.end_point_entry.place(x=245, y=80)

        tk.Button(self.options_win, width=15, bg="#124e71", fg="white", font=self.small_font, text="Starting Point", command=start_point).place(x=5, y=75)
        self.start_point_entry.bind("<Return>", lambda x: start_point())

    def place_table_image(self, frame, path):
        if "http" in path:
            path = "images/blank.png"
        img = Image.open(path)
        img = img.resize((34,30), Image.LANCZOS)
        imgr = PhotoImage(img)
        box = tk.Label(frame, image=imgr)
        box.image = imgr
        return box


def display_error(message, message_type="Error"):
    win32api.MessageBox(0, message, message_type)

def import_file(ui):
    filename = tk.filedialog.askopenfilename(initialdir="C://", title="Select file", filetype=(("CSV files", "*.csv"),("All files", "*.*")))
    if not filename:
        return None
    if filename[-4:] != ".csv":
        display_error("Imported files must be of .csv type.")
        return None

    csv_file_list = get_csv_as_list(filename, True)
    if csv_file_list:
        headers,items = csv_file_list
    else:
        display_error(f"An error occured when importing the file: {filename}")
        return None

    ui.item_specifics = [{} for _ in range(len(items))]    # Never do [{}] * some number
    for i,item in enumerate(items):
        for j,header in enumerate(headers):
            if header:
                if header[:1] == "C:":
                    ui.item_specifics[i][header[2:]] = item[j]
                else:
                    ui.item_specifics[i][header] = item[j]
    ui.show_items()


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
            return final[0],final[1:]
        else:
            return final
    except:
        return None

def write_csv(file, data):
    with open(file, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",")
        for row in data:
            csvwriter.writerow(row)

def clear_widget(widget):
    for child in widget.winfo_children():
        child.destroy()

def is_blank(string):
    return string or string.strip()

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
        assert len(num) == 12
        return num
    except:
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
