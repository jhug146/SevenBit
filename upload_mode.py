import tkinter as tk


class UploadMode:
    COUNTRIES = ("US", "UK", "AUS", "FRA", "GER", "ITA", "SPA", "To SQL database", "Fast images", "Download images with items")
    OPTIONS = ("US", "UK", "AUS", "FR", "DE", "IT", "ES", "SQL", "IMG", "DIMG")
    def __init__(self, item_type):
        self.item_type = item_type
        self.fix_mode()

    def fix_mode(self):
        state = [0] * len(self.OPTIONS)
        for i,option in enumerate(self.OPTIONS):
            if option in self.item_type.upload_data["upload_to"]:
                state[i] = 1
        self.upload_state = state

    def change_mode(self):
        self.win = tk.Tk()
        self.win.title("Change Upload Mode")
        self.win.geometry("250x300")

        self.int_vars = []
        for i in range(len(self.upload_state)):
            tk.Label(self.win, text=self.COUNTRIES[i]).grid(row=i, column=0)
            int_var = tk.IntVar(self.win, value=self.upload_state[i])
            tk.Checkbutton(self.win, variable=int_var, command=self.change_button).grid(row=i, column=1)
            self.int_vars.append(int_var)

    def change_button(self):
        for i,var in enumerate(self.int_vars):
            self.upload_state[i] = var.get()
