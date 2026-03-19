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

Set-Location (Join-Path $RootDir "frontend")

if (-not (Test-Path -LiteralPath "node_modules")) {
    npm install
}

if (-not $env:NEXT_PUBLIC_API_BASE_URL) {
    $env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
}
if (-not $env:FRONTEND_HOST) {
    $env:FRONTEND_HOST = "0.0.0.0"
}
if (-not $env:FRONTEND_PORT) {
    $env:FRONTEND_PORT = "3000"
}

npm run dev -- --hostname $env:FRONTEND_HOST --port $env:FRONTEND_PORT
