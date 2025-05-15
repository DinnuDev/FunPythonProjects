import tkinter as tk
from itertools import permutations
import random

# Precompute all patterns grouped by length (3 to 9)
# But mapped from 0-8 internally (we’ll use 1-9 for user input/output)
all_patterns_by_length = {
    r: [p for p in permutations(range(9), r)] for r in range(3, 10)
}

class PatternLockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pattern Lock Combinations")

        self.current_index = 0
        self.selected_length = 3
        self.patterns = all_patterns_by_length[self.selected_length]

        # --- Top Controls ---
        control_frame = tk.Frame(root)
        control_frame.pack(pady=5)

        tk.Label(control_frame, text="Dots:").grid(row=0, column=0, padx=5)
        self.length_var = tk.StringVar(value=str(self.selected_length))
        self.length_menu = tk.OptionMenu(control_frame, self.length_var, *range(3, 10), command=self.change_length)
        self.length_menu.grid(row=0, column=1, padx=5)

        self.prev_btn = tk.Button(control_frame, text="Previous", command=self.show_prev)
        self.prev_btn.grid(row=0, column=2, padx=5)

        self.next_btn = tk.Button(control_frame, text="Next", command=self.show_next)
        self.next_btn.grid(row=0, column=3, padx=5)

        self.random_btn = tk.Button(control_frame, text="Random", command=self.show_random)
        self.random_btn.grid(row=0, column=4, padx=5)

        self.all_btn = tk.Button(control_frame, text="Show All", command=self.show_all)
        self.all_btn.grid(row=0, column=5, padx=5)

        # --- Canvas to display pattern ---
        self.canvas = tk.Canvas(root, width=300, height=300, bg="white")
        self.canvas.pack(pady=10)

        self.status = tk.Label(root, text="", font=("Arial", 12))
        self.status.pack()

        # --- Horizontal Input Boxes ---
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=10)

        self.input_boxes = []
        for i in range(9):
            entry = tk.Entry(self.input_frame, width=2, font=("Arial", 16), justify="center")
            entry.grid(row=0, column=i, padx=3)
            entry.bind("<KeyRelease>", self.handle_input_navigation)
            self.input_boxes.append(entry)

        # Go and Clear buttons
        self.action_frame = tk.Frame(root)
        self.action_frame.pack(pady=5)

        self.input_btn = tk.Button(self.action_frame, text="Go", command=self.submit_pattern_input)
        self.input_btn.pack(side="left", padx=5)

        self.clear_btn = tk.Button(self.action_frame, text="Clear", command=self.clear_inputs)
        self.clear_btn.pack(side="left", padx=5)

        self.draw_pattern(self.patterns[self.current_index])

    def change_length(self, value):
        self.selected_length = int(value)
        self.patterns = all_patterns_by_length[self.selected_length]
        self.current_index = 0
        self.draw_pattern(self.patterns[self.current_index])
    def resolve_skipped_points(self, path):
        # Midpoint map for skipped connections
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

        # Remove duplicates while preserving order
        final = []
        seen = set()
        for val in resolved:
            if val not in seen:
                final.append(val)
                seen.add(val)
        return final

    def draw_pattern(self, pattern):
        self.canvas.delete("all")
        radius = 15
        spacing = 100
        coords = {}

        # 3x3 Dot grid layout
        dot_positions = {
            0: (0, 0), 1: (1, 0), 2: (2, 0),
            3: (0, 1), 4: (1, 1), 5: (2, 1),
            6: (0, 2), 7: (1, 2), 8: (2, 2),
        }

        # Draw 9 dots with numbers inside (1–9)
        for idx, (col, row) in dot_positions.items():
            x, y = col * spacing + 50, row * spacing + 50
            color = "lightblue" if idx in pattern else "gray"
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color)
            self.canvas.create_text(x, y, text=str(idx + 1), font=("Arial", 12, "bold"), fill="black")
            coords[idx] = (x, y)

        # Draw lines for the pattern
        for i in range(len(pattern) - 1):
            x1, y1 = coords[pattern[i]]
            x2, y2 = coords[pattern[i + 1]]
            self.canvas.create_line(x1, y1, x2, y2, width=3, fill="blue")

        # Update status label
        readable = tuple(i + 1 for i in pattern)  # convert to 1–9 display
        self.status.config(
            text=(
                f"Length: {len(pattern)} | "
                f"Pattern {self.current_index + 1 if pattern in self.patterns else 'Custom'} "
                f"of {len(self.patterns)} | Pattern: {readable}"
            )
        )

    def show_next(self):
        self.current_index = (self.current_index + 1) % len(self.patterns)
        self.draw_pattern(self.patterns[self.current_index])

    def show_prev(self):
        self.current_index = (self.current_index - 1) % len(self.patterns)
        self.draw_pattern(self.patterns[self.current_index])

    def show_random(self):
        self.patterns = all_patterns_by_length[self.selected_length]
        self.current_index = random.randint(0, len(self.patterns) - 1)
        self.draw_pattern(self.patterns[self.current_index])

    def show_all(self):
        all_window = tk.Toplevel(self.root)
        all_window.title(f"All Patterns of Length {self.selected_length}")
        text = tk.Text(all_window, wrap="none", font=("Courier", 10), width=40, height=30)
        text.pack(padx=10, pady=10)
        for idx, pattern in enumerate(self.patterns, 1):
            readable = tuple(i + 1 for i in pattern)
            text.insert("end", f"{idx}: {readable}\n")

    def handle_input_navigation(self, event):
        widget = event.widget
        key = event.keysym
        index = self.input_boxes.index(widget)

        if key == "BackSpace":
            if widget.get() == "" and index > 0:
                self.input_boxes[index - 1].focus_set()
        elif len(widget.get()) == 1:
            if index < len(self.input_boxes) - 1:
                self.input_boxes[index + 1].focus_set()

    def submit_pattern_input(self):
        values = [box.get().strip() for box in self.input_boxes if box.get().strip() != '']
        try:
            raw = ' '.join(values).replace(",", " ").split()
            digits = [int(v) - 1 for v in raw]  # Convert 1–9 to 0–8
            if len(digits) < 2:
                raise ValueError("Enter at least 2 digits.")
            if len(digits) != len(set(digits)):
                raise ValueError("Digits must be unique.")
            if any(d not in range(9) for d in digits):
                raise ValueError("Digits must be between 1 and 9.")

            # Auto-resolve skipped/intermediate dots
            resolved = self.resolve_skipped_points(digits)

            # Update input boxes visually
            for i, box in enumerate(self.input_boxes):
                if i < len(resolved):
                    box.delete(0, tk.END)
                    box.insert(0, str(resolved[i] + 1))  # back to 1-based
                else:
                    box.delete(0, tk.END)

            self.draw_pattern(tuple(resolved))
        except Exception as e:
            self.status.config(text=f"❌ Invalid input: {e}")

    def clear_inputs(self):
        for box in self.input_boxes:
            box.delete(0, tk.END)
        self.input_boxes[0].focus_set()
        self.status.config(text="Input cleared. Enter new pattern.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PatternLockApp(root)
    root.mainloop()
