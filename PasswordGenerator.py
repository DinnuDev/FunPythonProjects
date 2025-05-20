import customtkinter as ctk
import string
import secrets
import pyperclip
from tkinter import messagebox

# Initialize app
ctk.set_appearance_mode("System")  # Options: "Light", "Dark", "System"
ctk.set_default_color_theme("blue")

# Character sets
CHAR_SETS = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "digits": string.digits,
    "special": "!@#$%^&*()-_+=[]{}|;:,.<>?"
}

# Main app window
class PasswordGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🔐 Password Generator")
        self.geometry("500x400")
        self.resizable(False, False)

        self.length = ctk.IntVar(value=12)
        self.include_upper = ctk.BooleanVar(value=True)
        self.include_lower = ctk.BooleanVar(value=True)
        self.include_digits = ctk.BooleanVar(value=True)
        self.include_special = ctk.BooleanVar(value=True)
        self.generated_password = ctk.StringVar()

        self.create_widgets()

    def update_length_label(self, value):
        self.length_value_label.configure(text=f"{int(float(value))} chars")

    def create_widgets(self):
        ctk.CTkLabel(self, text="Password Generator", font=("Arial", 24, "bold")).pack(pady=10)

        # Length slider
        frame = ctk.CTkFrame(self)
        frame.pack(pady=10, fill="x", padx=20)
        length_top = ctk.CTkFrame(frame)
        length_top.pack(fill="x", padx=10)

        ctk.CTkLabel(length_top, text="Password Length").pack(side="left")
        self.length_value_label = ctk.CTkLabel(length_top, text=f"{self.length.get()} chars")
        self.length_value_label.pack(side="right")

        self.length_slider = ctk.CTkSlider(
            frame, from_=8, to=32, variable=self.length, number_of_steps=24,
            command=self.update_length_label
        )
        self.length_slider.pack(fill="x", padx=10)

        # Filters
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkCheckBox(filter_frame, text="Include Uppercase (A-Z)", variable=self.include_upper).pack(anchor="w",
                                                                                                        pady=4)
        ctk.CTkCheckBox(filter_frame, text="Include Lowercase (a-z)", variable=self.include_lower).pack(anchor="w",
                                                                                                        pady=4)
        ctk.CTkCheckBox(filter_frame, text="Include Numbers (0-9)", variable=self.include_digits).pack(anchor="w",
                                                                                                       pady=4)
        ctk.CTkCheckBox(filter_frame, text="Include Special Characters (!@#...)", variable=self.include_special).pack(
            anchor="w", pady=4)

        # Output display
        output_frame = ctk.CTkFrame(self)
        output_frame.pack(pady=10, padx=20, fill="x")
        self.password_entry = ctk.CTkEntry(output_frame, textvariable=self.generated_password, font=("Courier", 14), state="readonly")
        self.password_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(output_frame, text="📋", width=40, command=self.copy_password).pack(side="right", padx=5)

        # Strength label
        self.strength_label = ctk.CTkLabel(self, text="Strength: ", font=("Arial", 12))
        self.strength_label.pack()

        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10)
        ctk.CTkButton(button_frame, text="🎲 Generate", command=self.generate_password).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="🌓 Toggle Mode", command=self.toggle_mode).pack(side="left", padx=10)

    def generate_password(self):
        length = self.length.get()
        options = []

        if self.include_upper.get():
            options.append(("uppercase", CHAR_SETS["uppercase"]))
        if self.include_lower.get():
            options.append(("lowercase", CHAR_SETS["lowercase"]))
        if self.include_digits.get():
            options.append(("digits", CHAR_SETS["digits"]))
        if self.include_special.get():
            options.append(("special", CHAR_SETS["special"]))

        if not options:
            messagebox.showerror("Error", "Please select at least one character type.")
            return

        # Guarantee inclusion
        password_chars = [secrets.choice(charset) for _, charset in options]

        # Fill remaining characters
        all_chars = ''.join(charset for _, charset in options)
        while len(password_chars) < length:
            password_chars.append(secrets.choice(all_chars))

        # Shuffle result
        secrets.SystemRandom().shuffle(password_chars)
        final_password = ''.join(password_chars[:length])

        self.generated_password.set(final_password)
        self.update_strength(final_password)

    def copy_password(self):
        pwd = self.generated_password.get()
        if pwd:
            pyperclip.copy(pwd)
            self.strength_label.configure(text="📋 Copied to clipboard!")

    def update_strength(self, password):
        score = 0
        if any(c.islower() for c in password): score += 1
        if any(c.isupper() for c in password): score += 1
        if any(c.isdigit() for c in password): score += 1
        if any(c in CHAR_SETS["special"] for c in password): score += 1
        if len(password) >= 16: score += 1

        levels = {
            1: "Very Weak",
            2: "Weak",
            3: "Medium",
            4: "Strong",
            5: "Very Strong"
        }
        self.strength_label.configure(text=f"Strength: {levels.get(score, 'Unknown')}")

    def toggle_mode(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")

# Run app
if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()
