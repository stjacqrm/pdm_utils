import tkinter
from tkinter import Button
from tkinter import Entry
from tkinter import Label
from tkinter.ttk import Combobox

from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.gui import gui_basic

class Filterer(tkinter.Frame):
    def __init__(self, master, alchemist):
        super().__init__(master)
        self.master = master

        self.alchemist = alchemist
        self.validate_alchemist()

        self.tables = []
        self.columns = []
        self.operators = []

        self.create_widgets()

    def create_widgets(self):
        self.operator_entry = Combobox(self.master, width=3)
        self.operator_entry.place(rely=0.49, relx=0.49, anchor=tkinter.CENTER)
        self.operator_entry.configure(state="disabled")

        self.column_entry = Combobox(self.master, width=10)
        self.column_entry.place(in_=self.operator_entry, rely=0.49, x=-50, 
                                                    anchor=tkinter.CENTER)
        self.column_entry.configure(state="disabled")

        self.separator_label = Label(self.master, text=".", 
                                                    font=("Helvetica", 30),
                                                    background=gui_basic.BG1)
        self.separator_label.place(in_=self.column_entry, x=-7, y=3,
                                                    anchor=tkinter.CENTER)

        self.table_entry = Combobox(self.master, width=10)
        self.table_entry.place(in_=self.column_entry, rely=0.49, x=-60,
                                                    anchor=tkinter.CENTER)

        
        self.value_entry = Entry(self.master, width=20)
        self.value_entry.place(in_=self.operator_entry, rely=0.49, x=120, 
                                                    anchor=tkinter.CENTER)

    def validate_alchemist(self):
        if not isinstance(self.alchemist, AlchemyHandler):
            self.quit()

        if not self.alchemist.connected:
            self.quit()

        if not self.alchemist.connected_database:
            self.quit()


def create_window(filterer_window):
    filterer_window.geometry("500x250")
    filterer_window.minsize(400, 250)
    filterer_window.title("MySQL Filterer")
    filterer_window.configure(bg=gui_basic.BG1)
    filterer_window.attributes("-topmost", "true")

    gui_basic.center_window(filterer_window)

    return filterer_window
