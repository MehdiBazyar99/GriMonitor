#!/bin/bash
# Variables
REPO_URL="https://raw.githubusercontent.com/MehdiBazyar99/GriMonitor/main/uptime_monitor.py"
SCRIPT_NAME="uptime_monitor.py"
WRAPPER_SCRIPT="/usr/local/bin/Grimonitor"
VENV_DIR="venv"

# Function to remove old version of the script, virtual environment, and wrapper script if they exist
cleanup() {
    echo "Removing old version of the script, virtual environment, and wrapper script if they exist..."
    [ -f $SCRIPT_NAME ] && rm $SCRIPT_NAME
    [ -d $VENV_DIR ] && rm -rf $VENV_DIR
    [ -f $WRAPPER_SCRIPT ] && sudo rm $WRAPPER_SCRIPT
}

# Function to install required packages and set up virtual environment
setup_environment() {
    echo "Downloading uptime_monitor.py from GitHub..."
    curl -o $SCRIPT_NAME $REPO_URL

    echo "Making the script executable..."
    chmod +x $SCRIPT_NAME

    if ! command -v virtualenv &> /dev/null; then
        echo "Installing virtualenv..."
        python3 -m pip install virtualenv
    fi

    echo "Creating virtual environment..."
    python3 -m virtualenv $VENV_DIR

    echo "Activating virtual environment and installing required Python packages..."
    source $VENV_DIR/bin/activate
    pip install requests schedule python-telegram-bot
    deactivate
}

# Function to create a wrapper script to run the Python script with the virtual environment's Python interpreter
create_wrapper_script() {
    echo "Creating wrapper script..."
    echo -e "#!/bin/bash\n$(pwd)/$VENV_DIR/bin/python $(pwd)/$SCRIPT_NAME" | sudo tee $WRAPPER_SCRIPT > /dev/null
    sudo chmod +x $WRAPPER_SCRIPT
}

# Function to handle menu display and user interaction
display_menu() {
    echo "Installation complete. You can now use the command 'Grimonitor' to manage the uptime monitor."
    echo "Menu:"
    echo "1. Start Script"
    echo "2. Stop Script"
    echo "3. Change Configuration"
    echo "4. Uninstall Script"
    echo "5. Exit"

    while true; do
        read -p "Enter choice [1-5]: " choice
        case $choice in
            1) Grimonitor start ;;
            2) Grimonitor stop ;;
            3) Grimonitor configure ;;
            4) Grimonitor uninstall ;;
            5) exit 0 ;;
            *) echo "Invalid choice! Please choose again." ;;
        esac
    done
}

# Main function to orchestrate the installation
main() {
    cleanup
    setup_environment
    create_wrapper_script
    display_menu
}

main
