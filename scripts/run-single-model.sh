#!/bin/bash
# Run all cleaned MCQ subtasks for a single model and output results
# Usage: ./run-single-model.sh <model_id> <short_name>

set -a
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"
set +a

MODEL="$1"
SHORT_NAME="$2"
RESULT_DIR="logs/${SHORT_NAME}"
mkdir -p "$RESULT_DIR"

SUBTASKS="s3-security-mcq azure-network-mcq azure-compute-mcq azure-k8s-mcq gcp-network-mcq gcp-compute-mcq gcp-storage-mcq vpc-nat-mcq iam-mcq"
RESULTS_FILE="$RESULT_DIR/results.txt"
> "$RESULTS_FILE"

extract_accuracy() {
    local log_file=$1
    python3 -c "
import json, sys
with open('$log_file') as f:
    data = json.load(f)
scores = data.get('results',{}).get('scores',[])
if scores:
    acc = scores[0].get('metrics',{}).get('accuracy',{}).get('value')
    if acc is not None:
        print(round(acc * 100, 1))
        sys.exit(0)
sys.exit(1)
" 2>/dev/null
}

echo "=== Starting benchmark for $SHORT_NAME ($MODEL) ==="

for subtask in $SUBTASKS; do
    logfile="$RESULT_DIR/${subtask}.json"
    echo "[$SHORT_NAME] Running: $subtask"
    uv run openbench eval "$SCRIPT_DIR/../evals/rootly_terraform_clean" \
        --model "$MODEL" \
        --reasoning-effort "high" \
        --max-connections 3 \
        --max-subprocesses 3 \
        --timeout 180 \
        --logfile "$logfile" \
        --log-format json \
        -T subtask="$subtask" 2>&1

    if [ -f "$logfile" ]; then
        acc=$(extract_accuracy "$logfile")
        echo "$subtask:${acc:-ERROR}" >> "$RESULTS_FILE"
        echo "[$SHORT_NAME] $subtask: ${acc:-ERROR}"
    else
        echo "$subtask:ERROR" >> "$RESULTS_FILE"
        echo "[$SHORT_NAME] $subtask: ERROR"
    fi
done

# Run rootly_gmcq standalone
logfile="$RESULT_DIR/rootly_gmcq.json"
echo "[$SHORT_NAME] Running: rootly_gmcq"
uv run openbench eval "rootly_gmcq" \
    --model "$MODEL" \
    --reasoning-effort "high" \
    --max-connections 5 \
    --timeout 180 \
    --max-tokens 1 \
    --logfile "$logfile" \
    --log-format json 2>&1

if [ -f "$logfile" ]; then
    acc=$(extract_accuracy "$logfile")
    echo "rootly_gmcq:${acc:-ERROR}" >> "$RESULTS_FILE"
    echo "[$SHORT_NAME] rootly_gmcq: ${acc:-ERROR}"
else
    echo "rootly_gmcq:ERROR" >> "$RESULTS_FILE"
    echo "[$SHORT_NAME] rootly_gmcq: ERROR"
fi

echo ""
echo "=== $SHORT_NAME COMPLETE ==="
cat "$RESULTS_FILE"
