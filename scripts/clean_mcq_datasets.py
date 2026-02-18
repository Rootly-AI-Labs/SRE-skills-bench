#!/usr/bin/env python3
"""Download MCQ datasets from HuggingFace, remove questions with duplicate identical choices,
and save cleaned versions locally as JSON files."""

import json
import os
from datasets import load_dataset

DATASETS = {
    "s3-security-mcq": "rootly-ai-labs/terraform-s3-security-mcq",
    "azure-network-mcq": "rootly-ai-labs/terraform-azure-network-mcq",
    "azure-compute-mcq": "rootly-ai-labs/terraform-azure-compute-mcq",
    "azure-k8s-mcq": "rootly-ai-labs/terraform-azure-k8s-mcq",
    "gcp-network-mcq": "rootly-ai-labs/terraform-gcp-network-mcq",
    "gcp-compute-mcq": "rootly-ai-labs/terraform-gcp-compute-mcq",
    "gcp-storage-mcq": "rootly-ai-labs/terraform-gcp-storage-mcq",
    "vpc-nat-mcq": "rootly-ai-labs/terraform-vpc-nat-mcq",
    "iam-mcq": "rootly-ai-labs/terraform-iam-tf-mcq",
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "mcq_cleaned")


def extract_choices(content):
    """Parse choice texts from the user message content."""
    choices = {}
    for letter in ["A", "B", "C", "D"]:
        pattern = f"Choice {letter}:\n"
        start = content.find(pattern)
        if start == -1:
            continue
        start += len(pattern)
        end = len(content)
        for next_letter in ["B", "C", "D"]:
            if next_letter <= letter:
                continue
            next_start = content.find(f"Choice {next_letter}:\n", start)
            if next_start != -1 and next_start < end:
                end = next_start
        choices[letter] = content[start:end].strip()
    return choices


def is_valid_sample(record):
    """Return True if the sample has 4 distinct choices."""
    content = record["input"][1]["content"]
    choices = extract_choices(content)
    if len(choices) < 4:
        return False
    vals = list(choices.values())
    if len(vals) != len(set(vals)):
        return False
    return True


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for name, hf_path in DATASETS.items():
        ds = load_dataset(hf_path, split="test")
        original_count = len(ds)

        clean_records = [r for r in ds if is_valid_sample(r)]
        removed = original_count - len(clean_records)

        output_path = os.path.join(OUTPUT_DIR, f"{name}.json")
        with open(output_path, "w") as f:
            json.dump(clean_records, f)

        print(f"{name}: {original_count} -> {len(clean_records)} ({removed} removed)")

    print(f"\nCleaned datasets saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
