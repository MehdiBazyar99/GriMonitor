#!/bin/bash

# Variables
REPO_URL="https://raw.githubusercontent.com/MehdiBazyar99/GriMonitor/main/uptime_monitor.py"
SCRIPT_NAME="uptime_monitor.py"
WRAPPER_SCRIPT="/usr/local/bin/Grimonitor"

# Download the Python script
echo "Downloading uptime_monitor.py from GitHub..."
curl -o $SCRIPT_NAME $REPO_URL

# Make the script executable
chmod +x $SCRIPT_NAME

# Install required Python packages
echo "Installing required Python packages..."
python3 -m pip install requests schedule

# Remove existing wrapper script if it exists
if [ -f $WRAPPER_SCRIPT ]; then
    echo "Removing existing wrapper script..."
    sudo rm $WRAPPER_SCRIPT
fi

# Create a wrapper script to run the Python script with the Python interpreter
echo "Creating wrapper script..."
echo -e "#!/bin/bash\n/usr/bin/python3 $(pwd)/$SCRIPT_NAME \"\$@\"" | sudo tee $WRAPPER_SCRIPT > /dev/null

# Set executable permission for the wrapper script
sudo chmod +x $WRAPPER_SCRIPT

echo "Installation complete. You can now use the command 'Grimonitor' to manage the uptime monitor."
