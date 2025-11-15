#!/bin/bash
echo "1: Run CLI"
echo "2: Run GUI"
echo "3: Install dependencies"
echo "3: Exit"
read -p "Enter your choice: " choice
case $choice in
    1)
        echo "Starting CLI"
        python3 cli.py
        ;;
    2)
        echo "Starting GUI"
        python3 gui.py
        ;;
    3)
        echo "Installing dependencies"
        pip3 install -r requirements.txt
        ;;
    4)
        echo "Exiting"
        exit 0
        ;;
    *)
        echo "Invalid choice. Please select 1, 2, or 3."
        ;;
esac