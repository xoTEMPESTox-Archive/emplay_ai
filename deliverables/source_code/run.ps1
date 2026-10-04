# ==============================================================================
# RFP Intelligence Platform — One-Click Setup & Launch Script (Windows PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  RFP Intelligence Platform — Initializing Windows Environment   " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Locate or create Python virtual environment
$VenvDir = Join-Path $PSScriptRoot ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "[+] Creating Python virtual environment in $VenvDir..." -ForegroundColor Yellow
    python -m venv $VenvDir
} else {
    Write-Host "[✓] Existing virtual environment found: $VenvDir" -ForegroundColor Green
}

# 2. Verify or install dependencies
Write-Host "[+] Checking dependencies..." -ForegroundColor Yellow
$Installed = & $PythonExe -c "import rfp_intelligence, streamlit; print('OK')" 2>$null
if ($Installed -ne "OK") {
    Write-Host "[+] Installing dependencies into virtual environment..." -ForegroundColor Yellow
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -e .
    & $PythonExe -m pip install streamlit
} else {
    Write-Host "[✓] Dependencies already installed. Skipping package installation." -ForegroundColor Green
}

# 3. Create .env if missing
$EnvFile = Join-Path $PSScriptRoot ".env"
$EnvExample = Join-Path $PSScriptRoot ".env.example"
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Write-Host "[+] Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item $EnvExample $EnvFile
    }
}

# 4. Start FastAPI Backend as background job
Write-Host "[+] Starting FastAPI Backend on port 8000..." -ForegroundColor Cyan
$BackendJob = Start-Job -ScriptBlock {
    param($py)
    & $py -m rfp_intelligence.cli serve --host 127.0.0.1 --port 8000
} -ArgumentList $PythonExe

Start-Sleep -Seconds 2

# 5. Start Streamlit Web UI as background job
Write-Host "[+] Starting Streamlit Web UI on port 8501..." -ForegroundColor Cyan
$FrontendJob = Start-Job -ScriptBlock {
    param($py, $dir)
    Set-Location $dir
    & $py -m streamlit run web_ui.py --server.port 8501 --server.address 127.0.0.1 --server.headless false
} -ArgumentList $PythonExe, $PSScriptRoot

Start-Sleep -Seconds 2

# 6. Display Endpoints
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  🚀 All Services Running Successfully!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  💬 Streamlit Web UI:    http://localhost:8501" -ForegroundColor White
Write-Host "  📡 REST API Health:     http://localhost:8000/health" -ForegroundColor White
Write-Host "  📖 Swagger API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  Press Ctrl+C in this window to stop both servers." -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Green

# Open browser
Start-Process "http://localhost:8501"

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`n[*] Stopping background jobs..." -ForegroundColor Yellow
    Stop-Job $BackendJob -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue
    Stop-Job $FrontendJob -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue
    Write-Host "[✓] Services stopped cleanly." -ForegroundColor Green
}
