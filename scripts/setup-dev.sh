#!/usr/bin/env bash
# Development setup script
set -euo pipefail

echo "Setting up AI Platform development environment..."

python -m venv .venv
source .venv/bin/activate 2>/dev/null || .venv/Scripts/activate

pip install --upgrade pip
pip install -e "packages/protocol[dev]" -e "packages/shared[dev]" -e "services/ai-api[dev]"

npm install

echo "Done. Copy .env.example to .env and run: make docker-up && make test"
