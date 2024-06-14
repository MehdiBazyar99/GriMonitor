import os
import sys
import telnetlib
import requests
import schedule
import time
import subprocess
from getpass import getpass
from threading import Thread, Event


def install_packages():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "schedule"])
    except subprocess.CalledProcessError as e:
        print(f"\033[91mError installing packages: {e}\033[0m")
        sys.exit(1)


def config_menu(update=False):
    try:
        if update and os.path.exists("config.txt"):
            config = read_config()
            ip = input(f"\033[94mEnter the IP address to monitor [{config['ip']}]: \033[0m") or config['ip']
            port = input(f"\033[94mEnter the port to monitor [{config['port']}]: \033[0m") or config['port']
            interval = input(f"\033[94mEnter the monitoring interval in minutes [{config['interval']}]: \033[0m") or config['interval']
            bot_token = getpass(f"\033[94mEnter the Telegram bot token [{config['bot_token']}]: \033[0m") or config['bot_token']
            chat_id = input(f"\033[94mEnter the Telegram chat ID [{config['chat_id']}]: \033[0m") or config['chat_id']
        else:
            ip = input("\033[94mEnter the IP address to monitor: \033[0m")
            port = input("\033[94mEnter the port to monitor: \033[0m")
            interval = input("\033[94mEnter the monitoring interval in minutes: \033[0m")
            bot_token = getpass("\033[94mEnter the Telegram bot token: \033[0m")
            chat_id = input("\033[94mEnter the Telegram chat ID: \033[0m")

        try:
            port = int(port)
            interval = int(interval)
        except ValueError:
            print("\033[91mInvalid input for port or interval. Please enter valid numbers.\033[0m")
            return

        with open("config.txt", "w") as config_file:
            config_file.write(f"{ip}\n{port}\n{interval}\n{bot_token}\n{chat_id}")
        print("\033[92mConfiguration saved.\033[0m")
    except Exception as e:
        print(f"\033[91mError during configuration: {e}\033[0m")


def success_notification_menu():
    try:
        if os.path.exists("success_config.txt"):
            with open("success_config.txt", "r") as config_file:
                enabled, interval = config_file.read().split("\n")
                enabled = enabled.lower() == "true"
                interval = int(interval)
        else:
            enabled = False
            interval = 60

        print("\033[96m┌─────────────────────────────────────────────────┐\033[0m")
        print("\033[96m│        \033[93mSuccess Notification Configuration\033[96m       │\033[0m")
        print("\033[96m├─────────────────────────────────────────────────┤\033[0m")
        print(f"\033[96m│ \033[92mEnabled: {enabled}\033[96m                                    │\033[0m")
        print(f"\033[96m│ \033[92mInterval: {interval} minutes\033[96m                           │\033[0m")
        print("\033[96m├─────────────────────────────────────────────────┤\033[0m")
        print("\033[96m│ \033[92m1. Enable/Disable                               \033[96m│\033[0m")
        print("\033[96m│ \033[92m2. Set Interval                                 \033[96m│\033[0m")
        print("\033[96m│ \033[92m3. Back                                         \033[96m│\033[0m")
        print("\033[96m└─────────────────────────────────────────────────┘\033[0m")

        choice = input("\033[94mEnter your choice (1-3): \033[0m")

        if choice == "1":
            enabled = not enabled
            print(f"\033[92mSuccess notifications {'enabled' if enabled else 'disabled'}.\033[0m")
        elif choice == "2":
            interval = int(input("\033[94mEnter the success notification interval in minutes: \033[0m"))
            print(f"\033[92mSuccess notification interval set to {interval} minutes.\033[0m")
        elif choice == "3":
            return
        else:
            print("\033[91mInvalid choice. Please try again.\033[0m")

        with open("success_config.txt", "w") as config_file:
            config_file.write(f"{enabled}\n{interval}")

    except Exception as e:
        print(f"\033[91mError during success notification configuration: {e}\033[0m")


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
        print("\033[91mError reading configuration file. Please run 'Grimonitor install' first.\033[0m")
        sys.exit(1)


def send_telegram_message(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)
    except requests.exceptions.RequestException as e:
        print(f"\033[91mError sending Telegram message: {e}\033[0m")


