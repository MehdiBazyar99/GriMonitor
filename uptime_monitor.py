import os
import sys
import telnetlib
import requests
import schedule
import time
from getpass import getpass

def config_menu(update=False):
    try:
        if update and os.path.exists("config.txt"):
            config = read_config()
            ip = input(f"Enter the IP address to monitor [{config['ip']}]: ") or config['ip']
            port = input(f"Enter the port to monitor [{config['port']}]: ") or config['port']
            interval = input(f"Enter the interval in minutes [{config['interval']}]: ") or config['interval']
            bot_token = getpass(f"Enter the Telegram bot token [{config['bot_token']}]: ") or config['bot_token']
            chat_id = input(f"Enter the Telegram chat ID [{config['chat_id']}]: ") or config['chat_id']
        else:
            ip = input("Enter the IP address to monitor: ")
            port = input("Enter the port to monitor: ")
            interval = input("Enter the interval in minutes: ")
            bot_token = getpass("Enter the Telegram bot token: ")
            chat_id = input("Enter the Telegram chat ID: ")

        try:
            port = int(port)
            interval = int(interval)
        except ValueError:
            print("Invalid input for port or interval. Please enter valid numbers.")
            return

        with open("config.txt", "w") as config_file:
            config_file.write(f"{ip}\n{port}\n{interval}\n{bot_token}\n{chat_id}")
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
                "chat_id": lines[4].strip()
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

def check_connection(ip, port, bot_token, chat_id):
    try:
        telnetlib.Telnet(ip, port, timeout=10)
    except Exception as e:
        send_telegram_message(bot_token, chat_id, f"Connection to {ip}:{port} failed: {str(e)}")

def monitor():
    try:
        config = read_config()
        schedule.every(config["interval"]).minutes.do(
            check_connection, config["ip"], config["port"], config["bot_token"], config["chat_id"]
        )
        print("Monitoring started. Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Monitoring stopped.")

def print_menu():
    print("GriMonitor Uptime Monitor")
    print("1. Start")
    print("2. Update")
    print("3. Exit")

def main():
    while True:
        print_menu()
        choice = input("Enter your choice (1-3): ")

        if choice == "1":
            if os.path.exists("config.txt"):
                monitor()
            else:
                print("Please run 'Grimonitor install' first.")
        elif choice == "2":
            if os.path.exists("config.txt"):
                config_menu(update=True)
            else:
                print("Please run 'Grimonitor install' first.")
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
