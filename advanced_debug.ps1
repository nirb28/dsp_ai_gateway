# PowerShell script for advanced debugging of the DSP AI Gateway
# This script provides multiple debugging options for the FastAPI application

# Activate the virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1

# Set environment variables for debugging
$env:PYTHONPATH = (Get-Location).Path
$env:LOG_LEVEL = "DEBUG"

# Parse command line arguments
param(
    [switch]$pdb,
    [switch]$verbose,
    [switch]$trace_all,
    [int]$port = 8000
)

# Configure logging level based on verbosity
if ($verbose) {
    $logLevel = "debug"
} else {
    $logLevel = "info"
}

# Run with PDB if requested
if ($pdb) {
    Write-Host "Starting API gateway with PDB debugging enabled..."
    python -c "import pdb; pdb.set_trace(); import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=$port, reload=True, log_level='$logLevel')"
} elseif ($trace_all) {
    # Run with extensive tracing for all requests
    Write-Host "Starting API gateway with full request/response tracing..."
    $env:TRACE_ALL_REQUESTS = "True"
    python -m uvicorn app.main:app --host 0.0.0.0 --port $port --reload --log-level $logLevel
} else {
    # Standard debug mode
    Write-Host "Starting API gateway in debug mode..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port $port --reload --log-level $logLevel
}
