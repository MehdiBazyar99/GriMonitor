#!/bin/bash

# Variables
REPO_URL="https://raw.githubusercontent.com/MehdiBazyar99/GriMonitor/main/uptime_monitor.py"
SCRIPT_NAME="uptime_monitor.py"
LINK_NAME="/usr/local/bin/Grimonitor"

# Download the Python script
echo "Downloading uptime_monitor.py from GitHub..."
curl -o $SCRIPT_NAME $REPO_URL

# Make the script executable
chmod +x $SCRIPT_NAME

# Install required Python packages
echo "Installing required Python packages..."
python3 -m pip install requests schedule

# Create a symbolic link
echo "Creating symbolic link..."
sudo ln -s "$(pwd)/$SCRIPT_NAME" $LINK_NAME

# Set executable permission for the symbolic link
sudo chmod +x $LINK_NAME

echo "Installation complete. You can now use the command 'Grimonitor' to manage the uptime monitor."
