import os
import sys
import telnetlib
import requests
import schedule
import time
import subprocess
from getpass import getpass
from threading import Thread, Event
from daemon import DaemonContext
from daemon.pidfile import PIDLockFile
import logging

# Setup logging
logging.basicConfig(filename='/tmp/grimonitor.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for menu
MENU_HEADER = "\033[96m┌────────────────────────────────────────────────────────────────────────────┐\033[0m"
MENU_FOOTER = "\033[96m└────────────────────────────────────────────────────────────────────────────┘\033[0m"
MENU_TITLE = "\033[96m│                          \033[93mGriMonitor Uptime Monitor\033[96m                         │\033[0m"
MENU_SEPARATOR = "\033[96m├────────────────────────────────────────────────────────────────────────────┤\033[0m"
MENU_OPTIONS = [
    "\033[96m│ \033[92m1. Configure                                                               \033[96m│\033[0m",
    "\033[96m│ \033[92m2. Start                                                                   \033[96m│\033[0m",
    "\033[96m│ \033[92m3. Stop                                                                    \033[96m│\033[0m",
    "\033[96m│ \033[92m4. Success Notification Configuration                                      \033[96m│\033[0m",
    "\033[96m│ \033[92m5. View Current Configuration                                              \033[96m│\033[0m",
    "\033[96m│ \033[92m6. View Real-time Operation                                                \033[96m│\033[0m",
    "\033[96m│ \033[92m7. Uninstall                                                               \033[96m│\033[0m",
    "\033[96m│ \033[92m8. Exit                                                                    \033[96m│\033[0m"
]


def install_packages():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "schedule", "python-daemon"])
        logging.info("Required packages installed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error installing packages: {e}")
        print(f"\033[91mError installing packages: {e}\033[0m")
        sys.exit(1)


def config_menu(monitor_thread, stop_event):
    try:
        config = read_config()

        print(MENU_HEADER)
        print("\033[96m│                              \033[93mConfiguration Menu\033[96m                            │\033[0m")
        print(MENU_SEPARATOR)

        ip = input("\033[94mEnter the IP address to monitor (leave blank to keep current value): \033[0m") or config.get('ip', '')
        port = input("\033[94mEnter the port to monitor (leave blank to keep current value): \033[0m") or str(config.get('port', ''))
        interval = input("\033[94mEnter the monitoring interval in minutes (leave blank to keep current value): \033[0m") or str(config.get('interval', ''))
        bot_token = getpass("\033[94mEnter the Telegram bot token (leave blank to keep current value): \033[0m") or config.get('bot_token', '')
        chat_id = input("\033[94mEnter the Telegram chat ID (leave blank to keep current value): \033[0m") or config.get('chat_id', '')

        try:
            port = int(port)
            interval = int(interval)
        except ValueError:
            logging.error("Invalid input for port or interval. Please enter valid numbers.")
            print("\033[91mInvalid input for port or interval. Please enter valid numbers.\033[0m")
            return monitor_thread, stop_event

        new_config = {
            'ip': ip,
            'port': port,
            'interval': interval,
            'bot_token': bot_token,
            'chat_id': chat_id
        }

        if new_config != config:
            with open("config.txt", "w") as config_file:
                config_file.write(f"{ip}\n{port}\n{interval}\n{bot_token}\n{chat_id}")
            logging.info("Configuration saved.")

            if monitor_thread is not None and monitor_thread.is_alive():
                stop_event.set()
                monitor_thread.join(timeout=5)
                stop_event.clear()
                monitor_thread = None

            stop_event = Event()
            monitor_thread = Thread(target=check_connection, args=(stop_event,), daemon=True)
            monitor_thread.start()
            logging.info("Monitoring started with the new configuration.")
            print("\033[92mMonitoring started with the new configuration.\033[0m")
        else:
            logging.info("No changes made to the configuration.")
            print("\033[93mNo changes made to the configuration.\033[0m")

    except Exception as e:
        logging.error(f"Error during configuration: {e}")
        print(f"\033[91mError during configuration: {e}\033[0m")

    print(MENU_FOOTER)
    return monitor_thread, stop_event


