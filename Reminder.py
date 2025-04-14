import os
import sys
import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import winreg as reg

class RegistryManager:
    """Handle Windows registry operations for auto-start functionality"""
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "ReminderApp"

    @staticmethod
    def get_exe_path():
        """Get the path of the executable or script"""
        return sys.executable if getattr(sys, 'frozen', False) else os.path.realpath(__file__)

    @classmethod
    def set_auto_start(cls, enabled):
        """Set or remove the application from Windows startup"""
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, cls.REG_PATH, 0, reg.KEY_SET_VALUE)
            if enabled:
                reg.SetValueEx(key, cls.APP_NAME, 0, reg.REG_SZ, cls.get_exe_path())
            else:
                reg.DeleteValue(key, cls.APP_NAME)
            reg.CloseKey(key)
            return True
        except WindowsError as e:
            print(f"Error setting startup: {e}")
            return False

    @classmethod
    def is_auto_start_enabled(cls):
        """Check if the application is set to auto-start"""
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, cls.REG_PATH, 0, reg.KEY_READ)
            reg.QueryValueEx(key, cls.APP_NAME)
            reg.CloseKey(key)
            return True
        except WindowsError:
            return False

class ReminderApp:
    DEFAULT_INTERVAL = "10"
    DEFAULT_START_TIME = "09:00"
    DEFAULT_END_TIME = "17:30"

    def __init__(self):
        self.is_running = False
        self.remaining_time = 0
        self.root = tk.Tk()
        self.after_id = None  # Store after ID for cancellation
        self.setup_window()
        self.create_widgets()
        self.update_auto_start_button()

    def setup_window(self):
        """Configure the main window properties"""
        self.root.title("Drink Water Reminder")
        self.root.resizable(False, False)

        window_width, window_height = 400, 350
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

    def create_widgets(self):
        """Create and arrange all UI widgets"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Reminder Interval (minutes):").pack(pady=5)
        self.interval_var = tk.StringVar(value=self.DEFAULT_INTERVAL)
        self.interval_entry = ttk.Entry(main_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.pack()

        ttk.Label(main_frame, text="Start Time (HH:MM):").pack(pady=5)
        self.start_time_var = tk.StringVar(value=self.DEFAULT_START_TIME)
        self.start_time_entry = ttk.Entry(main_frame, textvariable=self.start_time_var, width=10)
        self.start_time_entry.pack()

        ttk.Label(main_frame, text="End Time (HH:MM):").pack(pady=5)
        self.end_time_var = tk.StringVar(value=self.DEFAULT_END_TIME)
        self.end_time_entry = ttk.Entry(main_frame, textvariable=self.end_time_var, width=10)
        self.end_time_entry.pack()

        self.countdown_label = ttk.Label(main_frame, text="Time Remaining: 00:00")
        self.countdown_label.pack(pady=10)

        self.start_button = ttk.Button(main_frame, text="Start Reminder", command=self.toggle_reminder)
        self.start_button.pack(pady=5)

        self.auto_start_label = ttk.Label(main_frame, text="")
        self.auto_start_label.pack(pady=5)
        # Create auto-start button once during initialization
        self.auto_start_button = ttk.Button(main_frame, text="Set Auto-start", command=self.add_auto_start)
        self.auto_start_button.pack(pady=5)

    def validate_inputs(self):
        """Validate all user inputs with specific error messages"""
        try:
            # Validate interval
            try:
                interval = int(self.interval_var.get())
                if interval <= 0:
                    raise ValueError("Interval must be a positive number")
            except ValueError:
                raise ValueError("Please enter a valid number for the interval")

            # Validate time format
            for time_var, field_name in [
                (self.start_time_var, "Start time"),
                (self.end_time_var, "End time")
            ]:
                time_str = time_var.get()
                try:
                    datetime.datetime.strptime(time_str, "%H:%M")
                except ValueError:
                    raise ValueError(f"{field_name} must be in HH:MM format (e.g., 09:00)")

            # Validate time range
            start = datetime.datetime.strptime(self.start_time_var.get(), "%H:%M")
            end = datetime.datetime.strptime(self.end_time_var.get(), "%H:%M")
            if end <= start:
                raise ValueError("End time must be after start time")

            return True
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return False

    def toggle_reminder(self):
        """Toggle between starting and stopping the reminder"""
        if self.is_running:
            self.stop_reminder()
        elif self.validate_inputs():
            self.start_reminder()

    def start_reminder(self):
        """Start the reminder system"""
        self.is_running = True
        self.start_button.config(text="Stop Reminder")
        self.set_input_state("disabled")
        self.remaining_time = int(self.interval_var.get()) * 60
        self.schedule_update()

    def stop_reminder(self):
        """Stop the reminder system"""
        self.is_running = False
        self.start_button.config(text="Start Reminder")
        self.set_input_state("normal")
        self.countdown_label.config(text="Time Remaining: 00:00")
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def set_input_state(self, state):
        """Enable or disable input fields"""
        for entry in (self.interval_entry, self.start_time_entry, self.end_time_entry):
            entry.config(state=state)

    def schedule_update(self):
        """Schedule the next update for countdown and reminder check"""
        if not self.is_running:
            return

        now = datetime.datetime.now().strftime("%H:%M")
        start_time = self.start_time_var.get()
        end_time = self.end_time_var.get()

        if start_time <= now < end_time:
            self.update_countdown()
        else:
            messagebox.showinfo("Reminder", "Outside reminder time range!")
            self.stop_reminder()
            return

        # Schedule next update in 1 second
        self.after_id = self.root.after(1000, self.schedule_update)

    def update_countdown(self):
        """Update the countdown display"""
        if not self.is_running:
            return

        if self.remaining_time > 0:
            self.remaining_time -= 1
            minutes, seconds = divmod(self.remaining_time, 60)
            self.countdown_label.config(text=f"Time Remaining: {minutes:02d}:{seconds:02d}")
        else:
            messagebox.showinfo("Reminder", "Time to drink water!")
            self.remaining_time = int(self.interval_var.get()) * 60

    def update_auto_start_button(self):
        """Update the auto-start button and label based on current state"""
        if RegistryManager.is_auto_start_enabled():
            self.auto_start_label.config(text="Application set to auto-start")
            self.auto_start_button.config(text="Remove Auto-start", command=self.remove_auto_start)
        else:
            self.auto_start_label.config(text="Application not set to auto-start")
            self.auto_start_button.config(text="Set Auto-start", command=self.add_auto_start)

    def add_auto_start(self):
        """Add application to auto-start"""
        if RegistryManager.set_auto_start(True):
            self.update_auto_start_button()

    def remove_auto_start(self):
        """Remove application from auto-start"""
        if RegistryManager.set_auto_start(False):
            self.update_auto_start_button()

def main():
    app = ReminderApp()
    app.root.mainloop()

if __name__ == "__main__":
    main()