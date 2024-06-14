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

def install_packages():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "schedule", "python-telegram-bot"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def config_menu(update=False, change_value=None):
    try:
        print(f"{BLUE}Current working directory: {os.getcwd()}{RESET}")
        
        # Check if config.txt exists
        if os.path.exists("config.txt"):
            config = read_config()
            print(f"{GREEN}Configuration file found.{RESET}")
        else:
            config = {
                "ip": "",
                "port": "",
                "interval": "",
                "bot_token": "",
                "chat_id": "",
                "success_interval": ""
            }
            print(f"{RED}Configuration file not found. Creating a new one.{RESET}")

        # Update or change specific values if requested
        if update or change_value:
            if change_value:
                value_to_change = change_value
            else:
                value_to_change = input(f"{BLUE}Enter the value to change (ip/port/interval/bot_token/chat_id/success_interval):{RESET} ")

            if value_to_change.lower() in config:
                if value_to_change.lower() in ["port", "interval", "success_interval"]:
                    new_value = input(f"{GREEN}Enter the new {value_to_change.lower()} [{config[value_to_change.lower()]}]:{RESET} ").strip()
                    if new_value:
                        try:
                            config[value_to_change.lower()] = int(new_value)
                        except ValueError:
                            print(f"{RED}Invalid input for {value_to_change.lower()}. Please enter a valid number.{RESET}")
                            return
                else:
                    config[value_to_change.lower()] = input(f"{GREEN}Enter the new {value_to_change.lower()} [{config[value_to_change.lower()]}]:{RESET} ").strip()
            else:
                print(f"{RED}Invalid value to change. Please try again.{RESET}")
                return
        else:
            # Prompt user to input all configuration values if not updating
            config["ip"] = input(f"{GREEN}Enter the IP address to monitor:{RESET} ").strip()
            port = input(f"{GREEN}Enter the port to monitor:{RESET} ").strip()
            try:
                config["port"] = int(port)
            except ValueError:
                print(f"{RED}Invalid input for port. Please enter a valid number.{RESET}")
                return
            interval = input(f"{GREEN}Enter the interval in minutes:{RESET} ").strip()
            try:
                config["interval"] = int(interval)
            except ValueError:
                print(f"{RED}Invalid input for interval. Please enter a valid number.{RESET}")
                return
            config["bot_token"] = getpass(f"{GREEN}Enter the Telegram bot token:{RESET} ").strip()
            config["chat_id"] = input(f"{GREEN}Enter the Telegram chat ID:{RESET} ").strip()
            success_interval = input(f"{GREEN}Enter the interval in minutes for success notifications:{RESET} ").strip()
            try:
                config["success_interval"] = int(success_interval)
            except ValueError:
                print(f"{RED}Invalid input for success interval. Please enter a valid number.{RESET}")
                return

        # Write updated or new configuration to config.txt
        with open("config.txt", "w") as config_file:
            config_file.write(f"{config['ip']}\n{config['port']}\n{config['interval']}\n{config['bot_token']}\n{config['chat_id']}\n{config['success_interval']}")
            print(f"{GREEN}Configuration file updated successfully.{RESET}")
        print(f"{GREEN}Configuration saved.{RESET}")

    except Exception as e:
        print(f"{RED}Error during configuration: {e}{RESET}")

def read_config():
    config_keys = ["ip", "port", "interval", "bot_token", "chat_id", "success_interval"]
    try:
        with open("config.txt", "r") as config_file:
            lines = config_file.readlines()
            if len(lines) != len(config_keys):
                raise ValueError("Incomplete configuration file")
            config = {}
            for key, value in zip(config_keys, lines):
                value = value.strip()
                if key in ["port", "interval", "success_interval"]:
                    config[key] = int(value)
                else:
                    config[key] = value
            return config
    except FileNotFoundError:
        print(f"{RED}Error: Configuration file 'config.txt' not found. Creating a new one.{RESET}")
        config_menu()
        return read_config()  # Retry reading config after creation
    except (ValueError, IndexError) as e:
        print(f"{RED}Error: Invalid configuration file format. Please check 'config.txt'. Details: {e}{RESET}")
        config_menu()
        return read_config()  # Retry reading config after menu interaction
    except Exception as e:
        print(f"{RED}Error reading configuration file: {e}{RESET}")
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
    schedule.every(config["interval"]).minutes.do(
        check_connection, config["ip"], config["port"], config["bot_token"], config["chat_id"], config["success_interval"]
    )
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_monitoring():
    config = read_config()
    monitoring_thread = Thread(target=monitor, args=(config,))
    monitoring_thread.start()
    print(f"{GREEN}Monitoring started in the background.{RESET}")

def stop_monitoring():
    schedule.clear()
    print(f"{RED}Monitoring stopped.{RESET}")

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

def main():
    install_packages()

    updater = Updater(token=read_config()["bot_token"], use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", handle_telegram_command))
    dispatcher.add_handler(CommandHandler("stop", handle_telegram_command))
    dispatcher.add_handler(CommandHandler("ping", handle_telegram_command))
    updater.start_polling()

    while True:
        print_menu()
        choice = input(f"{GREEN}Enter your choice (1-7):{RESET} ")

        if choice == "1":
            config_menu()
        elif choice == "2":
            if os.path.exists("config.txt"):
                start_monitoring()
            else:
                print(f"{RED}Please run 'Grimonitor install' first.{RESET}")
        elif choice == "3":
            stop_monitoring()
        elif choice == "4":
            if os.path.exists("config.txt"):
                config_menu(update=True)
            else:
                print(f"{RED}Please run 'Grimonitor install' first.{RESET}")
        elif choice == "5":
            if os.path.exists("config.txt"):
                config_menu(change_value=True)
            else:
                print(f"{RED}Please run 'Grimonitor install' first.{RESET}")
        elif choice == "6":
            if os.path.exists("config.txt"):
                os.remove("config.txt")
                print(f"{GREEN}Uninstalled.{RESET}")
            else:
                print(f"{RED}No configuration file found.{RESET}")
        elif choice == "7":
            print(f"{GREEN}Exiting...{RESET}")
            updater.stop()
            break
        else:
            print(f"{RED}Invalid choice. Please try again.{RESET}")

if __name__ == "__main__":
    main()
