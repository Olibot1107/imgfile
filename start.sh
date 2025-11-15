#!/bin/bash

# check if at least one argument is provided
if [ $# -eq 0 ]; then
    echo "No arguments provided. Please choose an option:"
    echo "1: Run CLI"
    echo "2: Run GUI"
    echo "3: Install dependencies"
    echo "4: Exit"
    read -p "Enter your choice (1-4): " choice
else
    choice=$1
fi

case $choice in
    1)
        echo "Starting CLI..."
        python3 cli.py
        ;;
    2)
        echo "Starting GUI..."
        python3 app.py
        ;;
    3)
        echo "Installing dependencies..."
        pip install -r requirements.txt
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run the script again and choose a valid option."
        exit 1
        ;;
esac