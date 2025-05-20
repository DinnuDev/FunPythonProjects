# Adjusted to process entire sample line in a smarter block rather than per character logic

import sys
import re
import pyperclip
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QTextEdit,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt


class StyledButton(QPushButton):
    def __init__(self, icon, tooltip):
        super().__init__(icon)
        self.setToolTip(tooltip)
        self.setFixedSize(40, 40)
        self.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                background-color: #2c3e50;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)


class RegexApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Regex Generator & Validator")
        self.setGeometry(100, 100, 960, 620)
        self.setStyleSheet("""
            QWidget {
                font-family: Segoe UI, sans-serif;
                font-size: 14px;
            }
            QLineEdit, QTextEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QLabel {
                font-weight: bold;
                margin-top: 10px;
            }
        """)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(self.create_generator_tab(), "🛠️ Regex Generator")
        self.tabs.addTab(self.create_validator_tab(), "🧪 Regex Validator")

    def create_generator_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Sample Text"))
        self.sample_text = QTextEdit(placeholderText="Enter sample text here...")
        self.sample_text.textChanged.connect(self.generate_regex)
        layout.addWidget(self.sample_text)

        self.options = {
            "digits": QCheckBox("Digits (\\d)"),
            "letters": QCheckBox("Letters ([a-zA-Z])"),
            "alphanumeric": QCheckBox("Alphanumeric (\\w)"),
            "whitespace": QCheckBox("Whitespace (\\s)"),
            "any": QCheckBox("Any Character (.)"),
            "start": QCheckBox("Start (^)"),
            "end": QCheckBox("End ($)"),
            "case": QCheckBox("Ignore Case"),
            "multiline": QCheckBox("Multiline")
        }

        filters1 = QHBoxLayout()
        filters2 = QHBoxLayout()
        for i, (key, cb) in enumerate(self.options.items()):
            cb.setChecked(True)
            cb.stateChanged.connect(self.generate_regex)
            (filters1 if i < 5 else filters2).addWidget(cb)
        layout.addLayout(filters1)
        layout.addLayout(filters2)

        self.literal_input = QLineEdit(placeholderText="Enter literal string (optional)")
        self.literal_input.textChanged.connect(self.generate_regex)
        layout.addWidget(QLabel("Literal Match"))
        layout.addWidget(self.literal_input)

        btn_layout = QHBoxLayout()
        copy_btn = StyledButton("📋", "Copy Regex")
        copy_btn.clicked.connect(self.copy_regex)
        reset_btn = StyledButton("🗑️", "Reset")
        reset_btn.clicked.connect(self.clear_generator)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(reset_btn)
        layout.addLayout(btn_layout)

        self.regex_output = QLineEdit()
        self.regex_output.setReadOnly(True)
        layout.addWidget(QLabel("Generated Regex"))
        layout.addWidget(self.regex_output)

        return widget

    def create_validator_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.regex_input = QLineEdit(placeholderText="Enter regex pattern...")
        layout.addWidget(QLabel("Regex Pattern"))
        layout.addWidget(self.regex_input)

        self.test_text = QTextEdit(placeholderText="Enter test string(s)...")
        layout.addWidget(QLabel("Test String(s)"))
        layout.addWidget(self.test_text)

        self.flags = {
            "IGNORECASE": QCheckBox("Ignore Case"),
            "MULTILINE": QCheckBox("Multiline"),
            "DOTALL": QCheckBox("Dot All"),
            "VERBOSE": QCheckBox("Verbose")
        }

        flags_layout = QHBoxLayout()
        for cb in self.flags.values():
            flags_layout.addWidget(cb)
        layout.addLayout(flags_layout)

        btn_layout = QHBoxLayout()
        validate_btn = StyledButton("✔️", "Validate")
        validate_btn.clicked.connect(self.validate_regex)
        clear_btn = StyledButton("🧹", "Clear")
        clear_btn.clicked.connect(self.clear_validator)
        btn_layout.addWidget(validate_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(QLabel("Results"))
        layout.addWidget(self.result_display)

        return widget

    def generate_regex(self):
        text = self.sample_text.toPlainText().strip()
        if not text:
            self.regex_output.setText("")
            return

        line = text.splitlines()[0]
        tokens = re.findall(r'\d+|[a-zA-Z]+|\s+|\W+', line)
        parts = []

        for token in tokens:
            if token.isdigit() and self.options["digits"].isChecked():
                parts.append(r"\d+")
            elif token.isalpha() and self.options["letters"].isChecked():
                parts.append(r"[a-zA-Z]+")
            elif token.isspace() and self.options["whitespace"].isChecked():
                parts.append(r"\s+")
            elif re.match(r'^\w+$', token) and self.options["alphanumeric"].isChecked():
                parts.append(r"\w+")
            elif self.options["any"].isChecked():
                parts.append(r".+")
            else:
                parts.append(re.escape(token))

        pattern = "".join(parts)

        if self.options["start"].isChecked():
            pattern = "^" + pattern
        if self.options["end"].isChecked():
            pattern += "$"

        if lit := self.literal_input.text().strip():
            pattern += re.escape(lit)

        self.regex_output.setText(pattern)

    def copy_regex(self):
        pyperclip.copy(self.regex_output.text())
        QMessageBox.information(self, "Copied", "Regex copied to clipboard.")

    def clear_generator(self):
        self.sample_text.clear()
        self.literal_input.clear()
        self.regex_output.clear()

    def validate_regex(self):
        pattern = self.regex_input.text()
        test_text = self.test_text.toPlainText()
        flags = 0
        if self.flags["IGNORECASE"].isChecked(): flags |= re.IGNORECASE
        if self.flags["MULTILINE"].isChecked(): flags |= re.MULTILINE
        if self.flags["DOTALL"].isChecked(): flags |= re.DOTALL
        if self.flags["VERBOSE"].isChecked(): flags |= re.VERBOSE

        try:
            compiled = re.compile(pattern, flags)
            matches = list(compiled.finditer(test_text))
            if not matches:
                self.result_display.setText("No matches found.")
            else:
                result = []
                for i, match in enumerate(matches, 1):
                    result.append(f"Match {i}: '{match.group()}'")
                    for j, group in enumerate(match.groups(), 1):
                        result.append(f"  Group {j}: '{group}'")
                self.result_display.setText("\n".join(result))
        except re.error as e:
            self.result_display.setText(f"Invalid Regex Pattern: {str(e)}")

    def clear_validator(self):
        self.regex_input.clear()
        self.test_text.clear()
        self.result_display.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegexApp()
    window.show()
    sys.exit(app.exec_())
