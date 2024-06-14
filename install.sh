#!/bin/bash

# Check if the script is running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root" >&2
    exit 1
fi

# Function to uninstall the script
uninstall() {
    # Stop the service
    systemctl stop uptime_monitor 2>/dev/null

    # Disable the service
    systemctl disable uptime_monitor 2>/dev/null

    # Remove the service file
    rm -f /etc/systemd/system/uptime_monitor.service

    # Remove the log file
    rm -f uptime_monitor.log

    # Remove the configuration file
    rm -f config.json

    # Remove the script file
    rm -f uptime_monitor.py

    # Remove the virtual environment
    rm -rf venv

    # Reload systemd
    systemctl daemon-reload

    echo "Uptime monitor has been uninstalled successfully."
}

# Check if the script is being run for installation or uninstallation
if [ "$1" == "uninstall" ]; then
    uninstall
    exit 0
fi

# Check for older versions and remove them
if [ -f uptime_monitor.py ] || [ -d venv ]; then
    echo "Detected older version. Removing..."
    uninstall
fi

# Install required packages
apt-get update
apt-get install -y python3 python3-venv python3-pip telnet

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install Python dependencies
pip install python-telegram-bot schedule requests

# Create the configuration file
echo "Creating configuration file..."
read -p "Enter the bot token: " bot_token
read -p "Enter your Telegram user ID: " admin_id
read -p "Enter the remote IP address: " remote_ip
read -p "Enter the remote port (default: 80): " remote_port
remote_port=${remote_port:-80}
read -p "Enter the check interval in minutes (default: 5): " check_interval
check_interval=${check_interval:-5}
read -p "Enter the success notification interval in minutes (default: 60): " success_notification_interval
success_notification_interval=${success_notification_interval:-60}

cat > config.json << EOF
{
    "bot_token": "$bot_token",
    "admin_id": "$admin_id",
    "remote_ip": "$remote_ip",
    "remote_port": $remote_port,
    "check_interval": $check_interval,
    "success_notification_interval": $success_notification_interval
}
EOF

# Create the log file
touch uptime_monitor.log

# Create the script file
cat > uptime_monitor.py << 'EOF'
# Paste the uptime_monitor.py script here
EOF

# Create the service file
cat > /etc/systemd/system/uptime_monitor.service << EOF
[Unit]
Description=Uptime Monitor
After=network.target

[Service]
ExecStart=$(pwd)/venv/bin/python $(pwd)/uptime_monitor.py
Restart=always
WorkingDirectory=$(pwd)

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload
systemctl enable uptime_monitor
systemctl start uptime_monitor

echo "Installation completed successfully!"
echo "You can control the uptime monitor using the following commands:"
echo "- systemctl start uptime_monitor (start the service)"
echo "- systemctl stop uptime_monitor (stop the service)"
echo "- systemctl restart uptime_monitor (restart the service)"
echo "- systemctl status uptime_monitor (check the service status)"
echo "To uninstall the uptime monitor, run: sudo ./install.sh uninstall"
echo "You can also interact with the uptime monitor using the Telegram bot."
