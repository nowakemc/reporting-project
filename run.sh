#!/bin/bash
# Aparavi Reporting Dashboard Runner
# This script ensures a clean start of the dashboard by stopping any running instances
# before launching a new one.

echo "Starting Aparavi Reporting Dashboard..."

# Kill any running Streamlit instances
echo "Stopping any previous dashboard instances..."
pkill -f streamlit > /dev/null 2>&1 || true

# Optional small delay to ensure processes are terminated
sleep 1

# Start the dashboard
echo "Launching dashboard..."
cd "$(dirname "$0")"
streamlit run app.py

# This script never reaches here during normal operation
# as the streamlit command runs in the foreground
