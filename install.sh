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

# Create a wrapper script to run the Python script with the Python interpreter
echo "Creating wrapper script..."
echo -e "#!/bin/bash\npython3 $(pwd)/$SCRIPT_NAME \"\$@\"" > /usr/local/bin/Grimonitor

# Set executable permission for the wrapper script
sudo chmod +x /usr/local/bin/Grimonitor

echo "Installation complete. You can now use the command 'Grimonitor' to manage the uptime monitor."
