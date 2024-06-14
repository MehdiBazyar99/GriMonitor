import os
import time
import schedule
import requests
import telnetlib
import logging
from telegram import Bot
from telegram.ext import CommandHandler, Updater

# Configuration
CONFIG_FILE = 'config.txt'

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read configuration from file
def read_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                name, value = line.strip().split('=')
                config[name] = value
    return config

config = read_config()

# Telegram Bot setup
bot_token = config.get('BOT_TOKEN')
chat_id = config.get('CHAT_ID')
bot = Bot(token=bot_token)
updater = Updater(token=bot_token, use_context=True)

# Ping function
def ping():
    try:
        with telnetlib.Telnet(config['IP'], config['PORT']) as tn:
            logger.info(f"Successfully connected to {config['IP']} on port {config['PORT']}")
            return True
    except:
        logger.error(f"Failed to connect to {config['IP']} on port {config['PORT']}")
        bot.send_message(chat_id=chat_id, text=f"Failed to connect to {config['IP']} on port {config['PORT']}")
        return False

# Command handlers for Telegram bot
def start(update, context):
    schedule.every(int(config['INTERVAL'])).minutes.do(ping)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Uptime monitor started.")

def stop(update, context):
    schedule.clear()
    context.bot.send_message(chat_id=update.effective_chat.id, text="Uptime monitor stopped.")

def configure(update, context):
    args = context.args
    if len(args) != 2:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /configure <key> <value>")
        return
    key, value = args
    config[key.upper()] = value
    with open(CONFIG_FILE, 'w') as f:
        for k, v in config.items():
            f.write(f"{k}={v}\n")
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Configuration updated: {key}={value}")

def status(update, context):
    status_message = "\n".join([f"{k}={v}" for k, v in config.items()])
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Current configuration:\n{status_message}")

# Adding handlers to dispatcher
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('stop', stop))
dispatcher.add_handler(CommandHandler('configure', configure))
dispatcher.add_handler(CommandHandler('status', status))

# Starting the bot
updater.start_polling()

# Main loop to keep the script running and check schedule
while True:
    schedule.run_pending()
    time.sleep(1)
