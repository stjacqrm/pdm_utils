import tkinter
from tkinter import Button 
from tkinter import Entry
from tkinter import Frame
from tkinter import Label
from tkinter import Menu
from tkinter import OptionMenu
from tkinter import StringVar
from tkinter import Menubutton
from tkinter.ttk import Combobox

from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.gui import connector
from pdm_utils.gui import filterer
from pdm_utils.gui import gui_basic
from pdm_utils.gui import logger

FILTERABLE_PIPELINES = ["export", "freeze", "resubmit", "resubmit"]

BASE_QUERY_TYPES = ["SELECT  ", "COUNT   ", "DISTINCT"]
BASE_COLUMNS = ["*"]
BASE_TABLES = ["Custom Table"]

class Explorer(tkinter.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master 

        self.alchemist = None
        self.tables = []
        self.columns = []

        self.login()
        if self.alchemist is None:
            self.quit()
             
        self.create_menu()
        self.create_widgets()
        self.create_display()
     
    def create_menu(self):        
        self.menu = Menu(self) 
        self.master.config(menu=self.menu)
        
        self.file_menu = Menu(self.menu)
        self.file_menu.add_command(label="Export Data")

        self.database_menu = Menu(self.menu)
        self.database_menu.add_command(label="Switch database", 
                                       command=self.connect)


        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.menu.add_cascade(label="Database", menu=self.database_menu)

    def create_widgets(self):
        self.select_frame = Frame(self.master, height=60)
        self.select_frame.config(bd=1, relief=tkinter.RAISED)
        self.select_frame.pack(fill=tkinter.X)


        self.query_type_var = StringVar(self.master)
        self.query_type_var.set(BASE_QUERY_TYPES[0])
        self.query_type_entry = OptionMenu(self.master, self.query_type_var, 
                                                *BASE_QUERY_TYPES)
        self.query_type_entry.place(in_=self.select_frame, rely=0.3, x=60, 
                                                anchor=tkinter.CENTER)

        self.columns_entry = Entry(self.master, width=30)
        self.columns_entry.place(in_=self.query_type_entry, x=100, rely=0.49,
                                                anchor=tkinter.W)
       

        self.table_entry_var = StringVar()
        self.table_entry_var.trace_add("write", self.validate_table) 
        self.table_entry = Combobox(self.master, width=10,
                                            textvariable=self.table_entry_var,
                                                values=BASE_TABLES+self.tables)
        self.table_entry.place(in_=self.query_type_entry, x=101, y=35,
                                                anchor=tkinter.W)


        self.separator_label = Label(self.master, text=".")
        self.separator_label.place(in_=self.table_entry, x=86, y=9,
                                                anchor=tkinter.W)


        self.column_entry = Combobox(self.master, width=10)
        self.column_entry.place(in_=self.table_entry, x=93, rely=0.49,
                                                anchor=tkinter.W)
        self.column_entry.configure(state="disabled")


        self.add_column_button = Button(self.master, text="ADD", width=2,
                                                height=1,
                                                font=("Helvetica", 7))
        self.add_column_button.place(in_=self.column_entry, x=90, rely=0.49,
                                                anchor=tkinter.W)

        self.where_label = Label(self.master, width=6, text="WHERE")
        self.where_label.place(in_=self.columns_entry, x=250, rely=0.49,
                                                anchor=tkinter.CENTER)
        self.where_entry = Entry(self.master, width=20)
        self.where_entry.place(in_=self.where_label, x=50, rely=0.49,
                                                anchor=tkinter.W)


        self.add_filter_button = Button(self.master, text="ADD", width=2,
                                                command=self.ask_filter)
        self.add_filter_button.place(in_=self.where_entry, x=170, rely=0.49,
                                                anchor=tkinter.CENTER)


        self.query_button = Button(self.master, text="QUERY", width=3)
        self.query_button.place(in_=self.add_filter_button, x=100, rely=0.49,
                                                anchor=tkinter.CENTER)


        self.clear_button = Button(self.master, text="CLEAR", width=3,
                                                command=self.clear)
        self.clear_button.place(in_=self.query_button, x=80, rely=0.49,
                                                anchor=tkinter.CENTER)
                
    def create_display(self):
        pass
    
    def login(self):
        logger_window = logger.create_window(tkinter.Toplevel()) 

        logger_obj = logger.Logger(logger_window)
        logger_obj.mainloop()

        logger_window.withdraw()

        self.alchemist = logger_obj.alchemist
        self.update_tables()

    def connect(self):
        connector_window = connector.create_window(tkinter.Toplevel())

        connector_obj = connector.Connector(connector_window, self.alchemist)
        connector_obj.mainloop()
        
        connector_window.withdraw()

    def update_tables(self):
        for table in self.alchemist.metadata.tables:
            self.tables.append(str(table))

    def validate_table(self, var, index, mode):
        table = self.table_entry.get()

        if table in self.tables:
            self.column_entry.configure(state="normal")
            self.update_columns(table)
        else:
            self.column_entry.configure(state="disabled")
            self.column_entry["values"] = []
    
    def update_columns(self, table):
        table_obj = self.alchemist.metadata.tables[f"{table}"]

        self.columns = BASE_COLUMNS.copy()

        for column in list(table_obj.columns):
            self.columns.append(str(column))
        
        self.column_entry["values"] = self.columns

    def ask_filter(self):
        filterer_window = filterer.create_window(tkinter.Toplevel()) 

        filterer_obj = filterer.Filterer(filterer_window, self.alchemist)
        filterer_obj.mainloop()

        filterer_window.withdraw()

    def clear(self):
        self.clear_widgets()

    def clear_widgets(self):
        self.column_entry.delete(0, tkinter.END)
        self.column_entry["values"] = BASE_COLUMNS
        self.column_entry.configure(state="disabled")

        self.table_entry.delete(0, tkinter.END) 

        self.where_entry.delete(0, tkinter.END)

def create_window(explorer_window):
    explorer_window.geometry("800x800")
    explorer_window.minsize(800, 800)
    explorer_window.title("pdm_utils Explorer")
    explorer_window.configure(bg=gui_basic.BG1)

    gui_basic.center_window(explorer_window)

    return explorer_window

if __name__ == "__main__":
    explorer_window = create_window(tkinter.Tk())
    explorer = Explorer(explorer_window)
    explorer.mainloop()
