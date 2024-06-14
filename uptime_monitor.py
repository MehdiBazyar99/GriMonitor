import os
import sys
import subprocess
import json
import schedule
import time
from datetime import datetime
from telegram import Bot
import npyscreen

# Global variables
CONFIG_FILE = "config.json"
LOG_FILE = "uptime_monitor.log"

# Load configuration from file
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "remote_ip": "",
            "remote_port": 80,
            "check_interval": 5,
            "bot_token": "",
            "admin_id": "",
            "success_notification_interval": 60
        }

# Save configuration to file
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Check if required packages are installed
def check_packages():
    required_packages = ["python-telegram-bot", "schedule", "npyscreen"]
    installed_packages = subprocess.check_output(["pip", "freeze"]).decode().split("\n")
    missing_packages = [p for p in required_packages if p not in installed_packages]
    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])

# Send notification to Telegram bot
def send_notification(bot, chat_id, message):
    try:
        bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        log(f"Error sending Telegram notification: {e}")

# Log messages to file
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# Ping remote server
def ping_remote_server(config):
    ip, port = config["remote_ip"], config["remote_port"]
    try:
        subprocess.check_call(["telnet", ip, str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        log(f"Successfully pinged {ip}:{port}")
        if config["success_notification_interval"] > 0:
            send_notification(bot, config["admin_id"], f"Successfully pinged {ip}:{port}")
    except subprocess.CalledProcessError:
        log(f"Failed to ping {ip}:{port}")
        send_notification(bot, config["admin_id"], f"Failed to ping {ip}:{port}")

# Main application class
class GrimonitorApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.config = load_config()
        check_packages()
        self.bot = Bot(token=self.config["bot_token"])
        self.addForm("MAIN", MainForm, name="Uptime Monitor")

# Main menu form
class MainForm(npyscreen.FormBaseNew):
    def create(self):
        self.add_handlers({
            "^Q": self.exit_func,
            "^S": self.save_config,
            "^I": self.install_packages,
            "^P": self.ping_server,
            "^C": self.change_settings
        })

        self.config = load_config()

        self.add(npyscreen.TitleText, name="Uptime Monitor", editable=False)
        self.add(npyscreen.FixedText, value="Press 'c' to change settings", editable=False)
        self.add(npyscreen.FixedText, value="Press 'p' to ping the server", editable=False)
        self.add(npyscreen.FixedText, value="Press 'i' to install packages", editable=False)
        self.add(npyscreen.FixedText, value="Press 's' to save configuration", editable=False)
        self.add(npyscreen.FixedText, value="Press 'q' to quit", editable=False)

    def exit_func(self, _):
        self.parentApp.setNextForm(None)
        self.editing = False

    def save_config(self, _):
        save_config(self.config)
        npyscreen.notify_confirm("Configuration saved", title="Success")

    def install_packages(self, _):
        check_packages()
        npyscreen.notify_confirm("Packages installed", title="Success")

    def ping_server(self, _):
        ping_remote_server(self.config)
        npyscreen.notify_confirm("Pinged server", title="Success")

    def change_settings(self, _):
        self.parentApp.addForm("SETTINGS", SettingsForm, name="Settings")
        self.parentApp.switchForm("SETTINGS")

# Settings form
class SettingsForm(npyscreen.ActionForm):
    def create(self):
        self.add_handlers({
            "^Q": self.exit_func,
            "^S": self.save_settings
        })

        self.config = load_config()

        self.add(npyscreen.TitleText, name="Settings", editable=False)
        self.ip_entry = self.add(npyscreen.TitleText, name="Remote IP:", value=self.config["remote_ip"], editable=True)
        self.port_entry = self.add(npyscreen.TitleText, name="Remote Port:", value=str(self.config["remote_port"]), editable=True)
        self.interval_entry = self.add(npyscreen.TitleText, name="Check Interval (minutes):", value=str(self.config["check_interval"]), editable=True)
        self.success_interval_entry = self.add(npyscreen.TitleText, name="Success Notification Interval (minutes):", value=str(self.config["success_notification_interval"]), editable=True)
        self.add(npyscreen.FixedText, value="Press 's' to save settings", editable=False)
        self.add(npyscreen.FixedText, value="Press 'q' to go back", editable=False)

    def exit_func(self, _):
        self.parentApp.switchFormPrevious()

    def save_settings(self, _):
        self.config["remote_ip"] = self.ip_entry.value
        self.config["remote_port"] = int(self.port_entry.value)
        self.config["check_interval"] = int(self.interval_entry.value)
        self.config["success_notification_interval"] = int(self.success_interval_entry.value)
        save_config(self.config)
        npyscreen.notify_confirm("Settings saved", title="Success")
        self.parentApp.switchFormPrevious()

def main():
    app = GrimonitorApp()
    app.run()

if __name__ == "__main__":
    main()
