#!/bin/bash
# Script automating the execution of SRE-skills-bench accross its tasks for a specific model and output CSV format for easy import

# Load API keys from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo "Error: .env file not found at $SCRIPT_DIR/.env"
    exit 1
fi

# Configuration
MODEL="openrouter/openai/gpt-5-mini"
CSV_FILE="results_$(date +%Y%m%d_%H%M%S).csv"
LOG_DIR="logs"

# SRE-skills-tasks
SUBTASKS="s3-security-mcq azure-network-mcq azure-compute-mcq azure-k8s-mcq gcp-network-mcq gcp-compute-mcq gcp-storage-mcq vpc-nat-mcq iam-mcq"

# Temporary file to store results
TEMP_RESULTS="/tmp/eval_results_$$.txt"
> "$TEMP_RESULTS"

# Extract accuracy from JSON log file
extract_accuracy_from_log() {
    local log_file=$1
    python3 -c "
import json
import sys
try:
    with open('$log_file', 'r') as f:
        data = json.load(f)
    results = data.get('results', {})
    scores = results.get('scores', [])
    if scores:
        metrics = scores[0].get('metrics', {})
        accuracy = metrics.get('accuracy', {}).get('value')
        if accuracy is not None:
            print(f'{accuracy:.2f}')
            sys.exit(0)
    sys.exit(1)
except:
    sys.exit(1)
"
}

# Function to run eval and capture accuracy
run_eval() {
    local subtask=$1
    local before_time=$(date +%s)

    echo "Running evaluation for: $subtask"
    echo ""

    # Run the evaluation with --log-format json (shows progress bars in real-time)
    uv run openbench eval rootly_terraform \
        --model "$MODEL" \
        --reasoning-effort "high" \
        --max-connections 35 \
        --log-format json \
        -T subtask="$subtask"

    # Find the most recent log file in logs/ directory
    local log_file=$(find "$LOG_DIR" -name "*.json" -newer /tmp/timestamp_$$ 2>/dev/null | sort -r | head -n1)

    if [ -z "$log_file" ]; then
        # Fallback: find the most recent JSON file
        log_file=$(ls -t "$LOG_DIR"/*.json 2>/dev/null | head -n1)
    fi

    # Extract accuracy from the log file
    if [ -n "$log_file" ] && [ -f "$log_file" ]; then
        accuracy=$(extract_accuracy_from_log "$log_file")
        if [ -n "$accuracy" ]; then
            echo "$subtask:$accuracy" >> "$TEMP_RESULTS"
            echo ""
            echo "✓ Captured accuracy for $subtask: $accuracy"
        else
            echo "$subtask:ERROR" >> "$TEMP_RESULTS"
            echo ""
            echo "✗ ERROR: Could not extract accuracy from log file"
        fi
    else
        echo "$subtask:ERROR" >> "$TEMP_RESULTS"
        echo ""
        echo "✗ ERROR: Could not find log file"
    fi
    echo ""
}

# Create timestamp file for finding new logs
touch /tmp/timestamp_$$

# Run evaluations for all subtasks
for subtask in $SUBTASKS; do
    run_eval "$subtask"
done

# Generate CSV file
# Data row: execution date + model name + accuracy scores
EXEC_DATE=$(date +%Y-%m-%d)
printf "%s,%s" "$EXEC_DATE" "$MODEL" > "$CSV_FILE"
for subtask in $SUBTASKS; do
    # Extract accuracy for this subtask from temp file
    accuracy=$(grep "^$subtask:" "$TEMP_RESULTS" | cut -d: -f2)
    printf ",%s" "$accuracy" >> "$CSV_FILE"
done
printf "\n" >> "$CSV_FILE"

# Display summary
echo ""
echo "======================================"
echo "EVALUATION COMPLETE"
echo "======================================"
echo ""
echo "Results:"
echo ""
for subtask in $SUBTASKS; do
    accuracy=$(grep "^$subtask:" "$TEMP_RESULTS" | cut -d: -f2)
    printf "%-25s: %s\n" "$subtask" "$accuracy"
done
echo ""
echo "--------------------------------------"
echo "Results saved to: $CSV_FILE"

# Clean up temp files
rm -f "$TEMP_RESULTS"
rm -f /tmp/timestamp_$$
