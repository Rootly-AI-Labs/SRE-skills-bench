"""
Rootly Terraform MCQ - Cleaned datasets (duplicate-choice questions removed).

Usage:
  uv run openbench eval ./evals/rootly_terraform_clean --model "anthropic/claude-opus-4-6" -T subtask=iam-mcq
"""

import os
from typing import Optional
from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig
from openbench.utils.mcq import MCQEval
from openbench.datasets.rootly_terraform import record_to_mcq_sample

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "mcq_cleaned")

SUBTASKS = [
    "s3-security-mcq",
    "azure-network-mcq",
    "azure-compute-mcq",
    "azure-k8s-mcq",
    "gcp-network-mcq",
    "gcp-compute-mcq",
    "gcp-storage-mcq",
    "vpc-nat-mcq",
    "iam-mcq",
]


@task
def rootly_terraform_clean(subtask: Optional[str] = None) -> Task:
    """Rootly Terraform MCQ evaluation using cleaned datasets."""
    if subtask is None:
        subtask = "azure-k8s-mcq"

    if subtask not in SUBTASKS:
        valid = ", ".join(SUBTASKS)
        raise ValueError(f"Unknown subtask: {subtask}. Valid subtasks are: {valid}")

    json_path = os.path.join(DATASETS_DIR, f"{subtask}.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Cleaned dataset not found at {json_path}. Run scripts/clean_mcq_datasets.py first."
        )

    return MCQEval(
        name="rootly_terraform_clean",
        dataset_type="json",
        dataset_path=json_path,
        record_to_mcq_sample=record_to_mcq_sample,
        auto_id=True,
        config=GenerateConfig(),
    )
