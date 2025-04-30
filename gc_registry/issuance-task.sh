#!/bin/bash
set -e

# Print diagnostic information
echo "======================= STARTING CERTIFICATE ISSUANCE TASK ======================="
echo "Current date: $(date)"
echo "Working directory: $(pwd)"
echo "Current user: $(whoami)"

# Navigate to code directory
echo "======================= CHANGING TO CODE DIRECTORY ======================="
cd /code
echo "Working directory after cd: $(pwd)"
echo "Directory contents:"
ls -la

# Create log directory
echo "======================= SETTING UP LOG DIRECTORY ======================="
mkdir -p /code/logs
echo "Log directory created at /code/logs"

# Run the actual task
echo "======================= RUNNING CERTIFICATE ISSUANCE TASK ======================="
/usr/local/bin/poetry run python gc_registry/certificate/issuance_task.py

# Check exit code
EXIT_CODE=$?
echo "======================= TASK COMPLETED ======================="
echo "Exit code: $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "Task failed with error code: $EXIT_CODE"
  exit $EXIT_CODE
fi

echo "Task completed successfully!"
echo "======================= END OF SCRIPT ======================="