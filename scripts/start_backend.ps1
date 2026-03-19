Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Import-EnvFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        $parts = $line -split "=", 2
        if ($parts.Count -ne 2) {
            return
        }

        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim("'`"")
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Import-EnvFile -Path (Join-Path $RootDir ".env")

Set-Location (Join-Path $RootDir "backend")

if (-not (Test-Path -LiteralPath ".venv")) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw "Python was not found. Install Python 3.12+ and ensure 'py' or 'python' is on PATH."
    }
}

$VenvPython = (Resolve-Path ".venv\Scripts\python.exe").Path

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements.txt

if (-not $env:DUCKDB_PATH) {
    $env:DUCKDB_PATH = Join-Path $RootDir "data\ttc.duckdb"
}
if (-not [System.IO.Path]::IsPathRooted($env:DUCKDB_PATH)) {
    $env:DUCKDB_PATH = Join-Path $RootDir $env:DUCKDB_PATH
}
if (-not $env:BACKEND_HOST) {
    $env:BACKEND_HOST = "0.0.0.0"
}
if (-not $env:BACKEND_PORT) {
    $env:BACKEND_PORT = "8000"
}

& $VenvPython -m uvicorn app.main:app --reload --host $env:BACKEND_HOST --port $env:BACKEND_PORT
