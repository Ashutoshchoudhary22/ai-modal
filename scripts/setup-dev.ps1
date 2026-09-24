# PowerShell development setup script
$ErrorActionPreference = "Stop"

Write-Host "Setting up AI Platform development environment..."

python -m venv .venv
& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e "packages/protocol[dev]" -e "packages/shared[dev]" -e "services/ai-api[dev]"

npm install

Write-Host "Done. Copy .env.example to .env and run: make docker-up; make test"