def success_notification_menu():
    while True:
        try:
            if os.path.exists("success_config.txt"):
                with open("success_config.txt", "r") as config_file:
                    enabled, interval = config_file.read().split("\n")
                    enabled = enabled.lower() == "true"
                    interval = int(interval)
            else:
                enabled = False
                interval = 60

            print(MENU_HEADER)
            print("\033[96m│                     \033[93mSuccess Notification Configuration\033[96m                    │\033[0m")
            print(MENU_SEPARATOR)
            print(f"\033[96m│ \033[92mEnabled: {str(enabled):<57}\033[96m│\033[0m")
            print(f"\033[96m│ \033[92mInterval: {interval} minutes{' ':<43}\033[96m│\033[0m")
            print(MENU_SEPARATOR)
            print("\033[96m│ \033[92m1. Enable/Disable                                                          \033[96m│\033[0m")
            print("\033[96m│ \033[92m2. Set Interval                                                            \033[96m│\033[0m")
            print("\033[96m│ \033[92m3. Back                                                                    \033[96m│\033[0m")
            print(MENU_FOOTER)

            choice = input("\033[94mEnter your choice (1-3): \033[0m")

            if choice == "1":
                enabled = not enabled
                logging.info(f"Success notifications {'enabled' if enabled else 'disabled'}.")
                print(f"\033[92mSuccess notifications {'enabled' if enabled else 'disabled'}.\033[0m")
                with open("success_config.txt", "w") as config_file:
                    config_file.write(f"{enabled}\n{interval}")
            elif choice == "2":
                interval = int(input("\033[94mEnter the success notification interval in minutes: \033[0m"))
                logging.info(f"Success notification interval set to {interval} minutes.")
                print(f"\033[92mSuccess notification interval set to {interval} minutes.\033[0m")
                with open("success_config.txt", "w") as config_file:
                    config_file.write(f"{enabled}\n{interval}")
            elif choice == "3":
                return
            else:
                logging.warning("Invalid choice in success notification menu.")
                print("\033[91mInvalid choice. Please try again.\033[0m")

        except Exception as e:
            logging.error(f"Error during success notification configuration: {e}")
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
    except (FileNotFoundError, IndexError, ValueError) as e:
        logging.warning(f"Error reading config: {e}")
        return {}


