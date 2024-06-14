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
MONITORING_THREAD = None
MENU_OPTIONS = {
    "1": config_menu,
    "2": start_monitoring,
    "3": stop_monitoring,
    "4": lambda: config_menu(update=True),
    "5": lambda: config_menu(change_value=True),
    "6": uninstall
}

def install_packages():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "schedule", "python-telegram-bot"])
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error installing packages: {e}{RESET}")
        sys.exit(1)

def check_config_exists():
    if not os.path.exists(CONFIG_FILE):
        print(f"{RED}Please run 'Grimonitor install' first.{RESET}")
        return False
    return True

def config_menu(update=False, change_value=None):
    try:
        if os.path.exists(CONFIG_FILE):
            config = read_config()
        else:
            config = {
                "ip": "",
                "port": "",
                "interval": "",
                "bot_token": "",
                "chat_id": "",
                "success_interval": ""
            }

        if update or change_value:
            if change_value:
                value_to_change = change_value
            else:
                value_to_change = input(f"{BLUE}Enter the value to change (ip/port/interval/bot_token/chat_id/success_interval):{RESET} ")

            if value_to_change.lower() == "ip":
                config["ip"] = input(f"{GREEN}Enter the IP address to monitor [{config['ip']}]:{RESET} ") or config["ip"]
            elif value_to_change.lower() == "port":
                port = input(f"{GREEN}Enter the port to monitor [{config['port']}]:{RESET} ") or config["port"]
                try:
                    config["port"] = int(port)
                except ValueError:
                    print(f"{RED}Invalid input for port. Please enter a valid number.{RESET}")
                    return
            elif value_to_change.lower() == "interval":
                interval = input(f"{GREEN}Enter the interval in minutes [{config['interval']}]:{RESET} ") or config["interval"]
                try:
                    config["interval"] = int(interval)
                except ValueError:
                    print(f"{RED}Invalid input for interval. Please enter a valid number.{RESET}")
                    return
            elif value_to_change.lower() == "bot_token":
                config["bot_token"] = getpass(f"{GREEN}Enter the Telegram bot token [{config['bot_token']}]:{RESET} ") or config["bot_token"]
            elif value_to_change.lower() == "chat_id":
                config["chat_id"] = input(f"{GREEN}Enter the Telegram chat ID [{config['chat_id']}]:{RESET} ") or config["chat_id"]
            elif value_to_change.lower() == "success_interval":
                success_interval = input(f"{GREEN}Enter the interval in minutes for success notifications [{config['success_interval']}]:{RESET} ") or config["success_interval"]
                try:
                    config["success_interval"] = int(success_interval)
                except ValueError:
                    print(f"{RED}Invalid input for success interval. Please enter a valid number.{RESET}")
                    return
            else:
                print(f"{RED}Invalid value to change. Please try again.{RESET}")
                return
        else:
            config["ip"] = input(f"{GREEN}Enter the IP address to monitor:{RESET} ")
            port = input(f"{GREEN}Enter the port to monitor:{RESET} ")
            try:
                config["port"] = int(port)
            except ValueError:
                print(f"{RED}Invalid input for port. Please enter a valid number.{RESET}")
                return
            interval = input(f"{GREEN}Enter the interval in minutes:{RESET} ")
            try:
                config["interval"] = int(interval)
            except ValueError:
                print(f"{RED}Invalid input for interval. Please enter a valid number.{RESET}")
                return
            config["bot_token"] = getpass(f"{GREEN}Enter the Telegram bot token:{RESET} ")
            config["chat_id"] = input(f"{GREEN}Enter the Telegram chat ID:{RESET} ")
            success_interval = input(f"{GREEN}Enter the interval in minutes for success notifications:{RESET} ")
            try:
                config["success_interval"] = int(success_interval)
            except ValueError:
                print(f"{RED}Invalid input for success interval. Please enter a valid number.{RESET}")
                return

        with open(CONFIG_FILE, "w") as config_file:
            config_file.write(f"{config['ip']}\n{config['port']}\n{config['interval']}\n{config['bot_token']}\n{config['chat_id']}\n{config['success_interval']}")
        print(f"{GREEN}Configuration saved.{RESET}")
    except Exception as e:
        print(f"{RED}Error during configuration: {e}{RESET}")

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
    except (FileNotFoundError, IndexError, ValueError):
        print(f"{RED}Error reading configuration file. Please run 'Grimonitor install' first.{RESET}")
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
        telnetlib.Telnet(ip, port, timeout=10)
        send_telegram_message(bot_token, chat_id, f"{GREEN}Connection to {ip}:{port} successful.{RESET}")
        schedule.every(success_interval).minutes.do(send_telegram_message, bot_token, chat_id, f"{GREEN}Connection to {ip}:{port} successful.{RESET}")
    except Exception as e:
        send_telegram_message(bot_token, chat_id, f"{RED}Connection to {ip}:{port} failed: {str(e)}{RESET}")

