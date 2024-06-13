import os
import sys
import telnetlib
import requests
import schedule
import time
import subprocess

def install_packages():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "schedule"])

install_packages()

def config_menu(update=False):
    if update and os.path.exists("config.txt"):
        config = read_config()
        ip = input(f"Enter the IP address to monitor [{config['ip']}]: ") or config['ip']
        port = input(f"Enter the port to monitor [{config['port']}]: ") or config['port']
        interval = input(f"Enter the interval in minutes [{config['interval']}]: ") or config['interval']
        bot_token = input(f"Enter the Telegram bot token [{config['bot_token']}]: ") or config['bot_token']
        chat_id = input(f"Enter the Telegram chat ID [{config['chat_id']}]: ") or config['chat_id']
    else:
        ip = input("Enter the IP address to monitor: ")
        port = input("Enter the port to monitor: ")
        interval = input("Enter the interval in minutes: ")
        bot_token = input("Enter the Telegram bot token: ")
        chat_id = input("Enter the Telegram chat ID: ")

    with open("config.txt", "w") as config_file:
        config_file.write(f"{ip}\n{port}\n{interval}\n{bot_token}\n{chat_id}")

    print("Configuration saved.")

def read_config():
    with open("config.txt", "r") as config_file:
        lines = config_file.readlines()
        return {
            "ip": lines[0].strip(),
            "port": int(lines[1].strip()),
            "interval": int(lines[2].strip()),
            "bot_token": lines[3].strip(),
            "chat_id": lines[4].strip()
        }

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def check_connection(ip, port, bot_token, chat_id):
    try:
        telnetlib.Telnet(ip, port, timeout=10)
    except Exception as e:
        send_telegram_message(bot_token, chat_id, f"Connection to {ip}:{port} failed: {str(e)}")

def monitor():
    config = read_config()
    schedule.every(config["interval"]).minutes.do(
        check_connection, config["ip"], config["port"], config["bot_token"], config["chat_id"]
    )

    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "install":
            config_menu()
        elif command == "start":
            monitor()
        elif command == "update":
            config_menu(update=True)
        elif command == "uninstall":
            if os.path.exists("config.txt"):
                os.remove("config.txt")
                print("Uninstalled.")
            else:
                print("No configuration file found.")
        else:
            print("Unknown command.")
    else:
        print("Usage: python uptime_monitor.py [install|start|update|uninstall]")

if __name__ == "__main__":
    main()