def check_connection(ip, port, bot_token, chat_id, success_enabled, success_interval):
    try:
        telnetlib.Telnet(ip, port, timeout=10)
        if success_enabled:
            send_telegram_message(bot_token, chat_id, f"Connection to {ip}:{port} is successful.")
    except Exception as e:
        send_telegram_message(bot_token, chat_id, f"Connection to {ip}:{port} failed: {str(e)}")


def monitor(stop_event):
    config = read_config()
    success_config = read_success_config()
    schedule.every(config["interval"]).minutes.do(
        check_connection, config["ip"], config["port"], config["bot_token"], config["chat_id"],
        success_config["enabled"], success_config["interval"]
    )
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)


def read_success_config():
    try:
        with open("success_config.txt", "r") as config_file:
            lines = config_file.readlines()
            return {
                "enabled": lines[0].strip().lower() == "true",
                "interval": int(lines[1].strip())
            }
    except (FileNotFoundError, IndexError, ValueError):
        return {
            "enabled": False,
            "interval": 60
        }


def print_menu():
    print("\033[96m┌─────────────────────────────────────────────────┐\033[0m")
    print("\033[96m│           \033[93mGriMonitor Uptime Monitor\033[96m            │\033[0m")
    print("\033[96m├─────────────────────────────────────────────────┤\033[0m")
    print("\033[96m│ \033[92m1. Install                                      \033[96m│\033[0m")
    print("\033[96m│ \033[92m2. Start                                        \033[96m│\033[0m")
    print("\033[96m│ \033[92m3. Stop                                         \033[96m│\033[0m")
    print("\033[96m│ \033[92m4. Status                                       \033[96m│\033[0m")
    print("\033[96m│ \033[92m5. Update Configuration                         \033[96m│\033[0m")
    print("\033[96m│ \033[92m6. Success Notification Configuration           \033[96m│\033[0m")
    print("\033[96m│ \033[92m7. Uninstall                                    \033[96m│\033[0m")
    print("\033[96m│ \033[92m8. Exit                                         \033[96m│\033[0m")
    print("\033[96m└─────────────────────────────────────────────────┘\033[0m")


def main():
    install_packages()
    stop_event = Event()
    monitor_thread = None

    while True:
        print_menu()
        choice = input("\033[94mEnter your choice (1-8): \033[0m")

        if choice == "1":
            config_menu()
        elif choice == "2":
            if os.path.exists("config.txt"):
                if monitor_thread is None or not monitor_thread.is_alive():
                    stop_event.clear()
                    monitor_thread = Thread(target=monitor, args=(stop_event,))
                    monitor_thread.start()
                    print("\033[92mMonitoring started.\033[0m")
                else:
                    print("\033[93mMonitoring is already running.\033[0m")
            else:
                print("\033[91mPlease run 'Grimonitor install' first.\033[0m")
        elif choice == "3":
            if monitor_thread is not None and monitor_thread.is_alive():
                stop_event.set()
                monitor_thread.join()
                print("\033[92mMonitoring stopped.\033[0m")
            else:
                print("\033[93mMonitoring is not currently running.\033[0m")
        elif choice == "4":
            if monitor_thread is not None and monitor_thread.is_alive():
                print("\033[92mMonitoring is currently running.\033[0m")
            else:
                print("\033[93mMonitoring is not currently running.\033[0m")
        elif choice == "5":
            if os.path.exists("config.txt"):
                config_menu(update=True)
            else:
                print("\033[91mPlease run 'Grimonitor install' first.\033[0m")
        elif choice == "6":
            success_notification_menu()
        elif choice == "7":
            if os.path.exists("config.txt"):
                os.remove("config.txt")
                print("\033[92mUninstalled.\033[0m")
            else:
                print("\033[93mNo configuration file found.\033[0m")
        elif choice == "8":
            if monitor_thread is not None and monitor_thread.is_alive():
                stop_event.set()
                monitor_thread.join()
            print("\033[92mExiting...\033[0m")
            break
        else:
            print("\033[91mInvalid choice. Please try again.\033[0m")


if __name__ == "__main__":
    main()
