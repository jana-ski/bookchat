#!/bin/bash

echo "Installing Python virtual environment..."
sudo apt-get update
sudo apt-get install -y python3-venv

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete! You can now run:"
echo "source venv/bin/activate"
echo "./push.py"
