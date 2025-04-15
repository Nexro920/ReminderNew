import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk
import winreg as reg
from PIL import Image, ImageDraw
import pystray
import threading

class RegistryManager:
    """Handle Windows registry operations for auto-start functionality."""
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "ReminderApp"

    @staticmethod
    def get_exe_path() -> str:
        """Get the path of the executable or script."""
        return sys.executable if getattr(sys, 'frozen', False) else os.path.realpath(__file__)

    @classmethod
    def set_auto_start(cls, enabled: bool) -> bool:
        """Set or remove the application from Windows startup."""
        try:
            with reg.OpenKey(reg.HKEY_CURRENT_USER, cls.REG_PATH, 0, reg.KEY_SET_VALUE) as key:
                if enabled:
                    reg.SetValueEx(key, cls.APP_NAME, 0, reg.REG_SZ, cls.get_exe_path())
                else:
                    reg.DeleteValue(key, cls.APP_NAME)
            return True
        except WindowsError as e:
            print(f"Error setting startup: {e}")
            return False

    @classmethod
    def is_auto_start_enabled(cls) -> bool:
        """Check if the application is set to auto-start."""
        try:
            with reg.OpenKey(reg.HKEY_CURRENT_USER, cls.REG_PATH, 0, reg.KEY_READ) as key:
                reg.QueryValueEx(key, cls.APP_NAME)
            return True
        except WindowsError:
            return False

class NotificationWindow:
    """Custom notification window styled like the main application."""
    MIN_WIDTH = 200
    WRAP_LENGTH = 300
    PADDING = 10
    SPACING = 5

    def __init__(self, parent: tk.Tk, title: str, message: str, on_close_callback: callable = None):
        """Initialize a notification window."""
        self.parent = parent
        self.on_close_callback = on_close_callback
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.resizable(False, False)

        # Main frame
        frame = ttk.Frame(self.top, padding=self.PADDING)
        frame.pack(fill=tk.BOTH, expand=True)

        # Message label
        ttk.Label(frame, text=message, wraplength=self.WRAP_LENGTH, justify="center").pack(pady=self.SPACING)

        # OK button
        ttk.Button(frame, text="OK", command=self.close).pack(pady=self.SPACING)

        # Center and bind events
        self.center_window()
        self.top.protocol("WM_DELETE_WINDOW", self.close)

    def center_window(self):
        """Center the window on the screen."""
        self.top.update_idletasks()
        width = max(self.MIN_WIDTH, self.top.winfo_reqwidth())
        height = self.top.winfo_reqheight()
        x = (self.top.winfo_screenwidth() - width) // 2
        y = (self.top.winfo_screenheight() - height) // 2
        self.top.geometry(f"{width}x{height}+{x}+{y}")

    def close(self):
        """Close the notification window and trigger callback."""
        self.top.destroy()
        if self.on_close_callback:
            self.on_close_callback()

