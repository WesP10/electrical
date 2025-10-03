#!/usr/bin/env powershell
<#
.SYNOPSIS
    PowerShell launcher for the Cornell Hyperloop GUI with centralized Python cache.

.DESCRIPTION
    This script sets up a centralized __pycache__ directory and launches the Python application
    with proper environment configuration. This ensures all Python bytecode files are stored
    in a single location rather than scattered throughout the project.

.PARAMETER Mock
    Use mock communication for development/testing

.PARAMETER NoDebug
    Disable debug mode

.PARAMETER ServerHost
    Host to bind to (default: 127.0.0.1)

.PARAMETER Port
    Port to bind to (default: 8050)

.PARAMETER Test
    Run tests instead of application

.PARAMETER Help
    Show help information

.EXAMPLE
    .\run.ps1 -Mock
    Launch with mock communication

.EXAMPLE
    .\run.ps1 -NoDebug -Port 3000
    Launch without debug on port 3000
#>

param(
    [switch]$Mock,
    [switch]$NoDebug,
    [string]$ServerHost = "127.0.0.1",
    [int]$Port = 8050,
    [switch]$Test,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

# Get the directory where this script is located (config) and go up to GUI root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$GuiRoot = Split-Path -Parent $ScriptDir
$CacheDir = Join-Path $GuiRoot "__pycache__"

# Ensure cache directory exists
if (-not (Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
    Write-Host "Created centralized cache directory: $CacheDir" -ForegroundColor Green
}

# Set environment variables for centralized cache
$env:PYTHONPYCACHEPREFIX = $CacheDir
$env:PYTHONDONTWRITEBYTECODE = $null  # Ensure bytecode writing is enabled

# Build Python command arguments
$PythonArgs = @("src/app.py")

if ($Mock) { $PythonArgs += "--mock" }
if ($NoDebug) { $PythonArgs += "--no-debug" }
if ($ServerHost -ne "127.0.0.1") { $PythonArgs += "--host", $ServerHost }
if ($Port -ne 8050) { $PythonArgs += "--port", $Port }
if ($Test) { $PythonArgs += "--test" }

# Display configuration
Write-Host "Cornell Hyperloop GUI Launcher" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Cache Directory: $CacheDir" -ForegroundColor Yellow
Write-Host "Python Args: $($PythonArgs -join ' ')" -ForegroundColor Yellow
Write-Host "PYTHONPYCACHEPREFIX: $env:PYTHONPYCACHEPREFIX" -ForegroundColor Yellow
Write-Host ""

# Change to GUI directory and launch Python
Push-Location $GuiRoot
try {
    # Launch Python with the configured environment
    & python @PythonArgs
    $ExitCode = $LASTEXITCODE
    
    if ($ExitCode -eq 0) {
        Write-Host "`nApplication completed successfully." -ForegroundColor Green
    } else {
        Write-Host "`nApplication exited with code: $ExitCode" -ForegroundColor Red
    }
    
    exit $ExitCode
} catch {
    Write-Error "Failed to launch application: $_"
    exit 1
} finally {
    Pop-Location
}