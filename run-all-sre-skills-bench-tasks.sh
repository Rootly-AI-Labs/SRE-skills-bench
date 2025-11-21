#!/bin/bash
# Script automating the execution of SRE-skills-bench accross its tasks for a specific model and output CSV format for easy import

export OPENAI_API_KEY=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
export OPENROUTER_API_KEY=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
export ANTHROPIC_API_KEY=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

# Configuration
MODEL="openrouter/anthropic/claude-sonnet-4.5"
CSV_FILE="results_$(date +%Y%m%d_%H%M%S).csv"
LOG_DIR="logs"

# SRE-skills-tasks
SUBTASKS="s3-security-mcq azure-network-mcq azure-compute-mcq azure-k8s-mcq gcp-network-mcq gcp-compute-mcq gcp-storage-mcq vpc-nat-mcq iam-mcq"

# Temporary file to store results
TEMP_RESULTS="/tmp/eval_results_$$.txt"
> "$TEMP_RESULTS"

# Extract accuracy from JSON log file
extract_accuracy_from_log() {
    local log_file=$
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
# Data row: model name + accuracy scores
printf "%s" "$MODEL" > "$CSV_FILE"
for subtask in $SUBTASKS; do
    # Extract accuracy for this subtask from temp file
    accuracy=$(grep "^$subtask:" "$TEMP_RESULTS" | cut -d: -f2)
    printf ",%s" "$accuracy" >> "$CSV_FILE"
done
printf "\n" >> "$CSV_FILE"

# Clean up temp files
rm -f "$TEMP_RESULTS"
rm -f /tmp/timestamp_$$

# Display summary
echo ""
echo "======================================"
echo "EVALUATION COMPLETE"
echo "======================================"
echo "Results saved to: $CSV_FILE"
echo ""
echo "CSV Contents:"
cat "$CSV_FILE"