class ReminderApp:
    """Drink water reminder app with system tray and notifications."""
    # Configuration constants
    CONFIG = {
        "interval": "10",
        "start_time": "09:00",
        "end_time": "17:30",
        "window_width": 400,
        "window_height": 350,
        "app_name": "Drink Water Reminder",
        "icon_color": (0, 128, 255),
        "icon_ellipse_color": (255, 255, 255),
        "entry_width": 10,
        "padding": 10,
        "spacing": 5
    }

    def __init__(self):
        self.is_running = False
        self.remaining_time = 0
        self.window_hidden = False
        self.after_id = None
        self.tray_icon = None
        self.root = tk.Tk()
        self._initialize_ui()
        self.update_auto_start_button()

    def _initialize_ui(self):
        """Set up the main window and widgets."""
        self.root.title(self.CONFIG["app_name"])
        self.root.resizable(False, False)

        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.CONFIG["window_width"]) // 2
        y = (screen_height - self.CONFIG["window_height"]) // 2
        self.root.geometry(f"{self.CONFIG['window_width']}x{self.CONFIG['window_height']}+{x}+{y}")

        # Bind events
        # self.root.bind("<Unmap>", lambda event: self.minimize_to_tray() if self.root.state() == "iconic" else None)
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.create_widgets()

    def create_widgets(self):
        """Create and arrange UI widgets."""
        frame = ttk.Frame(self.root, padding=self.CONFIG["padding"])
        frame.pack(fill=tk.BOTH, expand=True)

        # Interval input
        ttk.Label(frame, text="Reminder Interval (minutes):").pack(pady=self.CONFIG["spacing"])
        self.interval_var = tk.StringVar(value=self.CONFIG["interval"])
        self.interval_entry = ttk.Entry(frame, textvariable=self.interval_var, width=self.CONFIG["entry_width"])
        self.interval_entry.pack()

        # Start time input
        ttk.Label(frame, text="Start Time (HH:MM):").pack(pady=self.CONFIG["spacing"])
        self.start_time_var = tk.StringVar(value=self.CONFIG["start_time"])
        self.start_time_entry = ttk.Entry(frame, textvariable=self.start_time_var, width=self.CONFIG["entry_width"])
        self.start_time_entry.pack()

        # End time input
        ttk.Label(frame, text="End Time (HH:MM):").pack(pady=self.CONFIG["spacing"])
        self.end_time_var = tk.StringVar(value=self.CONFIG["end_time"])
        self.end_time_entry = ttk.Entry(frame, textvariable=self.end_time_var, width=self.CONFIG["entry_width"])
        self.end_time_entry.pack()

        # Countdown display
        self.countdown_label = ttk.Label(frame, text="Time Remaining: 00:00")
        self.countdown_label.pack(pady=self.CONFIG["spacing"] * 2)

        # Start/Stop button
        self.start_button = ttk.Button(frame, text="Start Reminder", command=self.toggle_reminder)
        self.start_button.pack(pady=self.CONFIG["spacing"])

        # Auto-start status
        self.auto_start_label = ttk.Label(frame, text="")
        self.auto_start_label.pack(pady=self.CONFIG["spacing"])
        self.auto_start_button = ttk.Button(frame, text="Set Auto-start", command=self.add_auto_start)
        self.auto_start_button.pack()

    def create_tray_icon(self):
        """Create system tray icon with menu."""
        try:
            image = Image.new('RGB', (64, 64), color=self.CONFIG["icon_color"])
            draw = ImageDraw.Draw(image)
            draw.ellipse((16, 16, 48, 48), fill=self.CONFIG["icon_ellipse_color"])

            menu = pystray.Menu(
                pystray.MenuItem("Restore", self.restore_window, default=True),
                pystray.MenuItem("Exit", self.exit_application)
            )

            self.tray_icon = pystray.Icon(
                name=self.CONFIG["app_name"],
                icon=image,
                title=self.CONFIG["app_name"],
                menu=menu
            )
        except Exception as e:
            print(f"Failed to create tray icon: {e}")
            self.restore_window()

    def show_notification(self, title: str, message: str, callback: callable = None):
        """Show a notification window without affecting main window visibility."""
        def _show():
            self.is_running = False
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None

            NotificationWindow(self.root, title, message, lambda: self.on_notification_closed(callback))

        self.root.after(0, _show)

    def on_notification_closed(self, callback: callable = None):
        """Handle notification window closure."""
        self.is_running = True
        if callback:
            callback()
        self.remaining_time = int(self.interval_var.get()) * 60
        self.schedule_update()

    def minimize_to_tray(self):
        """Minimize the window to the system tray."""
        if self.window_hidden:
            return

        try:
            self.root.withdraw()
            self.window_hidden = True
            if not self.tray_icon:
                self.create_tray_icon()
            threading.Thread(target=self.tray_icon.run, daemon=True, name="TrayIconThread").start()
        except Exception as e:
            print(f"Failed to minimize to tray: {e}")
            self.restore_window()

    def restore_window(self, icon=None, item=None):
        """Restore the main window from the system tray."""
        if not self.window_hidden:
            return

        def _restore():
            self.root.deiconify()
            self.window_hidden = False
            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception as e:
                    print(f"Error stopping tray icon: {e}")
                finally:
                    self.tray_icon = None

        self.root.after(0, _restore)

    def exit_application(self, icon=None, item=None):
        """Clean up resources and exit the application."""
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception as e:
                print(f"Error stopping tray icon: {e}")
            finally:
                self.tray_icon = None

        try:
            self.root.destroy()
        except Exception as e:
            print(f"Error destroying window: {e}")

        sys.exit(0)

    def validate_inputs(self) -> bool:
        """Validate user inputs for interval and time range."""
        try:
            interval = int(self.interval_var.get())
            if interval <= 0:
                raise ValueError("Interval must be positive")

            start = datetime.datetime.strptime(self.start_time_var.get(), "%H:%M")
            end = datetime.datetime.strptime(self.end_time_var.get(), "%H:%M")
            if end <= start:
                raise ValueError("End time must be after start time")

            return True
        except ValueError as e:
            self.show_notification("Invalid Input", str(e))
            return False

    def toggle_reminder(self):
        """Toggle the reminder on or off."""
        if self.is_running:
            self.stop_reminder()
        elif self.validate_inputs():
            self.start_reminder()

    def start_reminder(self):
        """Start the reminder system."""
        self.is_running = True
        self.start_button.config(text="Stop Reminder")
        self.set_input_state("disabled")
        self.remaining_time = int(self.interval_var.get()) * 60
        self.schedule_update()

    def stop_reminder(self):
        """Stop the reminder system."""
        self.is_running = False
        self.start_button.config(text="Start Reminder")
        self.set_input_state("normal")
        self.countdown_label.config(text="Time Remaining: 00:00")
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def set_input_state(self, state: str):
        """Enable or disable input fields."""
        for entry in (self.interval_entry, self.start_time_entry, self.end_time_entry):
            entry.config(state=state)

    def schedule_update(self):
        """Schedule the next countdown update."""
        if not self.is_running:
            return

        now = datetime.datetime.now().strftime("%H:%M")
        if self.start_time_var.get() <= now < self.end_time_var.get():
            self.update_countdown()
            self.after_id = self.root.after(1000, self.schedule_update)
        else:
            self.show_notification(self.CONFIG["app_name"], "Outside reminder time range!", self.stop_reminder)

    def update_countdown(self):
        """Update the countdown display."""
        if not self.is_running:
            return

        if self.remaining_time > 0:
            self.remaining_time -= 1
            minutes, seconds = divmod(self.remaining_time, 60)
            self.countdown_label.config(text=f"Time Remaining: {minutes:02d}:{seconds:02d}")
        else:
            self.show_notification(self.CONFIG["app_name"], "Time to drink water!")

    def update_auto_start_button(self):
        """Update the auto-start button and label."""
        is_enabled = RegistryManager.is_auto_start_enabled()
        self.auto_start_label.config(
            text="Application set to auto-start" if is_enabled else "Application not set to auto-start"
        )
        self.auto_start_button.config(
            text="Remove Auto-start" if is_enabled else "Set Auto-start",
            command=self.remove_auto_start if is_enabled else self.add_auto_start
        )

    def add_auto_start(self):
        """Enable auto-start."""
        if RegistryManager.set_auto_start(True):
            self.update_auto_start_button()

    def remove_auto_start(self):
        """Disable auto-start."""
        if RegistryManager.set_auto_start(False):
            self.update_auto_start_button()

def main():
    """Run the ReminderApp."""
    app = ReminderApp()
    app.root.mainloop()

if __name__ == "__main__":
    main()