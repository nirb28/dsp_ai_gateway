# PowerShell script to run tests using the embedded virtual environment

# Activate the virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1

# Run the tests
Write-Host "Running tests..."
python -m pytest -v

# Display test summary
Write-Host "Test execution completed."
