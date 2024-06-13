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

# Remove existing symbolic link if it exists
if [ -L $LINK_NAME ]; then
    echo "Removing existing symbolic link..."
    sudo rm $LINK_NAME
fi

# Create a wrapper script to run the Python script with the Python interpreter
echo "Creating wrapper script..."
echo -e "#!/bin/bash\npython3 $(pwd)/$SCRIPT_NAME \"\$@\"" | sudo tee $LINK_NAME > /dev/null

# Set executable permission for the wrapper script
sudo chmod +x $LINK_NAME

echo "Installation complete. You can now use the command 'Grimonitor' to manage the uptime monitor."
