# title: TicTacToe Game


import tkinter as tk
from tkinter import messagebox
import json
import os
import random

CONFIG_FILE = "tictactoe_config.json"

# Default config
default_config = {
    "player_name": "Player",
    "difficulty": "medium"
}
game_stats = {"Wins": 0, "Losses": 0, "Draws": 0}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        save_config(default_config)
        return default_config.copy()


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


class TicTacToe(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Modern Tic Tac Toe")
        self.geometry("400x620")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self.config_data = load_config()
        self.player_name = self.config_data.get("player_name", "Player")
        self.difficulty = self.config_data.get("difficulty", "medium")

        self.symbol = None
        self.cpu_symbol = None
        self.board = [None] * 9
        self.buttons = []
        self.turn = "player"
        self.colors = {"X": "#00BCD4", "O": "#FF4081"}

        self.create_widgets()

    def create_widgets(self):
        self.create_menu()

        top_frame = tk.Frame(self, bg="#1e1e1e")
        top_frame.pack(fill="x", pady=(10, 0), padx=10)

        self.name_label = tk.Label(top_frame, text=f"{self.player_name}", font=("Helvetica", 14),
                                   fg="white", bg="#1e1e1e", anchor="w")
        self.name_label.pack(side="left", anchor="w")

        self.stats_label = tk.Label(self, text=self.get_stats_text(), font=("Helvetica", 12),
                                    fg="white", bg="#1e1e1e")
        self.stats_label.pack(pady=(5, 10))

        self.symbol_frame = tk.Frame(self, bg="#1e1e1e")
        self.symbol_frame.pack(pady=10)

        symbol_label = tk.Label(self.symbol_frame, text="Choose your symbol:", fg="white", bg="#1e1e1e",
                                font=("Helvetica", 12))
        symbol_label.pack()
        tk.Button(self.symbol_frame, text="X", font=("Helvetica", 24), fg=self.colors["X"],
                  command=lambda: self.set_symbol("X")).pack(side="left", padx=20)
        tk.Button(self.symbol_frame, text="O", font=("Helvetica", 24), fg=self.colors["O"],
                  command=lambda: self.set_symbol("O")).pack(side="right", padx=20)

        self.board_frame = tk.Frame(self, bg="#1e1e1e")

        self.result_label = tk.Label(self, text="", font=("Helvetica", 14), fg="white", bg="#1e1e1e")
        self.result_label.pack(pady=5)

        self.turn_label = tk.Label(self, text="", font=("Helvetica", 12),
                                   fg="white", bg="#1e1e1e")
        self.turn_label.pack(pady=10)

    def create_menu(self):
        menu_bar = tk.Menu(self)
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Edit Player Name", command=self.edit_player_name)

        difficulty_menu = tk.Menu(settings_menu, tearoff=0)
        for level in ["easy", "medium", "hard"]:
            difficulty_menu.add_command(label=level.capitalize(),
                                        command=lambda lvl=level: self.set_difficulty(lvl))
        settings_menu.add_cascade(label="Change Difficulty", menu=difficulty_menu)

        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        self.config(menu=menu_bar)

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.config_data["difficulty"] = difficulty
        save_config(self.config_data)

    def set_symbol(self, symbol):
        self.symbol = symbol
        self.cpu_symbol = "O" if symbol == "X" else "X"
        self.symbol_frame.pack_forget()
        self.render_board()
        self.update_turn_label()

    def render_board(self):
        self.board_frame.pack()
        for i in range(9):
            btn = tk.Button(self.board_frame, text="", font=("Helvetica", 40), width=3, height=1,
                            command=lambda i=i: self.player_move(i), bg="#2e2e2e", fg="white",
                            activebackground="#444")
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)
            self.buttons.append(btn)

    def get_stats_text(self):
        return f"Wins: {game_stats['Wins']}  Losses: {game_stats['Losses']}  Draws: {game_stats['Draws']}"

    def update_turn_label(self):
        if self.symbol is None:
            self.turn_label.config(text="")
        else:
            turn_text = f"{self.player_name}'s Turn" if self.turn == "player" else "CPU's Turn"
            self.turn_label.config(text=turn_text)

    def player_move(self, idx):
        if self.board[idx] is None and self.turn == "player":
            self.animate_button(idx, self.symbol)
            self.board[idx] = self.symbol
            if self.check_winner(self.symbol):
                game_stats["Wins"] += 1
                self.show_result(f"{self.player_name} Wins!")
            elif all(self.board):
                game_stats["Draws"] += 1
                self.show_result("It's a Draw!")
            else:
                self.turn = "cpu"
                self.update_turn_label()
                self.after(500, self.cpu_move)

    def animate_button(self, idx, symbol):
        self.buttons[idx].config(fg=self.colors[symbol], text=symbol)

    def cpu_move(self):
        move = self.get_cpu_move()
        if move is not None:
            self.animate_button(move, self.cpu_symbol)
            self.board[move] = self.cpu_symbol
            if self.check_winner(self.cpu_symbol):
                game_stats["Losses"] += 1
                self.show_result("CPU Wins!")
            elif all(self.board):
                game_stats["Draws"] += 1
                self.show_result("It's a Draw!")
            else:
                self.turn = "player"
                self.update_turn_label()

    def get_cpu_move(self):
        available = [i for i, v in enumerate(self.board) if v is None]
        if not available:
            return None
        if self.difficulty == "easy":
            return random.choice(available)
        elif self.difficulty == "medium":
            return self.block_or_random()
        elif self.difficulty == "hard":
            return self.minimax_move()

    def block_or_random(self):
        for symbol in (self.cpu_symbol, self.symbol):
            for i in range(9):
                if self.board[i] is None:
                    self.board[i] = symbol
                    if self.check_winner(symbol):
                        self.board[i] = None
                        return i
                    self.board[i] = None
        available = [i for i, v in enumerate(self.board) if v is None]
        return random.choice(available) if available else None

    def minimax_move(self):
        def minimax(board, is_max):
            winner = self.check_winner(self.cpu_symbol if is_max else self.symbol, board)
            if winner:
                return (1 if is_max else -1)
            if all(board):
                return 0
            scores = []
            for i in range(9):
                if board[i] is None:
                    board[i] = self.cpu_symbol if is_max else self.symbol
                    score = minimax(board, not is_max)
                    board[i] = None
                    scores.append(score)
            return max(scores) if is_max else min(scores)

        best_score = -float('inf')
        best_move = None
        for i in range(9):
            if self.board[i] is None:
                self.board[i] = self.cpu_symbol
                score = minimax(self.board, False)
                self.board[i] = None
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move

    def check_winner(self, symbol, board=None):
        b = board if board else self.board
        wins = [(0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6)]
        return any(b[i] == b[j] == b[k] == symbol for i, j, k in wins)

    def show_result(self, message):
        self.result_label.config(text=message)
        self.stats_label.config(text=self.get_stats_text())
        self.after(1500, self.reset_game)

    def reset_game(self):
        self.board = [None] * 9
        self.turn = "player"
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()
        self.result_label.config(text="")
        self.stats_label.config(text=self.get_stats_text())
        self.render_board()
        self.update_turn_label()

    def edit_player_name(self):
        entry_window = tk.Toplevel(self)
        entry_window.title("Edit Player Name")
        entry_window.geometry("300x120")
        entry_window.configure(bg="#1e1e1e")

        tk.Label(entry_window, text="Enter new name:", bg="#1e1e1e", fg="white").pack(pady=10)
        name_entry = tk.Entry(entry_window)
        name_entry.insert(0, self.player_name)
        name_entry.pack(pady=5)

        def save_name():
            new_name = name_entry.get().strip()
            if new_name:
                self.player_name = new_name
                self.name_label.config(text=self.player_name)
                self.config_data["player_name"] = self.player_name
                save_config(self.config_data)
                self.update_turn_label()
                entry_window.destroy()

        tk.Button(entry_window, text="Save", command=save_name, bg="#444", fg="white").pack(pady=10)


app = TicTacToe()
app.mainloop()