def monitor(config):
    global MONITORING_THREAD
    if MONITORING_THREAD and MONITORING_THREAD.is_alive():
        print(f"{RED}Monitoring is already running.{RESET}")
        return

    schedule.every(config["interval"]).minutes.do(
        check_connection, config["ip"], config["port"], config["bot_token"], config["chat_id"], config["success_interval"]
    )
    MONITORING_THREAD = Thread(target=monitor_loop, daemon=True)
    MONITORING_THREAD.start()
    print(f"{GREEN}Monitoring started in the background.{RESET}")

def monitor_loop():
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_monitoring():
    if not check_config_exists():
        return
    monitor(read_config())

def stop_monitoring():
    global MONITORING_THREAD
    if MONITORING_THREAD and MONITORING_THREAD.is_alive():
        schedule.clear()
        MONITORING_THREAD.join()
        MONITORING_THREAD = None
        print(f"{RED}Monitoring stopped.{RESET}")
    else:
        print(f"{RED}Monitoring is not running.{RESET}")

def print_menu():
    print(f"{BLUE}GriMonitor Uptime Monitor{RESET}")
    print(f"{YELLOW}1. Install{RESET}")
    print(f"{YELLOW}2. Start{RESET}")
    print(f"{YELLOW}3. Stop{RESET}")
    print(f"{YELLOW}4. Update{RESET}")
    print(f"{YELLOW}5. Change Value{RESET}")
    print(f"{YELLOW}6. Uninstall{RESET}")
    print(f"{YELLOW}7. Exit{RESET}")

def handle_telegram_command(update, context):
    message = update.message.text
    config = read_config()

    if message.startswith("/start"):
        start_monitoring()
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
            telnetlib.Telnet(config["ip"], port, timeout=10)
            send_telegram_message(config["bot_token"], config["chat_id"], f"{GREEN}Connection to {config['ip']}:{port} successful.{RESET}")
        except Exception as e:
            send_telegram_message(config["bot_token"], config["chat_id"], f"{RED}Connection to {config['ip']}:{port} failed: {str(e)}{RESET}")
    else:
        send_telegram_message(config["bot_token"], config["chat_id"], f"{RED}Invalid command. Available commands: /start, /stop, /ping <port>{RESET}")

def uninstall():
    if check_config_exists():
        os.remove(CONFIG_FILE)
        print(f"{GREEN}Uninstalled.{RESET}")
    else:
        print(f"{RED}No configuration file found.{RESET}")

def main():
    install_packages()

    updater = Updater(read_config()["bot_token"], use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", handle_telegram_command))
    dispatcher.add_handler(CommandHandler("stop", handle_telegram_command))
    dispatcher.add_handler(CommandHandler("ping", handle_telegram_command))
    updater.start_polling()

    while True:
        print_menu()
        choice = input(f"{GREEN}Enter your choice (1-7):{RESET} ")

        if choice in MENU_OPTIONS:
            if choice != "1" and not check_config_exists():
                continue
            MENU_OPTIONS[choice]()
        elif choice == "7":
            print(f"{GREEN}Exiting...{RESET}")
            updater.stop()
            break
        else:
            print(f"{RED}Invalid choice. Please try again.{RESET}")

if __name__ == "__main__":
    main()
