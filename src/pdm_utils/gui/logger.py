import tkinter
from tkinter import Button
from tkinter import Entry
from tkinter import Label
from tkinter.ttk import Combobox

from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.gui import gui_basic
from pdm_utils.gui import connector

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
        connector_window = connector.create_window(tkinter.Toplevel())

        self.connector = connector.Connector(connector_window, self.alchemist)
        self.connector.mainloop()

        connector_window.withdraw()

        self.master.quit()

def create_window(logger_window):
    logger_window.geometry("400x250")
    logger_window.minsize(400, 250)
    logger_window.title("MySQL Login")
    logger_window.configure(bg=gui_basic.BG1)
    logger_window.attributes("-topmost", "true")

    gui_basic.center_window(logger_window)

    return logger_window

if __name__ == "__main__":
    logger_window = create_window(tkinter.Tk())
    logger = Logger(logger_window)
    logger.mainloop()

