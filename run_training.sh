#!/bin/bash
# run_training.sh - Entrypoint for Hugging Face Jobs

echo "[run_training.sh] Setting up environment..."
export PYTHONPATH=$PYTHONPATH:.

echo "[run_training.sh] Launching training module..."
# We use 'python -m' to ensure the 'training' package is recognized correctly
uv run python -m training.train_grpo "$@"
