import os
import sys
import time
import subprocess
import threading
import schedule
import json
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

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
    required_packages = ["python-telegram-bot", "schedule"]
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

# Main function
def main():
    global bot

    # Load configuration
    config = load_config()

    # Check and install required packages
    check_packages()

    # Initialize Telegram bot
    updater = Updater(config["bot_token"], use_context=True)
    bot = updater.bot
    dispatcher = updater.dispatcher

    # Set up command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("ping", ping))
    dispatcher.add_handler(CommandHandler("setip", set_ip))
    dispatcher.add_handler(CommandHandler("setport", set_port))
    dispatcher.add_handler(CommandHandler("setinterval", set_interval))
    dispatcher.add_handler(CommandHandler("setsuccessinterval", set_success_interval))

    # Start the bot
    updater.start_polling()

    # Schedule pinging remote server
    schedule.every(config["check_interval"]).minutes.do(ping_remote_server, config=config)

    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)

# Command handlers
def start(update: Update, context: CallbackContext):
    pass

def stop(update: Update, context: CallbackContext):
    pass

def status(update: Update, context: CallbackContext):
    pass

def ping(update: Update, context: CallbackContext):
    pass

def set_ip(update: Update, context: CallbackContext):
    pass

def set_port(update: Update, context: CallbackContext):
    pass

def set_interval(update: Update, context: CallbackContext):
    pass

def set_success_interval(update: Update, context: CallbackContext):
    pass

if __name__ == "__main__":
    main()

# Command handlers
def start(update: Update, context: CallbackContext):
    """Start the uptime monitor"""
    config = load_config()
    if not config["remote_ip"]:
        update.message.reply_text("Please set the remote IP address first using /setip")
        return

    schedule.every(config["check_interval"]).minutes.do(ping_remote_server, config=config)
    send_notification(bot, config["admin_id"], "Uptime monitor started")
    log("Uptime monitor started")
    update.message.reply_text("Uptime monitor started")

def stop(update: Update, context: CallbackContext):
    """Stop the uptime monitor"""
    schedule.clear()
    send_notification(bot, load_config()["admin_id"], "Uptime monitor stopped")
    log("Uptime monitor stopped")
    update.message.reply_text("Uptime monitor stopped")

def status(update: Update, context: CallbackContext):
    """Get the current status of the uptime monitor"""
    config = load_config()
    if schedule.get_jobs():
        update.message.reply_text(f"Uptime monitor is running\n"
                                  f"Remote IP: {config['remote_ip']}\n"
                                  f"Remote Port: {config['remote_port']}\n"
                                  f"Check Interval: {config['check_interval']} minutes\n"
                                  f"Success Notification Interval: {config['success_notification_interval']} minutes")
    else:
        update.message.reply_text("Uptime monitor is not running")

def ping(update: Update, context: CallbackContext):
    """Manually ping the remote server"""
    config = load_config()
    ping_remote_server(config)
    update.message.reply_text(f"Manually pinged {config['remote_ip']}:{config['remote_port']}")

def set_ip(update: Update, context: CallbackContext):
    """Set the remote IP address"""
    if len(context.args) != 1:
        update.message.reply_text("Usage: /setip <ip_address>")
        return

    ip = context.args[0]
    config = load_config()
    config["remote_ip"] = ip
    save_config(config)
    send_notification(bot, config["admin_id"], f"Remote IP address set to {ip}")
    log(f"Remote IP address set to {ip}")
    update.message.reply_text(f"Remote IP address set to {ip}")

def set_port(update: Update, context: CallbackContext):
    """Set the remote port"""
    if len(context.args) != 1:
        update.message.reply_text("Usage: /setport <port_number>")
        return

    try:
        port = int(context.args[0])
    except ValueError:
        update.message.reply_text("Invalid port number")
        return

    config = load_config()
    config["remote_port"] = port
    save_config(config)
    send_notification(bot, config["admin_id"], f"Remote port set to {port}")
    log(f"Remote port set to {port}")
    update.message.reply_text(f"Remote port set to {port}")

def set_interval(update: Update, context: CallbackContext):
    """Set the check interval"""
    if len(context.args) != 1:
        update.message.reply_text("Usage: /setinterval <minutes>")
        return

    try:
        interval = int(context.args[0])
    except ValueError:
        update.message.reply_text("Invalid interval")
        return

    config = load_config()
    config["check_interval"] = interval
    save_config(config)
    schedule.clear()
    schedule.every(interval).minutes.do(ping_remote_server, config=config)
    send_notification(bot, config["admin_id"], f"Check interval set to {interval} minutes")
    log(f"Check interval set to {interval} minutes")
    update.message.reply_text(f"Check interval set to {interval} minutes")

def set_success_interval(update: Update, context: CallbackContext):
    """Set the success notification interval"""
    if len(context.args) != 1:
        update.message.reply_text("Usage: /setsuccessinterval <minutes>")
        return

    try:
        interval = int(context.args[0])
    except ValueError:
        update.message.reply_text("Invalid interval")
        return

    config = load_config()
    config["success_notification_interval"] = interval
    save_config(config)
    send_notification(bot, config["admin_id"], f"Success notification interval set to {interval} minutes")
    log(f"Success notification interval set to {interval} minutes")
    update.message.reply_text(f"Success notification interval set to {interval} minutes")
