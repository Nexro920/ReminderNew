# Copyright (c) 2025 Nexro920
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk
import winreg as reg
from PIL import Image, ImageDraw
import pystray
import threading
import json

class RegistryManager:
    """Handle Windows registry operations for auto-start functionality."""
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "ReminderApp"

    @staticmethod
    def get_exe_path() -> str:
        """Get the path of the executable or script."""
        return sys.executable if getattr(sys, 'frozen', False) else os.path.realpath(__file__)

    @staticmethod
    def get_exe_dir() -> str:
        """Get the directory of the executable or script."""
        exe_path = RegistryManager.get_exe_path()
        return os.path.dirname(exe_path)

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
        self.top.attributes('-topmost', True)

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
        self.top.focus_force()
        self.top.after(1, lambda: self.top.attributes('-topmost', False))

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
        "spacing": 5,
        "config_file": os.path.join(RegistryManager.get_exe_dir(), "settings.json"),#"settings.json",
        "default_language": "English"
    }

    # Translation dictionaries
    TRANSLATIONS = {
        "English": {
            "app_name": "Drink Water Reminder",
            "interval_label": "Reminder Interval (minutes):",
            "start_time_label": "Start Time (HH:MM):",
            "end_time_label": "End Time (HH:MM):",
            "countdown_label": "Time Remaining: 00:00",
            "countdown_label_prefix": "Time Remaining",
            "start_button": "Start Reminder",
            "stop_button": "Stop Reminder",
            "auto_start_label_on": "Application set to auto-start",
            "auto_start_label_off": "Application not set to auto-start",
            "set_auto_start": "Set Auto-start",
            "remove_auto_start": "Remove Auto-start",
            "settings_button": "Settings",
            "settings_title": "Settings",
            "language_label": "Language:",
            "save_button": "Save",
            "invalid_input": "Invalid Input",
            "interval_error": "Interval must be positive",
            "interval_invalid": "Interval must be a number",
            "interval_empty": "Interval cannot be empty",
            "time_error": "End time must be after start time",
            "time_invalid": "Time must be in HH:MM format",
            "outside_range": "Outside reminder time range!",
            "drink_water": "Time to drink water!",
            "restore_window": "Restore",
            "hide_window": "Hide",
            "exit_button": "Exit"
        },
        "中文": {
            "app_name": "喝水提醒",
            "interval_label": "提醒间隔（分钟）：",
            "start_time_label": "开始时间（HH:MM）：",
            "end_time_label": "结束时间（HH:MM）：",
            "countdown_label": "剩余时间：00:00",
            "countdown_label_prefix": "剩余时间",
            "start_button": "开始提醒",
            "stop_button": "停止提醒",
            "auto_start_label_on": "应用已设为开机启动",
            "auto_start_label_off": "应用未设为开机启动",
            "set_auto_start": "设置开机启动",
            "remove_auto_start": "移除开机启动",
            "settings_button": "设置",
            "settings_title": "设置",
            "language_label": "语言：",
            "save_button": "保存",
            "invalid_input": "输入无效",
            "interval_error": "间隔时间必须为正数",
            "interval_invalid": "间隔时间必须为数字",
            "interval_empty": "间隔时间不能为空",
            "time_error": "结束时间必须晚于开始时间",
            "time_invalid": "时间必须为HH:MM格式",
            "outside_range": "不在提醒时间范围内！",
            "drink_water": "该喝水了！",
            "restore_window": "恢复",
            "hide_window": "隐藏",
            "exit_button": "退出"
        }
    }

    def __init__(self):
        self.is_running = False
        self.remaining_time = 0
        self.window_hidden = False
        self.after_id = None
        self.tray_icon = None
        self.language = self.load_setting("language", self.CONFIG["default_language"])
        self.interval = self.load_setting("interval", self.CONFIG["interval"])
        self.start_time = self.load_setting("start_time", self.CONFIG["start_time"])
        self.end_time = self.load_setting("end_time", self.CONFIG["end_time"])
        self.root = tk.Tk()
        # Create StringVar objects after root window
        self.interval_var = tk.StringVar(value=self.interval)
        self.start_time_var = tk.StringVar(value=self.start_time)
        self.end_time_var = tk.StringVar(value=self.end_time)
        self._initialize_ui()
        self.update_auto_start_button()

    def load_setting(self, setting: str, default: str) -> str:
        """Load a specific setting from config file or return default."""
        try:
            with open(self.CONFIG["config_file"], "r") as f:
                settings = json.load(f)
            value = settings.get(setting)
            if value is None:
                value = default
                self.save_settings({
                    "language": settings.get("language", self.CONFIG["default_language"]),
                    "interval": settings.get("interval", self.CONFIG["interval"]),
                    "start_time": settings.get("start_time", self.CONFIG["start_time"]),
                    "end_time": settings.get("end_time", self.CONFIG["end_time"])
                })
            return value
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_settings({
                "language": self.CONFIG["default_language"],
                "interval": self.CONFIG["interval"],
                "start_time": self.CONFIG["start_time"],
                "end_time": self.CONFIG["end_time"]
            })
            return default

    def save_settings(self, settings: dict):
        """Save all settings to config file."""
        try:
            with open(self.CONFIG["config_file"], "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_text(self, key: str) -> str:
        """Get translated text for the current language."""
        return self.TRANSLATIONS.get(self.language, self.TRANSLATIONS["English"]).get(key, key)

    def _initialize_ui(self):
        """Set up the main window and widgets."""
        self.root.title(self.get_text("app_name"))
        self.root.resizable(False, False)

        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.CONFIG["window_width"]) // 2
        y = (screen_height - self.CONFIG["window_height"]) // 2
        self.root.geometry(f"{self.CONFIG['window_width']}x{self.CONFIG['window_height']}+{x}+{y}")

        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.create_widgets()
        self.create_tray_icon()
        if self.tray_icon:
            threading.Thread(target=self.tray_icon.run, daemon=True, name="TrayIconThread").start()

    def create_widgets(self):
        """Create and arrange UI widgets."""
        frame = ttk.Frame(self.root, padding=self.CONFIG["padding"])
        frame.pack(fill=tk.BOTH, expand=True)

        # Interval input
        self.interval_label = ttk.Label(frame, text=self.get_text("interval_label"))
        self.interval_label.pack(pady=self.CONFIG["spacing"])
        self.interval_var = tk.StringVar(value=self.interval_var.get())
        self.interval_entry = ttk.Entry(frame, textvariable=self.interval_var, width=self.CONFIG["entry_width"])
        self.interval_entry.pack()

        # Start time input
        self.start_time_label = ttk.Label(frame, text=self.get_text("start_time_label"))
        self.start_time_label.pack(pady=self.CONFIG["spacing"])
        self.start_time_var = tk.StringVar(value=self.start_time_var.get())
        self.start_time_entry = ttk.Entry(frame, textvariable=self.start_time_var, width=self.CONFIG["entry_width"])
        self.start_time_entry.pack()

        # End time input
        self.end_time_label = ttk.Label(frame, text=self.get_text("end_time_label"))
        self.end_time_label.pack(pady=self.CONFIG["spacing"])
        self.end_time_var = tk.StringVar(value=self.end_time_var.get())
        self.end_time_entry = ttk.Entry(frame, textvariable=self.end_time_var, width=self.CONFIG["entry_width"])
        self.end_time_entry.pack()

        # Countdown display
        self.countdown_label = ttk.Label(frame, text=self.get_text("countdown_label"))
        self.countdown_label.pack(pady=self.CONFIG["spacing"] * 2)

        # Start/Stop button
        self.start_button = ttk.Button(frame, text=self.get_text("start_button"), command=self.toggle_reminder)
        self.start_button.pack(pady=self.CONFIG["spacing"])

        # Auto-start status
        self.auto_start_label = ttk.Label(frame, text="")
        self.auto_start_label.pack(pady=self.CONFIG["spacing"])
        self.auto_start_button = ttk.Button(frame, text=self.get_text("set_auto_start"), command=self.add_auto_start)
        self.auto_start_button.pack()

    def open_settings(self):
        """Open the settings window for language selection."""
        self.restore_window()

        settings_window = tk.Toplevel(self.root)
        settings_window.title(self.get_text("settings_title"))
        settings_window.resizable(False, False)
        settings_window.transient(self.root)

        frame = ttk.Frame(settings_window, padding=self.CONFIG["padding"])
        frame.pack(fill=tk.BOTH, expand=True)

        # Interval input
        ttk.Label(frame, text=self.get_text("interval_label")).pack(pady=self.CONFIG["spacing"])
        interval_var = tk.StringVar(value=self.interval_var.get())
        interval_entry = ttk.Entry(frame, textvariable=interval_var, width=self.CONFIG["entry_width"])
        interval_entry.pack(pady=self.CONFIG["spacing"])

        # Start time input
        ttk.Label(frame, text=self.get_text("start_time_label")).pack(pady=self.CONFIG["spacing"])
        start_time_var = tk.StringVar(value=self.start_time_var.get())
        start_time_entry = ttk.Entry(frame, textvariable=start_time_var, width=self.CONFIG["entry_width"])
        start_time_entry.pack(pady=self.CONFIG["spacing"])

        # End time input
        ttk.Label(frame, text=self.get_text("end_time_label")).pack(pady=self.CONFIG["spacing"])
        end_time_var = tk.StringVar(value=self.end_time_var.get())
        end_time_entry = ttk.Entry(frame, textvariable=end_time_var, width=self.CONFIG["entry_width"])
        end_time_entry.pack(pady=self.CONFIG["spacing"])

        # Language input
        ttk.Label(frame, text=self.get_text("language_label")).pack(pady=self.CONFIG["spacing"])
        language_var = tk.StringVar(value=self.language)
        language_menu = ttk.OptionMenu(frame, language_var, self.language, *self.TRANSLATIONS.keys())
        language_menu.pack(pady=self.CONFIG["spacing"])

        def save_and_close():
            if not self.validate_settings(interval_var, start_time_var, end_time_var):
                self.show_notification("invalid_input", self.get_text("invalid_input"))
                return
            # Update variables
            self.interval_var.set(interval_var.get())
            self.start_time_var.set(start_time_var.get())
            self.end_time_var.set(end_time_var.get())
            self.language = language_var.get()

            # Save all settings
            self.save_settings({
                "language": self.language,
                "interval": self.interval_var.get(),
                "start_time": self.start_time_var.get(),
                "end_time": self.end_time_var.get()
            })

            self.update_ui_text()
            settings_window.destroy()

        ttk.Button(frame, text=self.get_text("save_button"), command=save_and_close).pack(pady=self.CONFIG["spacing"])

        # Center window
        settings_window.update_idletasks()
        width = max(200, settings_window.winfo_reqwidth())
        height = settings_window.winfo_reqheight()
        x = (settings_window.winfo_screenwidth() - width) // 2
        y = (settings_window.winfo_screenheight() - height) // 2
        settings_window.geometry(f"{width}x{height}+{x}+{y}")

    def update_ui_text(self):
        """Update all UI text based on current language."""
        self.root.title(self.get_text("app_name"))
        for widget, key in [
            (self.interval_label, "interval_label"),
            (self.start_time_label, "start_time_label"),
            (self.end_time_label, "end_time_label"),
            (self.countdown_label, "countdown_label"),
            (self.start_button, "start_button" if not self.is_running else "stop_button"),
            (self.auto_start_button, "set_auto_start" if not RegistryManager.is_auto_start_enabled() else "remove_auto_start"),
            (self.auto_start_label, "auto_start_label_on" if RegistryManager.is_auto_start_enabled() else "auto_start_label_off")
        ]:
            widget.config(text=self.get_text(key))
        # Refresh tray icon if it exists
        if self.tray_icon:
            try:
                self.tray_icon.title = self.get_text("app_name")
                self.tray_icon.menu = self.is_show_window()
            except Exception as e:
                print(f"Failed to update tray icon: {e}")
                self.tray_icon.stop()
                self.tray_icon = None
                self.create_tray_icon()
                threading.Thread(target=self.tray_icon.run, daemon=True, name="TrayIconThread").start()

    def is_show_window(self):
        """Return menu with window_hidden ."""
        if self.window_hidden:
            return pystray.Menu(
                pystray.MenuItem(self.get_text("settings_button"), self.open_settings),
                pystray.MenuItem(self.get_text("restore_window"), self.toggle_window, default=True),
                pystray.MenuItem(self.get_text("exit_button"), self.exit_application)
            )
        else:
            return pystray.Menu(
                pystray.MenuItem(self.get_text("settings_button"), self.open_settings),
                pystray.MenuItem(self.get_text("hide_window"), self.toggle_window, default=True),
                pystray.MenuItem(self.get_text("exit_button"), self.exit_application)
            )

    def create_tray_icon(self):
        """Create system tray icon with menu."""
        try:
            image = Image.new('RGB', (64, 64), color=self.CONFIG["icon_color"])
            draw = ImageDraw.Draw(image)
            draw.ellipse((16, 16, 48, 48), fill=self.CONFIG["icon_ellipse_color"])

            menu = self.is_show_window()
            self.tray_icon = pystray.Icon(
                name=self.CONFIG["app_name"],
                icon=image,
                title=self.get_text("app_name"),
                menu=menu
            )
        except Exception as e:
            print(f"Failed to create tray icon: {e}")
            self.window_hidden = False
            self.root.deiconify()

    def show_notification(self, title: str, message: str, callback: callable = None):
        """Show a notification window without affecting main window visibility."""
        def _show():
            NotificationWindow(self.root, self.get_text(title), self.get_text(message), callback)

        self.root.after(0, _show)

    def on_notification_closed(self):
        """Handle notification window closure and restart countdown."""
        self.is_running = True
        self.remaining_time = int(self.interval_var.get()) * 60
        if not self.validate_inputs():
            self.stop_reminder()
            return
        self.schedule_update()

    def minimize_to_tray(self):
        """Minimize the window to the system tray."""
        if not self.window_hidden:
            self.root.withdraw()
            self.window_hidden = True
            self.tray_icon.menu = self.is_show_window()

    def toggle_window(self):
        """Toggle the window show or hide."""
        if self.window_hidden:
            self.restore_window()
        else:
            self.minimize_to_tray()

    def restore_window(self, icon=None, item=None):
        """Restore the main window."""
        if self.window_hidden:
            self.root.deiconify()
            self.window_hidden = False
            self.tray_icon.menu = self.is_show_window()

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

    def validate_inputs(self, interval_var=None, start_time_var=None, end_time_var=None, show_notification=True) -> bool:
        """
        Validate user inputs for interval and time range.

        Args:
            interval_var: StringVar for interval (defaults to self.interval_var).
            start_time_var: StringVar for start time (defaults to self.start_time_var).
            end_time_var: StringVar for end time (defaults to self.end_time_var).
            show_notification: Whether to show notification for errors (default: True).

        Returns:
            bool: True if inputs are valid, False otherwise.
        """
        # Use provided variables or default to instance variables
        interval_var = interval_var or self.interval_var
        start_time_var = start_time_var or self.start_time_var
        end_time_var = end_time_var or self.end_time_var

        try:
            # Validate interval
            interval_str = interval_var.get().strip()
            if not interval_str:
                raise ValueError("interval_empty", "Interval cannot be empty")
            try:
                interval = int(interval_str)
            except ValueError:
                raise ValueError("interval_invalid", "Interval must be a valid number")
            if interval <= 0:
                raise ValueError("interval_error", "Interval must be a positive number")

            # Validate time format and range
            start_str = start_time_var.get().strip()
            end_str = end_time_var.get().strip()
            try:
                start = datetime.datetime.strptime(start_str, "%H:%M")
                end = datetime.datetime.strptime(end_str, "%H:%M")
                # Validate hour and minute ranges
                if not (0 <= start.hour <= 23 and 0 <= start.minute <= 59):
                    raise ValueError("time_invalid", "Start time has invalid hours or minutes")
                if not (0 <= end.hour <= 23 and 0 <= end.minute <= 59):
                    raise ValueError("time_invalid", "End time has invalid hours or minutes")
            except ValueError:
                raise ValueError("time_invalid", "Times must be in HH:MM format")
            if end <= start:
                raise ValueError("time_error", "End time must be after start time")

            # Check if current time is within range
            now = datetime.datetime.now()
            start_time = datetime.datetime.combine(now.date(), start.time())
            end_time = datetime.datetime.combine(now.date(), end.time())
            if not (start_time <= now < end_time):
                raise ValueError("outside_range", "Current time is outside the reminder range")

            return True
        except ValueError as e:
            if show_notification:
                error_key = e.args[0] if e.args else "invalid_input"
                self.show_notification("invalid_input", error_key)
            # if show_notification and len(e.args) > 1:
            #     self.show_notification("invalid_input", e.args[1])
            return False

    def validate_settings(self, interval_var, start_time_var, end_time_var):
        """
        Validate settings inputs from the settings window without showing notifications.

        Args:
            interval_var: StringVar for interval.
            start_time_var: StringVar for start time.
            end_time_var: StringVar for end time.

        Returns:
            bool: True if inputs are valid, False otherwise.
        """
        return self.validate_inputs(interval_var, start_time_var, end_time_var, show_notification=False)

    def toggle_reminder(self):
        """Toggle the reminder on or off."""
        if self.is_running:
            self.stop_reminder()
        else:
            self.start_reminder()

    def start_reminder(self):
        """Start the reminder system."""
        if not self.validate_inputs():
            return

        self.is_running = True
        self.start_button.config(text=self.get_text("stop_button"))
        self.set_input_state("disabled")
        self.remaining_time = int(self.interval_var.get()) * 60
        self.schedule_update()

    def stop_reminder(self):
        """Stop the reminder system."""
        self.is_running = False
        self.start_button.config(text=self.get_text("start_button"))
        self.set_input_state("normal")
        self.countdown_label.config(text=self.get_text("countdown_label"))
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

        self.update_countdown()
        self.after_id = self.root.after(1000, self.schedule_update)

    def update_countdown(self):
        """Update the countdown display."""
        if not self.is_running:
            return

        if self.remaining_time > 0:
            self.remaining_time -= 1
            minutes, seconds = divmod(self.remaining_time, 60)
            self.countdown_label.config(text=f"{self.get_text('countdown_label_prefix')}: {minutes:02d}:{seconds:02d}")
        else:
            self.is_running = False
            self.show_notification("app_name", "drink_water", self.on_notification_closed)

    def update_auto_start_button(self):
        """Update the auto-start button and label."""
        is_enabled = RegistryManager.is_auto_start_enabled()
        self.auto_start_label.config(
            text=self.get_text("auto_start_label_on") if is_enabled else self.get_text("auto_start_label_off")
        )
        self.auto_start_button.config(
            text=self.get_text("remove_auto_start") if is_enabled else self.get_text("set_auto_start"),
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