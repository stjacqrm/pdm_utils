import sys

from tkinter import Tk

from pdm_utils.classes.filter import Filter
from pdm_utils.gui import gui_basic
from pdm_utils.gui.logger import Logger

def main():
    main_window = Tk()
    main_window.geometry("400x250")
    main_window.title("MySQL Login")
    main_window.configure(bg=gui_basic.BG1)
    gui_basic.center_window(main_window)
    login_window = Logger(main_window)
    login_window.mainloop()

    if not login_window.alchemist.connected_database:
        sys.exit(1)

    test_alchemist_1(login_window.alchemist)
        




def test_alchemist_1(alchemist):
    db_filter = Filter(alchemist=alchemist) 
    db_filter.key = "gene.Notes"
    db_filter.add("domain.Description LIKE '%Ig-like%'")
    db_filter.update()
    print(db_filter.values)




if __name__ == "__main__":
    main()
