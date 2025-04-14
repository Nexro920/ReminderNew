import os
import sys
import time
import datetime
import tkinter as tk
from tkinter import messagebox
import winreg as reg
# from pystray import Icon, MenuItem, Menu
#from PIL import Image, ImageDraw

# 获取当前运行的脚本路径
def get_exe_path():
    if getattr(sys, 'frozen', False):  # 如果是打包后的exe文件
        return sys.executable
    else:  # 如果是通过python源代码运行
        return os.path.realpath(__file__)

# 设定Windows自启动
def set_auto_start(enabled):
    script_path = get_exe_path()  # 获取当前的exe文件路径
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_SET_VALUE)
        if enabled:
            reg.SetValueEx(key, "ReminderApp", 0, reg.REG_SZ, script_path)
        else:
            reg.DeleteValue(key, "ReminderApp")
        reg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error setting startup: {e}")
        return False


# 检查是否已经设置为自启动
def is_auto_start_enabled():
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_READ)
        try:
            reg.QueryValueEx(key, "ReminderApp")
            reg.CloseKey(key)
            return True
        except FileNotFoundError:
            reg.CloseKey(key)
            return False
    except Exception as e:
        print(f"Error checking startup status: {e}")
        return False

# 提醒应用
class ReminderApp:
    def __init__(self):
        self.is_running = False
        self.remaining_time = 0
        self.root = tk.Tk()
        self.create_interface()

    # 创建界面
    def create_interface(self):
        self.root.title("提醒设置")

        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        position_top = int(screen_height / 2 - window_height / 2)
        position_left = int(screen_width / 2 - window_width / 2)

        self.root.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")

        # 提醒间隔（分钟）
        interval_label = tk.Label(self.root, text="提醒间隔（分钟）:")
        interval_label.pack()
        self.interval_var = tk.StringVar(value="10")
        self.interval_entry = tk.Entry(self.root, textvariable=self.interval_var)
        self.interval_entry.pack()

        # 起始时间
        start_time_label = tk.Label(self.root, text="提醒起始时间（HH:MM）:")
        start_time_label.pack()
        self.start_time_var = tk.StringVar(value="09:00")
        self.start_time_entry = tk.Entry(self.root, textvariable=self.start_time_var)
        self.start_time_entry.pack()

        # 结束时间
        end_time_label = tk.Label(self.root, text="提醒结束时间（HH:MM）:")
        end_time_label.pack()
        self.end_time_var = tk.StringVar(value="17:30")
        self.end_time_entry = tk.Entry(self.root, textvariable=self.end_time_var)
        self.end_time_entry.pack()

        # 倒计时标签
        self.countdown_label = tk.Label(self.root, text="剩余时间: 00:00 分钟")
        self.countdown_label.pack()

        # 开始/停止按钮
        self.start_button = tk.Button(self.root, text="开始提醒", command=self.toggle_reminder)
        self.start_button.pack()

        # 设置程序自启动
        self.auto_start_label = tk.Label(self.root, text="")
        self.auto_start_label.pack()
        self.update_auto_start_button()

    def update_auto_start_button(self):
        def rmbtn():
            if hasattr(self, 'auto_start_button'):
                self.auto_start_button.pack_forget()  # 移除旧按钮
        # 检查是否已设置为自启动
        if is_auto_start_enabled():
            self.auto_start_label.config(text="已设置为自启动，若要取消自启动，请点击取消按钮")
            rmbtn()
            self.auto_start_button = tk.Button(self.root, text="取消自启动", command=self.remove_auto_start)
        else:
            self.auto_start_label.config(text="尚未设置为自启动")
            rmbtn()
            self.auto_start_button = tk.Button(self.root, text="设置为自启动", command=self.add_auto_start)

        self.auto_start_button.pack()

    # 开始/停止按钮功能
    def toggle_reminder(self):
        if self.is_running:
            self.stop_reminder()
        else:
            self.start_reminder()

    def start_reminder(self):
        self.is_running = True
        self.start_button.config(text="停止")
        self.enable_input_fields(False)
        self.remaining_time = int(self.interval_var.get()) * 60
        self.remind_user()

    def stop_reminder(self):
        self.is_running = False
        self.start_button.config(text="开始提醒")
        self.enable_input_fields(True)

    # 启用或禁用输入框
    def enable_input_fields(self, state):
        if state:
            self.interval_entry.config(state="normal")
            self.start_time_entry.config(state="normal")
            self.end_time_entry.config(state="normal")
        else:
            self.interval_entry.config(state="disabled")
            self.start_time_entry.config(state="disabled")
            self.end_time_entry.config(state="disabled")

    # 提醒函数
    def remind_user(self):
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        current_time = now.strftime("%H:%M")

        # 获取用户设置的起始时间和结束时间，并且去掉秒和微秒部分
        start_time = datetime.datetime.strptime(self.start_time_var.get(), "%H:%M").replace(second=0, microsecond=0).strftime("%H:%M")
        end_time = datetime.datetime.strptime(self.end_time_var.get(), "%H:%M").replace(second=0, microsecond=0).strftime("%H:%M")

        # 判断当前时间是否在起始和结束时间之间
        if start_time <= current_time < end_time:
            self.update_countdown()
            if self.is_running:
                self.root.after(int(self.interval_var.get()) * 60 * 1000, self.remind_user)
        else:
            messagebox.showinfo("提醒", "当前时间为非提醒时间范围！")
            self.stop_reminder()

    # 更新倒计时显

    # 更新倒计时显示
    def update_countdown(self):
        if self.is_running:
            if self.remaining_time > 0:
                self.remaining_time -= 1  # 每秒递减
                minutes = self.remaining_time // 60
                seconds = self.remaining_time % 60
                self.countdown_label.config(text=f"剩余时间: {minutes:02}:{seconds:02} 分钟")
                self.root.after(1000, self.update_countdown)
            else:
                self.is_running = False
                messagebox.showinfo("提醒", "该喝水啦！")
                self.reset_timer()

    # 重置倒计时
    def reset_timer(self):
        self.remaining_time = int(self.interval_var.get()) * 60
        self.is_running = True
        self.update_countdown()

    # 设置为自启动
    def add_auto_start(self):
        if set_auto_start(True):
            self.update_auto_start_button()

    # 取消自启动
    def remove_auto_start(self):
        if set_auto_start(False):
            self.update_auto_start_button()

if __name__ == "__main__":
    app = ReminderApp()
    app.root.mainloop()
