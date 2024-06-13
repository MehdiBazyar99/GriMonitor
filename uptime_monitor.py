import os
import sys
import telnetlib
import requests
import schedule
import time
import subprocess
from getpass import getpass
from threading import Thread

def install_packages():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "schedule"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def config_menu(update=False, change_value=None):
    try:
        if os.path.exists("config.txt"):
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
                value_to_change = input("Enter the value to change (ip/port/interval/bot_token/chat_id/success_interval): ")

            if value_to_change.lower() == "ip":
                config["ip"] = input(f"Enter the IP address to monitor [{config['ip']}]: ") or config["ip"]
            elif value_to_change.lower() == "port":
                port = input(f"Enter the port to monitor [{config['port']}]: ") or config["port"]
                try:
                    config["port"] = int(port)
                except ValueError:
                    print("Invalid input for port. Please enter a valid number.")
                    return
            elif value_to_change.lower() == "interval":
                interval = input(f"Enter the interval in minutes [{config['interval']}]: ") or config["interval"]
                try:
                    config["interval"] = int(interval)
                except ValueError:
                    print("Invalid input for interval. Please enter a valid number.")
                    return
            elif value_to_change.lower() == "bot_token":
                config["bot_token"] = getpass(f"Enter the Telegram bot token [{config['bot_token']}]: ") or config["bot_token"]
            elif value_to_change.lower() == "chat_id":
                config["chat_id"] = input(f"Enter the Telegram chat ID [{config['chat_id']}]: ") or config["chat_id"]
            elif value_to_change.lower() == "success_interval":
                success_interval = input(f"Enter the interval in minutes for success notifications [{config['success_interval']}]: ") or config["success_interval"]
                try:
                    config["success_interval"] = int(success_interval)
                except ValueError:
                    print("Invalid input for success interval. Please enter a valid number.")
                    return
            else:
                print("Invalid value to change. Please try again.")
                return
        else:
            config["ip"] = input("Enter the IP address to monitor: ")
            port = input("Enter the port to monitor: ")
            try:
                config["port"] = int(port)
            except ValueError:
                print("Invalid input for port. Please enter a valid number.")
                return
            interval = input("Enter the interval in minutes: ")
            try:
                config["interval"] = int(interval)
            except ValueError:
                print("Invalid input for interval. Please enter a valid number.")
                return
            config["bot_token"] = getpass("Enter the Telegram bot token: ")
            config["chat_id"] = input("Enter the Telegram chat ID: ")
            success_interval = input("Enter the interval in minutes for success notifications: ")
            try:
                config["success_interval"] = int(success_interval)
            except ValueError:
                print("Invalid input for success interval. Please enter a valid number.")
                return

        with open("config.txt", "w") as config_file:
            config_file.write(f"{config['ip']}\n{config['port']}\n{config['interval']}\n{config['bot_token']}\n{config['chat_id']}\n{config['success_interval']}")
        print("Configuration saved.")
    except Exception as e:
        print(f"Error during configuration: {e}")
def read_config():
    try:
        with open("config.txt", "r") as config_file:
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
        print("Error reading configuration file. Please run 'Grimonitor install' first.")
        sys.exit(1)

def send_telegram_message(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")

def check_connection(ip, port, bot_token, chat_id, success_interval):
    try:
        telnetlib.Telnet(ip, port, timeout=10)
        send_telegram_message(bot_token, chat_id, f"Connection to {ip}:{port} successful.")
        schedule.every(success_interval).minutes.do(send_telegram_message, bot_token, chat_id, f"Connection to {ip}:{port} successful.")
    except Exception as e:
        send_telegram_message(bot_token, chat_id, f"Connection to {ip}:{port} failed: {str(e)}")

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
    print("Monitoring started in the background.")

def stop_monitoring():
    schedule.clear()
    print("Monitoring stopped.")

def print_menu():
    print("GriMonitor Uptime Monitor")
    print("1. Install")
    print("2. Start")
    print("3. Stop")
    print("4. Update")
    print("5. Change Value")
    print("6. Uninstall")
    print("7. Exit")

def handle_telegram_command(update):
    message = update.message.text
    config = read_config()

    if message.startswith("/start"):
        start_monitoring()
        send_telegram_message(config["bot_token"], config["chat_id"], "Monitoring started.")
    elif message.startswith("/stop"):
        stop_monitoring()
        send_telegram_message(config["bot_token"], config["chat_id"], "Monitoring stopped.")
    elif message.startswith("/ping"):
        try:
            port = int(message.split()[1])
        except (IndexError, ValueError):
            send_telegram_message(config["bot_token"], config["chat_id"], "Invalid command format. Usage: /ping <port>")
            return
        try:
            telnetlib.Telnet(config["ip"], port, timeout=10)
            send_telegram_message(config["bot_token"], config["chat_id"], f"Connection to {config['ip']}:{port} successful.")
        except Exception as e:
            send_telegram_message(config["bot_token"], config["chat_id"], f"Connection to {config['ip']}:{port} failed: {str(e)}")
    else:
        send_telegram_message(config["bot_token"], config["chat_id"], "Invalid command. Available commands: /start, /stop, /ping <port>")

def main():
    install_packages()

    while True:
        print_menu()
        choice = input("Enter your choice (1-7): ")

        if choice == "1":
            config_menu()
        elif choice == "2":
            if os.path.exists("config.txt"):
                start_monitoring()
            else:
                print("Please run 'Grimonitor install' first.")
        elif choice == "3":
            stop_monitoring()
        elif choice == "4":
            if os.path.exists("config.txt"):
                config_menu(update=True)
            else:
                print("Please run 'Grimonitor install' first.")
        elif choice == "5":
            if os.path.exists("config.txt"):
                config_menu(change_value=True)
            else:
                print("Please run 'Grimonitor install' first.")
        elif choice == "6":
            if os.path.exists("config.txt"):
                os.remove("config.txt")
                print("Uninstalled.")
            else:
                print("No configuration file found.")
        elif choice == "7":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
