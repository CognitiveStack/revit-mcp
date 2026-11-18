# Starts the CogStack Revit MCP server (FastMCP, port 8000) and keeps it healthy.
# Run at sign-in by the "CogStack - Revit MCP Server" scheduled task; see
# docs/REVIT_MCP_RECOVERY_RUNBOOK.md.
#
# - Restarts the server 10 seconds after it stops.
# - Every 30 seconds sends it a real MCP request; after 3 failures in a row
#   (a server that is running but stuck) it restarts it.
# - Server output goes to logs\server-<time>.out.log and .err.log; logs older
#   than 14 days are deleted.
#
# Revit's pyRevit Routes port (48884, 48885, ...) is found automatically.
# To pin one port instead, set it here, for example: $RevitPort = "48885"
$RevitPort = ""

$RepoDir = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $RepoDir "logs"
$HealthUrl = "http://127.0.0.1:8000/mcp"
$CheckSeconds = 30
$MaxFailures = 3
$StartupGraceSeconds = 120

$Uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $Uv) { $Uv = Join-Path $env:USERPROFILE "scoop\shims\uv.exe" }
if ($RevitPort) { $env:REVIT_PORT = $RevitPort }
$env:PYTHONUNBUFFERED = "1"
$PortText = if ($env:REVIT_PORT) { "pinned to $($env:REVIT_PORT)" } else { "auto-detect (48884-48889)" }

$host.UI.RawUI.WindowTitle = "Revit MCP Server :8000"
Set-Location $RepoDir
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Status($Message, $Color = "Gray") {
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Message" -ForegroundColor $Color
}

function Test-McpHealthy {
    $body = '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"watchdog","version":"1"}}}'
    try {
        $r = Invoke-WebRequest -Uri $HealthUrl -Method Post -Body $body -ContentType "application/json" `
            -Headers @{ Accept = "application/json, text/event-stream" } -UseBasicParsing -TimeoutSec 10
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

Write-Host "CogStack Revit MCP Server" -ForegroundColor Cyan
Write-Host "MCP port: 8000 | pyRevit Routes: $PortText | logs: $LogDir" -ForegroundColor Gray
Write-Host "To stop it for good, close this window.`n" -ForegroundColor Gray

while ($true) {
    Get-ChildItem $LogDir -Filter "server-*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } | Remove-Item -ErrorAction SilentlyContinue

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $out = Join-Path $LogDir "server-$stamp.out.log"
    $err = Join-Path $LogDir "server-$stamp.err.log"
    Write-Status "Starting server (log: logs\server-$stamp.err.log)" Cyan
    $p = Start-Process -FilePath $Uv -ArgumentList "run", "python", "main.py", "--http" -WorkingDirectory $RepoDir `
        -NoNewWindow -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    $null = $p.Handle  # keep a handle so ExitCode is available later

    $started = Get-Date
    $healthy = $false
    $failures = 0
    while (-not $p.HasExited) {
        Start-Sleep -Seconds $CheckSeconds
        if ($p.HasExited) { break }
        if (Test-McpHealthy) {
            if (-not $healthy -or $failures -gt 0) { Write-Status "Server is answering on port 8000" Green }
            $healthy = $true
            $failures = 0
        } elseif ($healthy -or ((Get-Date) - $started).TotalSeconds -gt $StartupGraceSeconds) {
            $failures++
            Write-Status "Health check failed ($failures of $MaxFailures)" Yellow
            if ($failures -ge $MaxFailures) {
                Write-Status "Server is not answering - restarting it" Red
                taskkill.exe /PID $p.Id /T /F | Out-Null
                break
            }
        }
    }

    $p.WaitForExit()
    Write-Status "Server stopped (exit code $($p.ExitCode)). Restarting in 10 seconds..." Yellow
    Start-Sleep -Seconds 10
}
