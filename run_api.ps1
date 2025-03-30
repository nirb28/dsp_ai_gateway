# PowerShell script to run the API gateway using the embedded virtual environment

# Activate the virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1

# Run the API gateway
Write-Host "Starting API gateway..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