def send_telegram_message(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logging.info(f"Telegram message sent successfully to chat_id {chat_id}.")
        else:
            logging.error(f"Failed to send Telegram message: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Telegram message: {e}")
        print(f"\033[91mError sending Telegram message: {e}\033[0m")

def check_connection(stop_event):
    config = read_config()
    success_config = read_success_config()

    while not stop_event.is_set():
        try:
            telnetlib.Telnet(config["ip"], config["port"], timeout=10)
            if success_config["enabled"]:
                send_telegram_message(config["bot_token"], config["chat_id"], f"Connection to {config['ip']}:{config['port']} is successful.")
            logging.info(f"Connection to {config['ip']}:{config['port']} successful.")
        except Exception as e:
            logging.error(f"Connection to {config['ip']}:{config['port']} failed: {str(e)}")
            send_telegram_message(config["bot_token"], config["chat_id"], f"Connection to {config['ip']}:{config['port']} failed: {str(e)}")

        time.sleep(config["interval"] * 60)


def read_success_config():
    try:
        with open("success_config.txt", "r") as config_file:
            lines = config_file.readlines()
            return {
                "enabled": lines[0].strip().lower() == "true",
                "interval": int(lines[1].strip())
            }
    except (FileNotFoundError, IndexError, ValueError) as e:
        logging.warning(f"Error reading success config: {e}")
        return {
            "enabled": False,
            "interval": 60
        }


def get_script_status(monitor_thread):
    if not os.path.exists("config.txt"):
        return "Not Configured"
    elif monitor_thread is None or not monitor_thread.is_alive():
        return "Stopped"
    else:
        return "Running"


def print_menu(script_status):
    print(MENU_HEADER)
    print(MENU_TITLE)
    print(f"\033[96m│                              \033[93mStatus: {script_status}\033[96m                              │\033[0m")
    print(MENU_SEPARATOR)
    for option in MENU_OPTIONS:
        print(option)
    print(MENU_FOOTER)


def uninstall():
    try:
        confirm = input("\033[94mAre you sure you want to uninstall GriMonitor? (y/n): \033[0m").lower()
        if confirm != 'y':
            return

        delete_all = input("\033[94mDo you want to delete all traces of the script? (y/n): \033[0m").lower() == 'y'

        if os.path.exists("config.txt"):
            os.remove("config.txt")
        if os.path.exists("success_config.txt"):
            os.remove("success_config.txt")

        if delete_all:
            script_path = os.path.abspath(__file__)
            os.remove(script_path)

        logging.info("GriMonitor uninstalled successfully.")
        print("\033[92mGriMonitor uninstalled successfully.\033[0m")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error during uninstallation: {e}")
        print(f"\033[91mError during uninstallation: {e}\033[0m")


def view_current_config():
    config = read_config()
    if config:
        print(MENU_HEADER)
        print("\033[96m│                              \033[93mCurrent Configuration\033[96m                          │\033[0m")
        print(MENU_SEPARATOR)
        print(f"\033[96m│ \033[92mIP Address: {config['ip']:<53}\033[96m│\033[0m")
        print(f"\033[96m│ \033[92mPort: {config['port']:<57}\033[96m│\033[0m")
        print(f"\033[96m│ \033[92mMonitoring Interval: {config['interval']} minutes{' ':<40}\033[96m│\033[0m")
        print(f"\033[96m│ \033[92mTelegram Bot Token: {config['bot_token']:<44}\033[96m│\033[0m")
        print(f"\033[96m│ \033[92mTelegram Chat ID: {config['chat_id']:<48}\033[96m│\033[0m")
        print(MENU_FOOTER)
    else:
        logging.warning("No configuration found. Please configure GriMonitor first.")
        print("\033[91mNo configuration found. Please configure GriMonitor first.\033[0m")


def view_realtime_operation(monitor_thread):
    if monitor_thread is None or not monitor_thread.is_alive():
        logging.warning("Monitoring is not currently running. Please start monitoring to view real-time operation.")
        print("\033[91mMonitoring is not currently running. Please start monitoring to view real-time operation.\033[0m")
        return

    print("\033[92mReal-time Operation:\033[0m")
    print("\033[96mPress Ctrl+C to exit.\033[0m")

    config = read_config()

    try:
        while True:
            try:
                telnetlib.Telnet(config["ip"], config["port"], timeout=10)
                print(f"\033[92mConnection to {config['ip']}:{config['port']} is successful.\033[0m")
            except Exception as e:
                print(f"\033[91mConnection to {config['ip']}:{config['port']} failed: {str(e)}\033[0m")

            time.sleep(1)  # Adjust the sleep time as needed for better responsiveness
    except KeyboardInterrupt:
        logging.info("Exiting real-time operation view.")
        print("\033[96mExiting real-time operation view.\033[0m")


def start_monitoring_daemon(stop_event):
    with DaemonContext(pidfile=PIDLockFile('/tmp/grimonitor.pid')):
        check_connection(stop_event)


def main():
    install_packages()
    stop_event = Event()
    monitor_thread = None
    config = read_config()

    try:
        while True:
            script_status = get_script_status(monitor_thread)
            print_menu(script_status)
            choice = input("\033[94mEnter your choice (1-8): \033[0m")

            if choice == "1":
                monitor_thread, stop_event = config_menu(monitor_thread, stop_event)
            elif choice == "2":
                if config:
                    if monitor_thread is None or not monitor_thread.is_alive():
                        stop_event.clear()
                        monitor_thread = Thread(target=check_connection, args=(stop_event,), daemon=True)
                        monitor_thread.start()
                        logging.info("Monitoring started.")
                        print("\033[92mMonitoring started.\033[0m")
                    else:
                        logging.warning("Monitoring is already running.")
                        print("\033[93mMonitoring is already running.\033[0m")
                else:
                    logging.warning("Please configure GriMonitor first.")
                    print("\033[91mPlease configure GriMonitor first.\033[0m")
            elif choice == "3":
                if monitor_thread is not None:
                    stop_event.set()
                    monitor_thread.join(timeout=5)
                    monitor_thread = None
                    logging.info("Monitoring stopped.")
                    print("\033[92mMonitoring stopped.\033[0m")
                else:
                    logging.warning("Monitoring is not currently running.")
                    print("\033[93mMonitoring is not currently running.\033[0m")
            elif choice == "4":
                success_notification_menu()
            elif choice == "5":
                view_current_config()
            elif choice == "6":
                view_realtime_operation(monitor_thread)
            elif choice == "7":
                uninstall()
            elif choice == "8":
                if monitor_thread is not None and monitor_thread.is_alive():
                    stop_event.set()
                    monitor_thread.join(timeout=5)
                logging.info("Exiting GriMonitor.")
                print("\033[92mExiting...\033[0m")
                break
            else:
                logging.warning("Invalid choice in main menu.")
                print("\033[91mInvalid choice. Please try again.\033[0m")
    except KeyboardInterrupt:
        if monitor_thread is not None and monitor_thread.is_alive():
            stop_event.set()
            monitor_thread.join(timeout=5)
        logging.info("Exiting GriMonitor due to keyboard interrupt.")
        print("\033[92mExiting...\033[0m")

if __name__ == "__main__":
    main()
