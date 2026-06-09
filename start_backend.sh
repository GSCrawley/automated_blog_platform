#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Change to the automated-blog-system directory
cd automated-blog-system

# Start the backend server
python src/main.py --port 5001

# Note: Press Ctrl+C to stop the server