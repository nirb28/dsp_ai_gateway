# PowerShell script to debug the API gateway using the embedded virtual environment

# Activate the virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1

# Set environment variables for debugging
$env:LOG_LEVEL = "DEBUG"
$env:PYTHONPATH = (Get-Location).Path

# Run the API gateway in debug mode
Write-Host "Starting API gateway in debug mode..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
