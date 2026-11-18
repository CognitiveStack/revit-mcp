# Starts the CogStack Revit MCP server (FastMCP, port 8000) and restarts it if it stops.
# Run at sign-in by the "CogStack - Revit MCP Server" scheduled task; see
# docs/REVIT_MCP_RECOVERY_RUNBOOK.md.
#
# Revit's pyRevit Routes port (48884, 48885, ...) is found automatically.
# To pin one port instead, set it here, for example: $RevitPort = "48885"
$RevitPort = ""

$RepoDir = Split-Path -Parent $PSScriptRoot
$Uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $Uv) { $Uv = Join-Path $env:USERPROFILE "scoop\shims\uv.exe" }
if ($RevitPort) { $env:REVIT_PORT = $RevitPort }
$PortText = if ($env:REVIT_PORT) { "pinned to $($env:REVIT_PORT)" } else { "auto-detect (48884-48889)" }

$host.UI.RawUI.WindowTitle = "Revit MCP Server :8000"
Set-Location $RepoDir

while ($true) {
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  Starting CogStack Revit MCP Server" -ForegroundColor Cyan
    Write-Host "MCP port: 8000 | pyRevit Routes: $PortText" -ForegroundColor Gray
    Write-Host "To stop it for good, close this window.`n" -ForegroundColor Gray

    & $Uv run python main.py --http

    Write-Host "`n$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  Server stopped (exit code $LASTEXITCODE). Restarting in 10 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}
