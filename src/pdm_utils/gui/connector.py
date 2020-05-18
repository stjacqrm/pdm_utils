import tkinter
from tkinter import Button
from tkinter import Label
from tkinter.ttk import Combobox

from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.gui import gui_basic

class Connector(tkinter.Frame):
    def __init__(self, master, alchemist):
        super().__init__(master)
        self.master = master
    
        self.alchemist = alchemist
        self.validate_alchemist()
 
        self.create_widgets()
    
    def create_widgets(self):
        self.database_entry = Combobox(self.master, 
                                          values=self.alchemist.databases)
        self.database_entry.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.database_label = Label(self.master, text="Database: ",
                                          font=gui_basic.ENTRY_LABEL_FONT,
                                          bg=gui_basic.BG1)
        self.database_label.place(in_=self.database_entry, x=-5, rely=0.5,
                                          anchor=tkinter.E)


        self.connect_button = Button(self.master, text="Connect", 
                                          command=self.connect,
                                          font=gui_basic.BUTTON_FONT_1)
        self.connect_button.place(in_=self.database_entry, y=30, relx=0.5,
                                                      anchor=tkinter.N)


        self.prompt_label = Label(self.master, 
                                          text="Please enter MySQL database: ",
                                          bg=gui_basic.BG1)
        self.prompt_label.place(in_=self.database_entry, y=-30, relx=0.5, 
                                                      anchor=tkinter.S)

    def validate_alchemist(self):
        if not isinstance(self.alchemist, AlchemyHandler):
            self.quit()

        if not self.alchemist.connected:
            self.quit()

        if not self.alchemist.databases:
            self.quit()

    def connect(self):
        self.alchemist.database = self.database_entry.get()

        try:
            self.alchemist.build_engine()
        except:
            self.prompt_label["text"] = ("Invalid MySQL database.  "
                                         "Please try again.")
        else:
            self.quit()

def create_window(connector_window):
    connector_window.geometry("300x250")
    connector_window.minsize(300, 250)
    connector_window.title("MySQL Database Connector")
    connector_window.configure(bg=gui_basic.BG1)
    connector_window.attributes("-topmost", "true")
    
    gui_basic.center_window(connector_window)

    return connector_window
