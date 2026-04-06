#!/bin/bash
set -e

mkdir -p /data/.hermes/sessions
mkdir -p /data/.hermes/skills
mkdir -p /data/.hermes/workspace
mkdir -p /data/.hermes/pairing

# Create config.yaml with model from env (gateway reads model ONLY from config.yaml)
MODEL="${LLM_MODEL:-${HERMES_MODEL:-anthropic/claude-opus-4.6}}"
echo "model: $MODEL" > /data/.hermes/config.yaml
echo "[start.sh] Created config.yaml with model=$MODEL"

exec python /app/server.py
