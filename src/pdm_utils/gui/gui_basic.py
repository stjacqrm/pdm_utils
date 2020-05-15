from tkinter import font

ENTRY_LABEL_FONT = ("Helvetica", 10)
BUTTON_FONT_1 = ("Helvetica", 10, "bold")

BG1 = "grey67"


def center_window(window):
    window.update_idletasks()

    width = window.winfo_width()
    height = window.winfo_height()

    x = (window.winfo_screenwidth()  // 2)  -  (width  // 2)
    y = (window.winfo_screenheight() // 2)  -  (height // 2)

    window.geometry(f"{width}x{height}+{x}+{y}")
