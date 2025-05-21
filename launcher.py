import os
import subprocess
import customtkinter as ctk
from tkinter import messagebox
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ScriptLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Python Launcher by Dinesh Kumar")
        self.geometry("500x600")
        self.resizable(False, True)

        self.header = ctk.CTkLabel(self, text="Scripts", font=ctk.CTkFont(size=20, weight="bold"))
        self.header.pack(pady=20)

        self.frame = ctk.CTkScrollableFrame(self, width=450, height=450)
        self.frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.reload_button = ctk.CTkButton(self, text="🔁 Reload Scripts", command=self.load_scripts)
        self.reload_button.pack(pady=(0, 10))

        self.load_scripts()

    def get_script_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def extract_title(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for _ in range(10):  # Read first 10 lines
                    line = f.readline()
                    if not line:
                        break
                    if line.lower().startswith("# title:"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return None

    def load_scripts(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        script_dir = self.get_script_dir()
        current_file = os.path.basename(__file__)
        script_files = [
            f for f in os.listdir(script_dir)
            if f.endswith('.py') and f != current_file
        ]

        if not script_files:
            label = ctk.CTkLabel(self.frame, text="No Python scripts found.", text_color="gray")
            label.pack(pady=10)
            return

        for file in script_files:
            file_path = os.path.join(script_dir, file)
            display_title = self.extract_title(file_path) or file
            btn = ctk.CTkButton(
                self.frame,
                text=display_title,
                command=lambda f=file: self.run_script(f),
                width=400
            )
            btn.pack(pady=5, padx=10)

    def run_script(self, file_name):
        script_path = os.path.join(self.get_script_dir(), file_name)
        try:
            if sys.platform == 'win32':
                subprocess.Popen(
                    ["python", script_path],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                subprocess.Popen(
                    ["python3", script_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            messagebox.showerror("Execution Error", str(e))


if __name__ == "__main__":
    app = ScriptLauncherApp()
    app.mainloop()
