import sys
import os
import tkinter as tk
from dynamic_island import DynamicIslandApp

def main():
    root = tk.Tk()
    root.title("Dynamic Island for Windows")

    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_dir, "app_icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    app = DynamicIslandApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
