import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

CONFIG_FILE = "monitor_config.json"
LOG_FILE = "activity_logs.txt"

default_config = {
    "Application Usage": True,
    "Idle Time Detection": True,
    "Idle Trigger Delay": 10,  # seconds
    "Log Save Interval": 1,  # minutes
    "Idle Buffer Timer": 1  # minutes
}

activity_logs = defaultdict(list)
idle_times = []
app_usage_times = []
last_activity_time = time.time()
start_time = time.time()


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


class SettingsPanel(ttk.Frame):
    def __init__(self, parent, config, callback, cancel_callback):
        super().__init__(parent)
        self.original_config = config.copy()
        self.config = config
        self.callback = callback
        self.cancel_callback = cancel_callback

        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.tree.insert("", "end", "Tracking", text="Tracking")

        self.settings_frame = ttk.Frame(self)
        self.settings_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.feature_vars = {}
        self.tree.bind("<<TreeviewSelect>>", self.display_settings)

        self.btn_frame = ttk.Frame(self.settings_frame)
        self.btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        ttk.Button(self.btn_frame, text="Save", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="Cancel", command=self.cancel_settings).pack(side=tk.RIGHT, padx=5)

        self.displayed_feature = None

        self.idle_minutes = tk.IntVar(value=config.get("Idle Trigger Delay", 10) // 60)
        self.idle_seconds = tk.IntVar(value=config.get("Idle Trigger Delay", 10) % 60)
        self.buffer_minutes = tk.IntVar(value=config.get("Idle Buffer Timer", 1))
        self.log_interval = tk.IntVar(value=config.get("Log Save Interval", 1))

        for key in config:
            if key not in ["Idle Trigger Delay", "Idle Buffer Timer", "Log Save Interval"]:
                self.tree.insert("Tracking", "end", key, text=key)

    def display_settings(self, event):
        for widget in self.settings_frame.winfo_children():
            if widget not in [self.btn_frame]:
                widget.destroy()

        selected = self.tree.selection()
        if not selected:
            return

        feature = selected[0]
        if feature == "Idle Time Detection":
            ttk.Label(self.settings_frame, text="Idle Delay Minutes:").pack()
            ttk.Entry(self.settings_frame, textvariable=self.idle_minutes).pack()
            ttk.Label(self.settings_frame, text="Idle Delay Seconds:").pack()
            ttk.Entry(self.settings_frame, textvariable=self.idle_seconds).pack()
            ttk.Label(self.settings_frame, text="Idle Buffer Timer (Min):").pack()
            ttk.Entry(self.settings_frame, textvariable=self.buffer_minutes).pack()

        if feature == "Application Usage":
            ttk.Label(self.settings_frame, text="Log Save Interval (Min):").pack()
            ttk.Entry(self.settings_frame, textvariable=self.log_interval).pack()

        var = tk.BooleanVar(value=self.config.get(feature, False))
        chk = ttk.Checkbutton(self.settings_frame, text=f"Enable {feature}", variable=var)
        chk.pack(anchor="w", pady=10)
        self.feature_vars[feature] = var
        self.displayed_feature = feature

    def save_settings(self):
        if self.displayed_feature:
            self.config[self.displayed_feature] = self.feature_vars[self.displayed_feature].get()

        delay = self.idle_minutes.get() * 60 + self.idle_seconds.get()
        self.config["Idle Trigger Delay"] = max(5, delay)
        self.config["Idle Buffer Timer"] = max(0, self.buffer_minutes.get())
        self.config["Log Save Interval"] = max(1, self.log_interval.get())

        save_config(self.config)
        self.callback(self.config)

    def cancel_settings(self):
        self.callback(self.original_config)
        self.cancel_callback(self.original_config)


class MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("User Activity & Idle Time Monitor by Dinesh Kumar")
        self.root.geometry("1100x700")
        self.config = load_config()
        self.monitoring = False
        self.last_saved_time = time.time()
        self.start_buffer_time = time.time() + self.config.get("Idle Buffer Timer", 1) * 60

        self.create_widgets()
        self.start_monitoring()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.main_frame = ttk.Frame(self.notebook)
        self.settings_frame = SettingsPanel(self.notebook, self.config.copy(), self.apply_settings, self.cancel_settings)
        self.graph_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.main_frame, text="Monitor")
        self.notebook.add(self.settings_frame, text="Settings")
        self.notebook.add(self.graph_frame, text="Graph")

        self.status_label = tk.Label(self.main_frame, text="Status: Monitoring", font=("Arial", 14))
        self.status_label.pack(pady=10)

        self.log_display = tk.Text(self.main_frame, height=25, font=("Courier New", 10))
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_area = ttk.Frame(self.graph_frame)
        self.plot_area.pack(fill=tk.BOTH, expand=True)
        self.show_graph()

    def start_monitoring(self):
        self.monitoring = True
        threading.Thread(target=self.track_user_activity, daemon=True).start()

    def track_user_activity(self):
        global last_activity_time
        try:
            import pynput.mouse, pynput.keyboard

            def on_activity(event=None):
                global last_activity_time
                last_activity_time = time.time()

            pynput.mouse.Listener(on_move=on_activity, on_click=on_activity).start()
            pynput.keyboard.Listener(on_press=on_activity).start()

            while self.monitoring:
                now = time.time()
                timestamp = datetime.now().strftime("%H:%M:%S")
                idle_threshold = self.config.get("Idle Trigger Delay", 10)

                if self.config.get("Application Usage", False):
                    active_app = self.get_active_window()
                    if active_app:
                        activity_logs["Application Usage"].append((timestamp, active_app))
                        app_usage_times.append((timestamp, 1))
                        self.log_display.insert(tk.END, f"[{timestamp}] App: {active_app} \n")

                if self.config.get("Idle Time Detection", False) and now > self.start_buffer_time:
                    idle_time = now - last_activity_time
                    if idle_time >= idle_threshold:
                        idle_times.append((timestamp, idle_time))
                        self.log_display.insert(tk.END, f"[{timestamp}] Idle: {idle_time:.2f} sec \n")

                if now - self.last_saved_time >= self.config.get("Log Save Interval", 1) * 60:
                    self.save_logs()
                    self.last_saved_time = now

                self.log_display.see(tk.END)
                self.show_graph()
                time.sleep(5)
        except Exception as e:
            self.log_display.insert(tk.END, f"[ERROR] Monitoring failed: {e} \n")

    def save_logs(self):
        try:
            with open(LOG_FILE, "a") as log_file:
                for key, entries in activity_logs.items():
                    for entry in entries:
                        log_file.write(f"[{entry[0]}] {key}: {entry[1]} \n")
                log_file.write("\n")
            activity_logs.clear()
        except Exception as e:
            self.log_display.insert(tk.END, f"[ERROR] Failed to save logs: {e} \n")

    def get_active_window(self):
        try:
            import win32gui
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except Exception:
            return "Unknown (win32gui not available)"

    def apply_settings(self, new_config):
        self.config = new_config
        self.start_buffer_time = time.time() + self.config.get("Idle Buffer Timer", 1) * 60
        self.log_display.insert(tk.END, "[INFO] Settings saved. \n")
        self.log_display.see(tk.END)

    def cancel_settings(self, original_config):
        self.config = original_config
        self.log_display.insert(tk.END, "[INFO] Settings canceled.\n")
        self.log_display.see(tk.END)

    def show_graph(self):
        for widget in self.plot_area.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 4))

        if idle_times:
            times_idle = [t[0] for t in idle_times[-20:]]
            values_idle = [t[1] for t in idle_times[-20:]]
            ax.plot(times_idle, values_idle, marker='o', linestyle='-', label="Idle Time (sec)", color='red')

        if app_usage_times:
            times_app = [t[0] for t in app_usage_times[-20:]]
            values_app = [t[1] for t in app_usage_times[-20:]]
            ax.plot(times_app, values_app, marker='x', linestyle='--', label="Activity", color='green')

        ax.set_title("User Activity and Idle Time (Last 20 Samples)")
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        ax.tick_params(axis='x', rotation=45)

        canvas = FigureCanvasTkAgg(fig, master=self.plot_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = MonitorApp(root)
    root.mainloop()
