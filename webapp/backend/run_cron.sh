#!/bin/bash

# Cron job script for processing video submissions
# This script should be run from the backend directory

LOCKFILE=/tmp/cron_processor.lock
echo "$(date): Attempting to acquire lock at $LOCKFILE"
exec 200>$LOCKFILE
if flock -n 200; then
    echo "$(date): Lock acquired, running job."
else
    echo "$(date): Lock already held, exiting."
    exit 1
fi

# Set the working directory to the script location
cd "$(dirname "$0")"

source venv/bin/activate
# Load environment variables if .env file exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Create temp directory if it doesn't exist
mkdir -p temp

# Run the cron processor
echo "$(date): Starting video submission processing cron job"

python3 cron_processor.py

# Check exit status
if [ $? -eq 0 ]; then
    echo "$(date): Cron job completed successfully"
else
    echo "$(date): Cron job failed with exit code $?"
    exit 1
fi 