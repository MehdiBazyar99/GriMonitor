import os
import sys
import telnetlib
import requests
import schedule
import time
import subprocess
from getpass import getpass
from threading import Thread
from telegram.ext import Updater, CommandHandler

# ANSI escape codes for colors
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

CONFIG_FILE = "config.txt"

def install_packages():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "schedule", "python-telegram-bot"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def create_config_file(config):
    try:
        with open(CONFIG_FILE, "w") as config_file:
            config_file.write(f"{config['ip']}\n{config['port']}\n{config['interval']}\n{config['bot_token']}\n{config['chat_id']}\n{config['success_interval']}")
        print(f"{GREEN}Configuration file created successfully.{RESET}")
    except Exception as e:
        print(f"{RED}Error creating configuration file: {e}{RESET}")

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        try:
            config = read_config()
            print(f"{GREEN}Configuration loaded from {CONFIG_FILE}.{RESET}")
        except Exception as e:
            print(f"{RED}Error loading configuration: {e}{RESET}")
            config = get_user_config()
            create_config_file(config)
    else:
        print(f"{RED}Configuration file not found. Creating a new one.{RESET}")
        config = get_user_config()
        create_config_file(config)

    return config

def read_config():
    try:
        with open(CONFIG_FILE, "r") as config_file:
            lines = config_file.readlines()
            return {
                "ip": lines[0].strip(),
                "port": int(lines[1].strip()),
                "interval": int(lines[2].strip()),
                "bot_token": lines[3].strip(),
                "chat_id": lines[4].strip(),
                "success_interval": int(lines[5].strip())
            }
    except Exception as e:
        raise RuntimeError(f"Error reading configuration file: {e}")

def get_user_config():
    try:
        print(f"{BLUE}Current working directory: {os.getcwd()}{RESET}")
        ip = input(f"{GREEN}Enter the IP address to monitor:{RESET} ")
        port = int(input(f"{GREEN}Enter the port to monitor:{RESET} "))
        interval = int(input(f"{GREEN}Enter the interval in minutes:{RESET} "))
        bot_token = getpass(f"{GREEN}Enter the Telegram bot token:{RESET} ")
        chat_id = input(f"{GREEN}Enter the Telegram chat ID:{RESET} ")
        success_interval = int(input(f"{GREEN}Enter the interval in minutes for success notifications:{RESET} "))

        return {
            "ip": ip,
            "port": port,
            "interval": interval,
            "bot_token": bot_token,
            "chat_id": chat_id,
            "success_interval": success_interval
        }
    except ValueError as ve:
        print(f"{RED}Invalid input: {ve}{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        sys.exit(1)

def send_telegram_message(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error sending Telegram message: {e}{RESET}")

def check_connection(ip, port, bot_token, chat_id, success_interval):
    try:
        with telnetlib.Telnet(ip, port, timeout=10) as tn:
            send_telegram_message(bot_token, chat_id, f"{GREEN}Connection to {ip}:{port} successful.{RESET}")
            schedule.every(success_interval).minutes.do(send_telegram_message, bot_token, chat_id, f"{GREEN}Connection to {ip}:{port} successful.{RESET}")
    except Exception as e:
        send_telegram_message(bot_token, chat_id, f"{RED}Connection to {ip}:{port} failed: {str(e)}{RESET}")

def monitor(config):
    schedule.every(config["interval"]).minutes.do(
        check_connection, config["ip"], config["port"], config["bot_token"], config["chat_id"], config["success_interval"]
    )
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_monitoring(config):
    monitoring_thread = Thread(target=monitor, args=(config,))
    monitoring_thread.start()
    print(f"{GREEN}Monitoring started in the background.{RESET}")

def stop_monitoring():
    schedule.clear()
    print(f"{RED}Monitoring stopped.{RESET}")

def handle_telegram_command(update, context):
    message = update.message.text
    config = load_or_create_config()

    if message.startswith("/start"):
        start_monitoring(config)
        send_telegram_message(config["bot_token"], config["chat_id"], f"{GREEN}Monitoring started.{RESET}")
    elif message.startswith("/stop"):
        stop_monitoring()
        send_telegram_message(config["bot_token"], config["chat_id"], f"{RED}Monitoring stopped.{RESET}")
    elif message.startswith("/ping"):
        try:
            port = int(message.split()[1])
        except (IndexError, ValueError):
            send_telegram_message(config["bot_token"], config["chat_id"], f"{RED}Invalid command format. Usage: /ping <port>{RESET}")
            return
        try:
            with telnetlib.Telnet(config["ip"], port, timeout=10) as tn:
                send_telegram_message(config["bot_token"], config["chat_id"], f"{GREEN}Connection to {config['ip']}:{port} successful.{RESET}")
        except Exception as e:
            send_telegram_message(config["bot_token"], config["chat_id"], f"{RED}Connection to {config['ip']}:{port} failed: {str(e)}{RESET}")
    else:
        send_telegram_message(config["bot_token"], config["chat_id"], f"{RED}Invalid command. Available commands: /start, /stop, /ping <port>{RESET}")

def print_menu():
    print(f"{BLUE}GriMonitor Uptime Monitor{RESET}")
    print(f"{YELLOW}1. Start Monitoring{RESET}")
    print(f"{YELLOW}2. Stop Monitoring{RESET}")
    print(f"{YELLOW}3. Change Configuration{RESET}")
    print(f"{YELLOW}4. Exit{RESET}")

def main():
    install_packages()
    config = load_or_create_config()

    updater = Updater(token=config["bot_token"], use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", handle_telegram_command))
    dispatcher.add_handler(CommandHandler("stop", handle_telegram_command))
    dispatcher.add_handler(CommandHandler("ping", handle_telegram_command))
    updater.start_polling()

    while True:
        print_menu()
        choice = input(f"{GREEN}Enter your choice (1-4):{RESET} ")

        if choice == "1":
            start_monitoring(config)
        elif choice == "2":
            stop_monitoring()
        elif choice == "3":
            config = get_user_config()
            create_config_file(config)
        elif choice == "4":
            print(f"{GREEN}Exiting...{RESET}")
            updater.stop()
            break
        else:
            print(f"{RED}Invalid choice. Please try again.{RESET}")

if __name__ == "__main__":
    main()
