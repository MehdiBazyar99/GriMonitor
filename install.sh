#!/bin/bash
# Variables
REPO_URL="https://raw.githubusercontent.com/MehdiBazyar99/GriMonitor/main/uptime_monitor.py"
SCRIPT_NAME="uptime_monitor.py"
WRAPPER_SCRIPT="/usr/local/bin/Grimonitor"
VENV_DIR="venv"

# Function to check if a package is installed
is_package_installed() {
    python3 -c "import pkgutil; exit(0 if pkgutil.find_loader('$1') else 1)"
}

# Function to install the script
install_script() {
    echo "Installing GriMonitor..."
    # Download the new Python script
    echo "Downloading uptime_monitor.py from GitHub..."
    curl -o $SCRIPT_NAME $REPO_URL
    # Make the script executable
    chmod +x $SCRIPT_NAME
    # Install virtualenv if not installed
    if ! command -v virtualenv &> /dev/null; then
        echo "Installing virtualenv..."
        python3 -m pip install virtualenv
    fi
    # Create a virtual environment
    echo "Creating virtual environment..."
    python3 -m virtualenv $VENV_DIR
    # Activate the virtual environment
    source $VENV_DIR/bin/activate
    # Install required Python packages in the virtual environment if not already installed
    for package in "requests" "schedule"; do
        if ! is_package_installed $package; then
            echo "Installing $package..."
            pip install $package
        else
            echo "$package is already installed."
        fi
    done
    # Deactivate the virtual environment
    deactivate
    # Create a wrapper script to run the Python script with the virtual environment's Python interpreter
    echo "Creating wrapper script..."
    echo -e "#!/bin/bash\n$(pwd)/$VENV_DIR/bin/python $(pwd)/$SCRIPT_NAME" | sudo tee $WRAPPER_SCRIPT > /dev/null
    # Set executable permission for the wrapper script
    sudo chmod +x $WRAPPER_SCRIPT
    echo "Installation complete. You can now use the command 'Grimonitor' to manage the uptime monitor."
}

# Function to uninstall the script
uninstall_script() {
    echo "Uninstalling GriMonitor..."
    # Remove the script, virtual environment, and wrapper script
    [ -f $SCRIPT_NAME ] && rm $SCRIPT_NAME
    [ -d $VENV_DIR ] && rm -rf $VENV_DIR
    [ -f $WRAPPER_SCRIPT ] && sudo rm $WRAPPER_SCRIPT
    echo "Uninstallation complete."
}

# Main script
if [ "$1" = "install" ]; then
    install_script
elif [ "$1" = "uninstall" ]; then
    uninstall_script
else
    echo "Usage: install.sh [install|uninstall]"
fi
