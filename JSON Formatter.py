import tkinter as tk
from tkinter import ttk, messagebox
import json
import re

try:
    import js2py
    js_eval_enabled = True
except ImportError:
    js_eval_enabled = False


class JSJSONEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JS/JSON Editor with Formatter and Dummy Generator")
        self.root.geometry("1200x600")
        self.create_widgets()

    def create_widgets(self):
        # Left side: Text Editor
        editor_frame = tk.Frame(self.root)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.text_editor = tk.Text(editor_frame, wrap=tk.NONE, undo=True, font=("Courier New", 12))
        self.text_editor.pack(fill=tk.BOTH, expand=True)

        y_scroll = tk.Scrollbar(editor_frame, command=self.text_editor.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_editor.config(yscrollcommand=y_scroll.set)

        x_scroll = tk.Scrollbar(editor_frame, command=self.text_editor.xview, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_editor.config(xscrollcommand=x_scroll.set)

        # Button panel
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10, anchor='n')

        format_btn = tk.Button(button_frame, text="Format JS/JSON", command=self.format_json, width=25, bg="lightblue")
        format_btn.pack(pady=5)

        generate_btn = tk.Button(button_frame, text="Generate Dummy Data", command=self.generate_dummy_json, width=25, bg="lightgreen")
        generate_btn.pack(pady=5)

        # Tree Viewer
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=("value",), show="tree headings")
        self.tree.heading("#0", text="Key")
        self.tree.heading("value", text="Value")
        self.tree.column("#0", width=300)
        self.tree.column("value", width=400)
        self.tree.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        # Color styling for Treeview tags
        self.tree.tag_configure("str", foreground="#ce9178")
        self.tree.tag_configure("num", foreground="#b5cea8")
        self.tree.tag_configure("bool", foreground="#569cd6")
        self.tree.tag_configure("null", foreground="#808080")
        self.tree.tag_configure("key", font=("Courier New", 10, "bold"))

    def parse_js_or_json(self, text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                if js_eval_enabled:
                    js_obj = js2py.eval_js(f"var obj = {text}; obj;")
                    return json.loads(js_obj.to_json())
                else:
                    # Regex fallback (naive)
                    text = re.sub(r"(\w+)\s*:", r'"\1":', text)
                    text = text.replace("'", '"')
                    return json.loads(text)
            except Exception as e:
                raise json.JSONDecodeError("Invalid JS/JSON format", text, 0)

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
            self.display_json_error(e)

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
            self.display_json_error(e)

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

    def display_json_error(self, error):
        self.text_editor.tag_remove("error", "1.0", tk.END)
        try:
            index = f"{error.lineno}.{error.colno - 1}"
            self.text_editor.tag_add("error", index, f"{error.lineno}.{error.colno}")
            self.text_editor.tag_config("error", background="red", foreground="white")
            self.text_editor.see(index)
        except:
            pass
        messagebox.showerror("Invalid Input", f"{error.msg} at line {error.lineno}, column {error.colno}")

    def insert_into_tree(self, data, parent=""):
        if isinstance(data, dict):
            for key, value in data.items():
                tag, val_str = self.get_value_tag(value)
                node = self.tree.insert(parent, "end", text=key, values=(val_str,), tags=(tag,))
                if isinstance(value, (dict, list)):
                    self.insert_into_tree(value, node)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                tag, val_str = self.get_value_tag(item)
                node = self.tree.insert(parent, "end", text=f"[{idx}]", values=(val_str,), tags=(tag,))
                if isinstance(item, (dict, list)):
                    self.insert_into_tree(item, node)

    def get_value_tag(self, value):
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


if __name__ == "__main__":
    root = tk.Tk()
    app = JSJSONEditorApp(root)
    root.mainloop()
