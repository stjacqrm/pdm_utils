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
from tkinter.ttk import Treeview
from tkinter.ttk import Scrollbar

from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.classes.filter import Filter
from pdm_utils.functions import parsing
from pdm_utils.functions import querying
from pdm_utils.gui import connector
from pdm_utils.gui import gui_basic
from pdm_utils.gui import logger
from pdm_utils.pipelines.export_db import decode_results

FILTERABLE_PIPELINES = ["export", "freeze", "resubmit", "resubmit"]

BASE_QUERY_TYPES = ["SELECT  ", "COUNT   ", "DISTINCT"]
BASE_COLUMNS = ["*"]
BASE_CONJUNCTIONS = ["AND", "OR"]

class Explorer(tkinter.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master 

        self.alchemist = None
        self.filter = None
        self.tables = []

        self.login()
        if self.alchemist is None:
            self.quit()

        self.create_widgets() 
        self.display = None

    def create_widgets(self):
        self.create_menu()
        self.create_selector()

        self.display_frame = Frame(self.master)
        self.display_frame.pack(fill=tkinter.BOTH, expand=1)

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
       
    def create_selector(self):
        self.select_frame = Frame(self.master, height=60)
        self.select_frame.config(bd=1, relief=tkinter.RAISED)
        self.select_frame.pack(fill=tkinter.X) 

        self.query_type_var = StringVar(self.master)
        self.query_type_var.set(BASE_QUERY_TYPES[0])
        self.query_type_entry = OptionMenu(self.master, self.query_type_var, 
                                                *BASE_QUERY_TYPES)
        self.query_type_entry.place(in_=self.select_frame, rely=0.3, x=60, 
                                                anchor=tkinter.CENTER)
    
        self.create_columns_selector()
            
        self.where_label = Label(self.master, width=6, text="WHERE")
        self.where_label.place(in_=self.columns_entry, x=250, rely=0.49,
                                                anchor=tkinter.CENTER) 

        self.create_filters_selector()
        
        self.query_button = Button(self.master, text="QUERY", width=3,
                                                command=self.query)
        self.query_button.place(in_=self.where_entry, x=315, rely=0.49,
                                                anchor=tkinter.CENTER)


        self.clear_button = Button(self.master, text="CLEAR", width=3,
                                                command=self.clear)
        self.clear_button.place(in_=self.query_button, x=80, rely=0.49,
                                                anchor=tkinter.CENTER)
         
    def create_columns_selector(self):
        self.columns_entry = Entry(self.master, width=30)
        self.columns_entry.place(in_=self.query_type_entry, x=100, rely=0.49,
                                                anchor=tkinter.W)
       

        self.column_t_entry_var = StringVar(name="column_table")
        self.column_t_entry_var.trace_add("write", self.validate_table_bind) 
        self.column_t_entry = Combobox(self.master, width=10,
                                        textvariable=self.column_t_entry_var,
                                                values=self.tables)
        self.column_t_entry.place(in_=self.query_type_entry, x=101, y=35,
                                                anchor=tkinter.W)


        self.column_separator_label = Label(self.master, text=".")
        self.column_separator_label.place(in_=self.column_t_entry, x=86, y=9,
                                                anchor=tkinter.W)


        self.column_c_entry = Combobox(self.master, width=10)
        self.column_c_entry.place(in_=self.column_t_entry, x=93, rely=0.49,
                                                anchor=tkinter.W)
        self.column_c_entry.configure(state="disabled")


        self.add_column_button = Button(self.master, text="ADD", width=2,
                                                height=1,
                                                font=("Helvetica", 7),
                                                command=self.add_column)
        self.add_column_button.bind("<Return>", self.add_column_invoke)
        self.add_column_button.place(in_=self.column_c_entry, x=90, rely=0.49,
                                                anchor=tkinter.W)

    def create_filters_selector(self):
        self.where_entry_var = StringVar()
        self.where_entry_var.trace_add("write", self.detect_where_entry_bind)
        self.where_entry = Entry(self.master, width=40,
                                        textvariable=self.where_entry_var)
        self.where_entry.place(in_=self.where_label, x=50, rely=0.49,
                                                anchor=tkinter.W)


        self.filter_t_entry_var = StringVar(name="filter_table")
        self.filter_t_entry_var.trace_add("write", self.validate_table_bind)
        self.filter_t_entry = Combobox(self.master, width=10,
                                        textvariable=self.filter_t_entry_var,
                                                values=self.tables)
        self.filter_t_entry.place(in_=self.where_label, x=51, y=31,
                                                anchor=tkinter.W)

       
        self.filter_separator_label = Label(self.master, text=".")
        self.filter_separator_label.place(in_=self.filter_t_entry, x=86, y=9,
                                                anchor=tkinter.W)


        self.filter_c_entry_var = StringVar(name="filter_column")
        self.filter_c_entry_var.trace_add("write", self.validate_column_bind)
        self.filter_c_entry = Combobox(self.master, width=10,
                                        textvariable=self.filter_c_entry_var)
        self.filter_c_entry.place(in_=self.filter_t_entry, x=93, rely=0.49,
                                                anchor=tkinter.W)
        self.filter_c_entry.configure(state="disabled")

        
        self.filter_o_entry = Combobox(self.master, width=5)
        self.filter_o_entry.place(in_=self.filter_c_entry, x=93, rely=0.49,
                                                anchor=tkinter.W)
        self.filter_o_entry.configure(state="disabled")


        self.filter_conj_entry = Combobox(self.master, width=3, 
                                                values=BASE_CONJUNCTIONS)
        self.filter_conj_entry.place(in_=self.filter_t_entry, rely=0.49, x=-5,
                                                anchor=tkinter.E)
        self.filter_conj_entry.configure(state="disabled")


        self.add_filter_button = Button(self.master, text="ADD", width=2, 
                                                height=1,
                                                font=("Helvetica", 7),
                                                command=self.add_filter)
        self.add_filter_button.bind("<Return>", self.add_filter_invoke)
        self.add_filter_button.place(in_=self.filter_o_entry, x=75, rely=0.49,
                                                anchor=tkinter.CENTER)

    def login(self):
        logger_window = logger.create_window(tkinter.Toplevel()) 

        logger_obj = logger.Logger(logger_window)
        logger_obj.mainloop()

        logger_window.withdraw()

        self.alchemist = logger_obj.alchemist
        self.db_filter = Filter(alchemist=self.alchemist)
        self.update_tables()

    def connect(self):
        connector_window = connector.create_window(tkinter.Toplevel())

        connector_obj = connector.Connector(connector_window, self.alchemist)
        connector_obj.mainloop()
        
        connector_window.withdraw()

        self.db_filter.link(alchemist=self.alchemist)

    def update_tables(self):
        for table in self.alchemist.metadata.tables:
            self.tables.append(str(table))

    def validate_table(self, var):
        if var == "column_table":
            columns = BASE_COLUMNS
            table_entry = self.column_t_entry
            column_entry = self.column_c_entry
        elif var == "filter_table":
            columns = []
            table_entry = self.filter_t_entry
            column_entry = self.filter_c_entry

        table = table_entry.get()

        if table in self.tables:
            column_entry.configure(state="normal")
            columns = columns + self.get_columns(table)
            column_entry["values"] = columns
        else:
            column_entry.delete(0, tkinter.END)
            column_entry.configure(state="disabled")
            column_entry["values"] = []
   
    def validate_column(self, var):
        if var == "filter_column":
            table_entry = self.filter_t_entry
            column_entry = self.filter_c_entry
            operator_entry = self.filter_o_entry

        column = column_entry.get()

        if column in column_entry["values"]:
            table = table_entry.get()
            operator_entry.configure(state="normal")
            operators = self.get_operators(table, column)
            operator_entry["values"] = operators
        else:
            operator_entry.delete(0, tkinter.END)
            operator_entry.configure(state="disabled")
            operator_entry["values"] = []

    def get_columns(self, table):
        table_obj = self.alchemist.metadata.tables[f"{table}"]

        columns = []
        for column in list(table_obj.columns):
            columns.append(str(column.name))

        return columns

    def get_operators(self, table, column):
        column_obj = querying.get_column(self.alchemist.metadata,
                                         ".".join([table, column]))

        if column_obj.type.python_type in parsing.COMPARABLE_TYPES:
            operators = parsing.OPERATORS
        else:
            operators = parsing.NONNUMERIC_OPERATORS

        return operators

    def clear(self):
        self.clear_widgets()
        #self.clear_display()

    def clear_widgets(self):
        self.column_t_entry.delete(0, tkinter.END) 
        self.columns_entry.delete(0, tkinter.END)

        self.filter_t_entry.delete(0, tkinter.END)
        self.where_entry.delete(0, tkinter.END)


    def clear_display(self):
        pass

    def add_column(self):
        table = self.column_t_entry.get()
        column = self.column_c_entry.get()

        if table in self.tables and column == "*":
            column_names = []
            for column in list(self.alchemist.metadata.tables[table].columns):
                column_names.append(str(column))

            addition = ", ".join(column_names)

            self.columns_entry.insert(tkinter.END, addition)
        elif table in self.tables and column in self.column_c_entry["values"]:
            if self.columns_entry.get() == "":
                addition = f"{table}.{column}"
            else:
                addition = f", {table}.{column}"

            self.columns_entry.insert(tkinter.END, addition)  
        else:
            pass

    def add_filter(self):
        table = self.filter_t_entry.get()
        column = self.filter_c_entry.get()
        operator = self.filter_o_entry.get()
        conjunction = self.filter_conj_entry.get()

        if table in self.tables and column in self.filter_c_entry["values"] \
                                and operator in self.filter_o_entry["values"]:

            if self.where_entry.get() != "":
                addition = ""
                if conjunction in BASE_CONJUNCTIONS:
                    addition = f" {conjunction} {table}.{column} {operator}"
            else:
                addition = f"{table}.{column} {operator} "

            self.where_entry.insert(tkinter.END, addition)
        else:
            pass

    def detect_where_entry(self):
        if self.where_entry.get() != "":
            self.filter_conj_entry.configure(state="normal")
        else:
            self.filter_conj_entry.delete(0, tkinter.END)
            self.filter_conj_entry.configure(state="disabled")

    def query(self):
        try:
            columns = self.process_columns()
        except:
            self.raise_column_error()
            return

        try:
            self.db_filter.add(self.where_entry.get())
        except:
            self.raise_filter_error()
            return
        
        query_type = self.query_type_var.get()  
        conditionals = self.db_filter.build_where_clauses()
        self.db_filter.reset()
        if query_type == BASE_QUERY_TYPES[0]:
            query = querying.build_select(self.alchemist.graph, columns,
                                                where=conditionals)
        elif query_type == BASE_QUERY_TYPES[1]:
            query = querying.build_count(self.alchemist.graph, columns,
                                                where=conditionals)
        elif query_type == BASE_QUERY_TYPES[2]:
            query = querying.build_distinct(self.alchemist.graph, columns, 
                                                where=conditionals)

        data = querying.execute(self.alchemist.engine, query)
        decode_results(data, columns)
        
        header = []
        for column in columns:
            header.append(str(column))

        self.create_display(data, header)

    def process_columns(self):
        columns_string = self.columns_entry.get()

        split_columns_string = columns_string.split(",")

        columns = []
        for string in split_columns_string:
            columns.append(querying.get_column(self.alchemist.metadata, string))

        return columns

    def create_display(self, data, header):
        if not self.display is None:
            self.display.destroy()
        
        self.display = Treeview(self.display_frame)

        self.create_display_frame()
        self.create_display_headers(header)
        self.create_display_data(data)

    def create_display_frame(self):
        yscrollbar = Scrollbar(self.display_frame, orient="vertical",
                                                   command=self.display.yview)
        yscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

        xscrollbar = Scrollbar(self.display_frame, orient="horizontal",
                                                   command=self.display.xview)
        xscrollbar.pack(side=tkinter.TOP, fill=tkinter.X)

        self.display.configure(yscrollcommand=yscrollbar.set,
                               xscrollcommand=xscrollbar.set)

    def create_display_headers(self, header): 
        self.display.column("#0", width=100, minwidth=100)
        self.display.heading("#0", text=header[0], anchor=tkinter.W)

        if len(header) > 1: 
            self.display["columns"] = tuple(range(1, len(header)))

            for index in range(1, len(header)):
                self.display.column(index, width=100, minwidth=100)
                self.display.heading(index, text=header[index], 
                                                    anchor=tkinter.W)

        self.display.pack(fill=tkinter.BOTH, expand=1)

    def create_display_data(self, data):
        for entry_index in range(len(data)):
            entry = tuple(data[entry_index].values())
            self.display.insert("", "end",
                                text=entry[0], values=entry[1:])

    def raise_column_error(self):
        print("COLUMN ERROR")

    def raise_filter_error(self):
        print("FILTER ERROR")

    def validate_table_bind(self, var, index, mode):
        self.validate_table(var)

    def validate_column_bind(self, var, index, mode):
        self.validate_column(var)

    def detect_where_entry_bind(self, var, index, mode):
        self.detect_where_entry()

    def add_column_invoke(self, var=None, index=None, mode=None):
        self.add_column_button.invoke()
                
    def add_filter_invoke(self, var=None, index=None, mode=None):
        self.add_filter_button.invoke()

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
