# title: Dot Connect


import tkinter as tk
from itertools import permutations
import random
import math

class PatternLockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pattern Lock by Dinesh Vutukuru")
        self.root.geometry("500x600")
        self.root.resizable(False, False)

        self.dot_radius = 20
        self.spacing = 100
        self.dots = {}
        self.active_path = []
        self.selected_length = 3
        self.current_index = 0

        self.patterns_by_length = {
            r: [p for p in permutations(range(9), r)] for r in range(3, 10)
        }
        self.patterns = self.patterns_by_length[self.selected_length]

        self.setup_ui()
        self.draw_pattern(self.patterns[self.current_index])

    def setup_ui(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=5)

        tk.Label(control_frame, text="Dots:").grid(row=0, column=0)
        self.length_var = tk.StringVar(value=str(self.selected_length))
        tk.OptionMenu(control_frame, self.length_var, *range(3, 10), command=self.change_length).grid(row=0, column=1)

        tk.Button(control_frame, text="Previous", command=self.show_prev).grid(row=0, column=2)
        tk.Button(control_frame, text="Next", command=self.show_next).grid(row=0, column=3)
        tk.Button(control_frame, text="Random", command=self.show_random).grid(row=0, column=4)
        tk.Button(control_frame, text="Show All", command=self.show_all).grid(row=0, column=5)

        self.canvas = tk.Canvas(self.root, width=300, height=300, bg="white")
        self.canvas.pack(pady=10)
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw_motion)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)

        self.status = tk.Label(self.root, text="", font=("Arial", 12))
        self.status.pack(pady=5)

        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(pady=5)

        self.input_boxes = []
        for i in range(9):
            entry = tk.Entry(self.input_frame, width=2, font=("Arial", 14), justify="center")
            entry.grid(row=0, column=i, padx=2)
            entry.bind("<KeyRelease>", self.handle_input_navigation)
            self.input_boxes.append(entry)

        action_frame = tk.Frame(self.root)
        action_frame.pack(pady=10)

        tk.Button(action_frame, text="Go", command=self.submit_pattern_input).pack(side="left", padx=5)
        tk.Button(action_frame, text="Clear", command=self.clear_inputs).pack(side="left", padx=5)

    def draw_grid(self):
        self.canvas.delete("all")
        self.dots = {}
        for i in range(3):
            for j in range(3):
                idx = i * 3 + j
                x = j * self.spacing + 50
                y = i * self.spacing + 50
                self.dots[idx] = (x, y)
                self.canvas.create_oval(x - self.dot_radius, y - self.dot_radius,
                                        x + self.dot_radius, y + self.dot_radius,
                                        fill="gray")
                self.canvas.create_text(x, y, text=str(idx + 1), font=("Arial", 12, "bold"))

    def draw_pattern(self, pattern):
        self.draw_grid()
        for i in range(len(pattern) - 1):
            x1, y1 = self.dots[pattern[i]]
            x2, y2 = self.dots[pattern[i + 1]]
            self.canvas.create_line(x1, y1, x2, y2, width=3, fill="blue")

        for idx in pattern:
            x, y = self.dots[idx]
            self.canvas.create_oval(x - self.dot_radius, y - self.dot_radius,
                                    x + self.dot_radius, y + self.dot_radius,
                                    fill="lightblue")
            self.canvas.create_text(x, y, text=str(idx + 1), font=("Arial", 12, "bold"))

        for i, box in enumerate(self.input_boxes):
            if i < len(pattern):
                box.delete(0, tk.END)
                box.insert(0, str(pattern[i] + 1))
            else:
                box.delete(0, tk.END)

        readable = tuple(i + 1 for i in pattern)
        index_text = f"{self.current_index + 1}" if pattern in self.patterns else "Custom"
        self.status.config(text=f"Length: {len(pattern)} | Pattern {index_text} of {len(self.patterns)} | Pattern: {readable}")

    def change_length(self, value):
        self.selected_length = int(value)
        self.patterns = self.patterns_by_length[self.selected_length]
        self.current_index = 0
        self.draw_pattern(self.patterns[self.current_index])

    def show_prev(self):
        self.current_index = (self.current_index - 1) % len(self.patterns)
        self.draw_pattern(self.patterns[self.current_index])

    def show_next(self):
        self.current_index = (self.current_index + 1) % len(self.patterns)
        self.draw_pattern(self.patterns[self.current_index])

    def show_random(self):
        base = random.sample(range(9), self.selected_length)
        resolved = self.resolve_skipped_points(base)
        self.draw_pattern(resolved)

    def show_all(self):
        top = tk.Toplevel(self.root)
        top.title("All Patterns")
        text = tk.Text(top, width=40, height=30)
        text.pack(padx=10, pady=10)
        for i, pat in enumerate(self.patterns, 1):
            readable = tuple(p + 1 for p in pat)
            text.insert("end", f"{i}: {readable}\n")

    def handle_input_navigation(self, event):
        widget = event.widget
        idx = self.input_boxes.index(widget)
        if event.keysym == "BackSpace" and widget.get() == "" and idx > 0:
            self.input_boxes[idx - 1].focus_set()
        elif len(widget.get()) == 1 and idx < 8:
            self.input_boxes[idx + 1].focus_set()

    def clear_inputs(self):
        for box in self.input_boxes:
            box.delete(0, tk.END)
        self.status.config(text="Input cleared.")

    def submit_pattern_input(self):
        try:
            values = [box.get() for box in self.input_boxes if box.get().strip()]
            digits = [int(v) - 1 for v in values]
            if len(digits) < 2 or len(set(digits)) != len(digits):
                raise ValueError("Enter 2–9 unique digits (1–9).")
            if any(d < 0 or d > 8 for d in digits):
                raise ValueError("Digits must be between 1 and 9.")
            resolved = self.resolve_skipped_points(digits)
            self.draw_pattern(resolved)
        except Exception as e:
            self.status.config(text=f"❌ {e}")

    def start_draw(self, event):
        self.active_path = []
        self.draw_grid()
        idx = self.get_dot_index(event.x, event.y)
        if idx is not None:
            self.active_path.append(idx)

    def draw_motion(self, event):
        idx = self.get_dot_index(event.x, event.y)
        if idx is not None and idx not in self.active_path:
            self.active_path.append(idx)
            resolved = self.resolve_skipped_points(self.active_path)
            self.draw_pattern(resolved)

    def end_draw(self, event):
        if self.active_path:
            resolved = self.resolve_skipped_points(self.active_path)
            self.draw_pattern(resolved)
            self.active_path = []

    def get_dot_index(self, x, y):
        for idx, (cx, cy) in self.dots.items():
            if math.hypot(x - cx, y - cy) <= self.dot_radius:
                return idx
        return None

    def resolve_skipped_points(self, path):
        midpoint_map = {
            (0, 2): 1, (2, 0): 1,
            (0, 6): 3, (6, 0): 3,
            (2, 8): 5, (8, 2): 5,
            (6, 8): 7, (8, 6): 7,
            (0, 8): 4, (8, 0): 4,
            (2, 6): 4, (6, 2): 4,
            (1, 7): 4, (7, 1): 4,
            (3, 5): 4, (5, 3): 4,
        }
        resolved = [path[0]]
        for i in range(1, len(path)):
            a, b = path[i - 1], path[i]
            mid = midpoint_map.get((a, b))
            if mid is not None and mid not in resolved and mid not in path[:i]:
                resolved.append(mid)
            resolved.append(b)
        final = []
        seen = set()
        for val in resolved:
            if val not in seen:
                final.append(val)
                seen.add(val)
        return final


if __name__ == "__main__":
    root = tk.Tk()
    app = PatternLockApp(root)
    root.mainloop()
