import tkinter
from tkinter import Button
from tkinter import Entry
from tkinter import Label
from tkinter.ttk import Combobox

from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.gui import gui_basic

class Logger(tkinter.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack()

        self.create_widgets()

        self.alchemist = AlchemyHandler()
        self.login_attempts = 5

    def create_widgets(self):
        self.user_entry = Entry(self.master)
        self.user_entry.place(relx=0.5, rely=0.45, 
                                            anchor=tkinter.CENTER)

        self.user_label = Label(self.master, text="Username: ",
                                             font=gui_basic.ENTRY_LABEL_FONT,
                                             bg=gui_basic.BG1)
        self.user_label.place(in_=self.user_entry, x=-5, rely=0.5,
                                            anchor=tkinter.E)
  

        self.pass_entry = Entry(self.master, show="*")
        self.pass_entry.place(relx=0.5, rely=0.60, 
                                            anchor=tkinter.CENTER)

        self.pass_label = Label(self.master, text="Password: ",
                                             font=gui_basic.ENTRY_LABEL_FONT,
                                             bg=gui_basic.BG1)
        self.pass_label.place(in_=self.pass_entry, x=-5, rely=0.5,
                                            anchor=tkinter.E)

            
        self.prompt_label = Label(self.master, 
                                  text="Please enter MySQL credentials: ",
                                  bg=gui_basic.BG1)
        self.prompt_label.place(in_=self.user_entry, y=-30, relx=0.5,
                                            anchor=tkinter.S)


        self.login_button = Button(self.master, text="Login", 
                                                command=self.login,
                                                font=gui_basic.BUTTON_FONT_1)
        self.login_button.place(in_=self.pass_entry, y=30, relx=0.5,
                                            anchor=tkinter.N)

    def login(self):
        self.alchemist.username = self.user_entry.get()
        self.alchemist.password = self.pass_entry.get()

        try:
            self.alchemist.build_engine()
        except:
            self.prompt_label["text"] = ("Invalid MySQL credentials.  "
                                         "Please try again.")
            self.login_attempts -= 1
        else:
            self.prompt_label["text"] = ("Logged in!  Please enter a database.")
            self.connect()

    def connect(self):
        connector_window = Connector(self.alchemist)
        gui_basic.center_window(connector_window)
        connector_window.mainloop()

        self.master.quit()

class Connector(tkinter.Toplevel):
    def __init__(self, alchemist):
        super().__init__()

        self.geometry("300x250")
        self.title("MySQL Database Connector")

        self.alchemist = alchemist
        self.validate_alchemist()
 
        self.create_widgets()
    
    def create_widgets(self):
        self.database_entry = Combobox(self, values=self.alchemist.databases)
        self.database_entry.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.database_label = Label(self, text="Database: ",
                                          font=gui_basic.ENTRY_LABEL_FONT,
                                          bg=gui_basic.BG1)
        self.database_label.place(in_=self.database_entry, x=-5, rely=0.5,
                                                      anchor=tkinter.E)


        self.connect_button = Button(self, text="Connect", command=self.connect,
                                           font=gui_basic.BUTTON_FONT_1)
        self.connect_button.place(in_=self.database_entry, y=30, relx=0.5,
                                                      anchor=tkinter.N)


        self.prompt_label = Label(self, text="Please enter MySQL database: ",
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
