# title: JSON Formatter


import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import re
import js2py

class JSJSONEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JS/JSON Editor with Formatter, Dummy Generator, and Dark Theme")
        self.root.geometry("1250x650")
        self.theme = "dark"
        self.create_widgets()
        self.apply_theme()

    def create_widgets(self):
        # === Editor Panel ===
        editor_frame = tk.Frame(self.root)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Fix Treeview widget background in frame itself

        self.text_editor = tk.Text(editor_frame, wrap=tk.NONE, undo=True, font=("Courier New", 12))
        self.text_editor.pack(fill=tk.BOTH, expand=True)

        y_scroll = tk.Scrollbar(editor_frame, command=self.text_editor.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_editor.config(yscrollcommand=y_scroll.set)

        x_scroll = tk.Scrollbar(editor_frame, command=self.text_editor.xview, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_editor.config(xscrollcommand=x_scroll.set)

        # === Responsive Horizontal Button Panel ===
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5, padx=5, fill=tk.X)

        buttons = [
            ("Format", self.format_json, "#81d4fa"),
            ("Dummy", self.generate_dummy_json, "#a5d6a7"),
            ("Export", self.export_to_file, "#fff59d"),
            ("Copy", self.copy_to_clipboard, "#e0e0e0"),
            ("Theme", self.toggle_theme, "#ffcc80"),
        ]

        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, command=command, bg=color)
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3, pady=3)

        # === Tree View ===
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=("value",), show="tree headings")
        self.tree.heading("#0", text="Key")
        self.tree.heading("value", text="Value")
        self.tree.column("#0", width=300)
        self.tree.column("value", width=400)
        self.tree.pack(fill=tk.BOTH, expand=True)

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # Style and tags
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("Courier New", 11, "bold"), rowheight=24)
        self.tree.tag_configure("str", foreground="#ffb86c")  # orange
        self.tree.tag_configure("num", foreground="#8be9fd")  # cyan
        self.tree.tag_configure("bool", foreground="#50fa7b")  # green
        self.tree.tag_configure("null", foreground="#6272a4")  # purple

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()

    def apply_theme(self):
        dark_bg = "#282a36"
        light_bg = "white"
        dark_fg = "#f8f8f2"
        light_fg = "black"
        selected_dark = "#44475a"
        selected_light = "#e0e0e0"

        if self.theme == "dark":
            self.root.configure(bg=dark_bg)
            self.text_editor.configure(bg=dark_bg, fg=dark_fg, insertbackground="white")

            self.style.configure("Treeview",
                                 background=dark_bg,
                                 fieldbackground=dark_bg,
                                 foreground=dark_fg,
                                 bordercolor=dark_bg)
            self.style.map("Treeview", background=[("selected", selected_dark)])
        else:
            self.root.configure(bg=light_bg)
            self.text_editor.configure(bg=light_bg, fg=light_fg, insertbackground="black")

            self.style.configure("Treeview",
                                 background=light_bg,
                                 fieldbackground=light_bg,
                                 foreground=light_fg,
                                 bordercolor=light_bg)
            self.style.map("Treeview", background=[("selected", selected_light)])

    def parse_js_or_json(self, text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                js_obj = js2py.eval_js(f"var obj = {text}; obj;")
                return json.loads(js_obj.to_json())
            except Exception:
                text = re.sub(r"(\w+)\s*:", r'"\1":', text)
                text = text.replace("'", '"')
                return json.loads(text)

    def format_json(self):
        self.tree.delete(*self.tree.get_children())
        raw_text = self.text_editor.get("1.0", tk.END).strip()
        try:
            data = self.parse_js_or_json(raw_text)
            formatted = json.dumps(data, indent=4)
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert(tk.END, formatted)
            self.insert_into_tree(data)
        except json.JSONDecodeError as e:
            self.show_error(e)

    def generate_dummy_json(self):
        self.tree.delete(*self.tree.get_children())
        raw_text = self.text_editor.get("1.0", tk.END).strip()
        try:
            data = self.parse_js_or_json(raw_text)
            dummy = self.generate_dummy(data)
            formatted = json.dumps(dummy, indent=4)
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert(tk.END, formatted)
            self.insert_into_tree(dummy)
        except json.JSONDecodeError as e:
            self.show_error(e)

    def generate_dummy(self, data):
        if isinstance(data, dict):
            return {k: self.generate_dummy(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.generate_dummy(data[0])] if data else []
        elif isinstance(data, str):
            return "example"
        elif isinstance(data, (int, float)):
            return 123
        elif isinstance(data, bool):
            return True
        elif data is None:
            return None
        return data

    def insert_into_tree(self, data, parent=""):
        if isinstance(data, dict):
            for key, value in data.items():
                tag, val = self.get_tag_and_str(value)
                node = self.tree.insert(parent, "end", text=key, values=(val,), tags=(tag,))
                if isinstance(value, (dict, list)):
                    self.insert_into_tree(value, node)
        elif isinstance(data, list):
            for item in data:
                tag, val = self.get_tag_and_str(item)
                node = self.tree.insert(parent, "end", text="", values=(val,), tags=(tag,))
                if isinstance(item, (dict, list)):
                    self.insert_into_tree(item, node)

    def get_tag_and_str(self, value):
        if isinstance(value, str):
            return "str", f'"{value}"'
        elif isinstance(value, (int, float)):
            return "num", str(value)
        elif isinstance(value, bool):
            return "bool", str(value).lower()
        elif value is None:
            return "null", "null"
        elif isinstance(value, dict):
            return "", "{...}"
        elif isinstance(value, list):
            return "", "[...]"
        return "", str(value)

    def export_to_file(self):
        content = self.text_editor.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Export Failed", "Editor is empty!")
            return
        try:
            data = self.parse_js_or_json(content)
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                messagebox.showinfo("Export Successful", f"Saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Invalid data:\n{e}")

    def copy_to_clipboard(self):
        content = self.text_editor.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Copy Failed", "Editor is empty!")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()
        messagebox.showinfo("Copied", "Content copied to clipboard!")

    def show_error(self, error):
        self.text_editor.tag_remove("error", "1.0", tk.END)
        try:
            index = f"{error.lineno}.{error.colno - 1}"
            self.text_editor.tag_add("error", index, f"{error.lineno}.{error.colno}")
            self.text_editor.tag_config("error", background="red", foreground="white")
            self.text_editor.see(index)
        except:
            pass
        messagebox.showerror("Invalid Input", f"{error.msg} at line {error.lineno}, column {error.colno}")


if __name__ == "__main__":
    root = tk.Tk()
    app = JSJSONEditorApp(root)
    root.mainloop()
