import tkinter as tk


class UploadDisplay(object):

    def __init__(self, listings, ui, upload):
        """
        Creates the display window
        :param listings: 3d_list
        :param ui: UI object
        """
        self.ui = ui
        self.upload = upload
        self.win = tk.Toplevel(self.ui.window)
        self.win.geometry("400x400")
        self.win.title("Upload Progress")
        self.win.iconphoto(False, tk.PhotoImage(file="images/icon.png"))

        self.errors_frame = tk.Frame(self.win, width=self.ui.scrw*0.6, height=self.ui.scrh)
        self.errors_frame.place(x=10, y=0)
        self.progress_frame = tk.Frame(self.win, width=self.ui.scrw*0.4, height=self.ui.scrh)
        self.progress_frame.place(x=1160, y=0)

        self.row_count = 0

        self.scroll = ScrollableFrame(self.errors_frame, 25_000, "black", self.ui.scrw*0.59)
        self.scroll.place(x=0, y=0)
        self.scroll_frame = tk.Frame(self.scroll.scrollable_frame, width=self.ui.scrw*0.6, height=self.ui.scrh, bg="black")
        self.scroll_frame.place(x=0, y=0)

        self.table_frame = tk.Frame(self.progress_frame, width=self.ui.scrw*0.4, height=self.ui.scrh)
        self.table_frame.place(x=0, y=0)
        self.header_frame = tk.Frame(self.table_frame, width=self.ui.scrw*0.4, height=self.ui.scrh*0.1, bg="green")
        self.header_frame.place(x=0, y=50)
        self.content_scroll = ScrollableFrame(self.table_frame, 25_000, "#e5e5e5", self.ui.scrw*0.385)
        self.content_scroll.place(x=0, y=78)
        self.content_frame = tk.Frame(self.content_scroll.scrollable_frame, width=self.ui.scrw*0.385, height=self.ui.scrh)
        self.content_frame.place(x=0, y=0)

        self.stop_button = tk.Button(self.table_frame, command=self.stop_upload, text="Stop Upload", bg="red", fg="white", font=self.ui.big_font).place(x=600, y=5)

        for header in ((43,"Title",0),(7,"SKU",1),(11,"Status",2)):
            tk.Label(self.header_frame, width=int(header[0]), fg="black", font=self.ui.big_font, height=1, text=header[1], borderwidth=1, relief="solid").grid(row=0, column=header[2])

        self.status_vars = []
        self.status_labels = []
        for i,batch in enumerate(listings):
            for country in batch:
                if country:
                    item = country
                    break

            for detail in ((74, item["Title"], 0),(12, item["SKU"], 1)):
                tk.Label(self.content_frame, width=detail[0], height=1, text=detail[1], borderwidth=1, relief="solid").grid(row=i, column=detail[2])
            var = tk.StringVar(self.win, value="")
            var.set("Waiting")
            self.status_vars.append(var)
            label = tk.Label(self.content_frame, width=18, height=1, textvariable=self.status_vars[i], borderwidth=1, relief="solid")
            label.grid(row=i, column=2)
            self.status_labels.append(label)

        self.listings_len = len(listings)

    def mainloop(self):
        self.ui.window.mainloop()

    def push_error(self, error, sku):
        """
        Adds an error onto the console
        :param error: string
        :return: None
        """
        message = f" >>  {sku} --- {error}"
        if message.strip() == ">>":
            message = " >> Blank error?"
        try:
            tk.Message(self.scroll_frame, width=self.ui.scrw*0.59, text=message, font=self.ui.console_font, bg="black", fg="white", anchor="w").grid(row=self.row_count, column=0)
            self.row_count += 1
        except (tk.TclError, RuntimeError):
            print("Error printing message")

    def stop_upload(self):
        """
        Stops the upload and cleans up the window
        :return: None
        """
        self.upload.set_upload(True)  # This causes the upload to stop
        self.win.destroy()
        self.upload.upload_begin = self.ui.item_specifics[self.upload.listing_number]["SKU"]
        del self

    def recolour(self):
        """
        Updates the colurings of the status names in the main table
        Success : Green
        Warning : Orange
        Failure : Red
        Waiting / Other : Black
        :return: None
        """
        for i,label in enumerate(self.status_labels):
            status = self.status_vars[i].get()
            try:
                if status == "Success":
                    label.configure(fg="green")
                elif status == "Warning":
                    label.configure(fg="orange")
                elif status == "Failure":
                    label.configure(fg="red")
                else:
                    label.configure(fg="black")
            except tk.TclError:
                self.stop_upload()

    def set_item_status(self, item_num, status):
        """
        Updates an item's status, calls the the recolour method and increment the progressbar
        :param item_num: integer
        :param status: string
        :return: None
        """
        try:
            self.status_vars[item_num].set(status)
        except RuntimeError:
            self.stop_upload()
        self.recolour()


class ScrollableFrame(tk.Frame):
    def __init__(self, container, scroll_height, colour, width, *args, **kwargs):
        """
        Creates a scrollable frame object with specified height, width and colour
        :param container: tkinter frame object
        :param scroll_height: integer
        :param colour: string
        :param width: integer
        :param args: Any
        :param kwargs: Any
        """
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, width=width, height=1000)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=colour)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), width=3000, height=scroll_height, window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
