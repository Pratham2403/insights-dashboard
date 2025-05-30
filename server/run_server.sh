#!/bin/bash

# Script to start the Sprinklr Insights Dashboard server

# Ensure the memory directory exists
python -m app.init

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
