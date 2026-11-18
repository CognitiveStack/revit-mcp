Revit MCP Recovery Runbook

Purpose

Recovery procedure for the revit-triviron MCP integration when Claude Codereports that the Revit MCP server has failed, disconnected, or timed out.

This runbook documents the validated Windows + WSL deployment used for theTriviron Revit MCP.

Architecture

Claude Code runs in WSL and connects over MCP Streamable HTTP throughTailscale to the FastMCP server running on the Windows laptop.

FastMCP then communicates locally with the pyRevit Routes API running insideAutodesk Revit.

Claude Code / laptop-wsl
100.96.97.18
        |
        | MCP Streamable HTTP over Tailscale
        v
Windows laptop
FastMCP / Uvicorn
port 8000
        |
        | HTTP localhost
        v
pyRevit Routes
port 48884 (or 48885, 48886, ... — see below)
        |
        v
Autodesk Revit

Known Tailscale endpoints

Windows laptop:

laptop.tailfd6deb.ts.net
100.65.78.118

WSL:

laptop-wsl
100.96.97.18

Claude Code currently connects to:

http://100.65.78.118:8000/mcp

The MagicDNS equivalent is:

http://laptop.tailfd6deb.ts.net:8000/mcp

Important distinction

There are two independent services.

Port 48884 — Revit / pyRevit bridge

This is provided by pyRevit Routes inside the Windows Revit environment.

Health endpoint:

http://localhost:48884/revit_mcp/status/

pyRevit gives the first Revit session port 48884 and each extra session the
next port: 48885, 48886, and so on. If a second Revit is open, or an earlier
Revit session did not shut down cleanly, the model you want may be on 48885.

FastMCP finds the port by itself: it tries 48884-48889, uses the first one
whose /revit_mcp/status/ answers, and looks again whenever Revit stops
answering. It can therefore start before Revit is open.

To pin one port instead, set the REVIT_PORT environment variable before
starting FastMCP, for example:

$env:REVIT_PORT = "48885"

or set $RevitPort in scripts\start-revit-mcp.ps1.

Port 8000 — Claude-facing FastMCP server

This starts automatically at Windows sign-in through the scheduled task
described in the next section.

Stopping FastMCP stops port 8000 but does not stop Revit or the pyRevit
Routes service.

Automatic startup — scheduled task

Windows Task Scheduler task:

CogStack - Revit MCP Server

Trigger: at sign-in of LAPTOP\charles (not on wake from sleep or unlock).

It runs:

C:\Users\charles\Documents\Autodesk\MCP_Repos\start-revit-mcp.ps1

which calls the version-controlled script in this repository:

scripts\start-revit-mcp.ps1

That script runs uv run python main.py --http in a minimized window titled
"Revit MCP Server :8000". It keeps the server healthy:

- If the server stops or crashes, it restarts it after 10 seconds.
- Every 30 seconds it sends the server a real MCP request. After 3 failures
  in a row (a server that is running but stuck), it restarts it.
- Server output goes to logs\server-<time>.out.log and .err.log in this
  repository; logs older than 14 days are deleted. Read the .err.log for
  tracebacks.

Closing the window stops it for good, until the task is
started again.

How to check it is running

Task Manager → Processes → Apps: "Windows PowerShell". Expand it to see the
window "Revit MCP Server :8000". (Details tab: powershell.exe, uv.exe,
python.exe.)

Task Scheduler → Task Scheduler Library → "CogStack - Revit MCP Server":
Status should be Running.

From PowerShell:

(Get-ScheduledTask -TaskName "CogStack - Revit MCP Server").State
Test-NetConnection localhost -Port 8000 | Select-Object TcpTestSucceeded

To start it without signing out and in again:

Start-ScheduledTask -TaskName "CogStack - Revit MCP Server"

Do not start it while a manually started server is running: both would try
to use port 8000.

Battery settings

By default, Task Scheduler does not start the task on battery power and stops
it when the laptop switches to battery. To let it run on battery, run this in
an Administrator PowerShell (the task runs with highest privileges, so
changing it needs elevation):

$t = Get-ScheduledTask -TaskName "CogStack - Revit MCP Server"
$t.Settings.DisallowStartIfOnBatteries = $false
$t.Settings.StopIfGoingOnBatteries = $false
Set-ScheduledTask -InputObject $t

Do not run uv from WSL in this repository

The repository lives on the Windows drive, so WSL and Windows share its .venv
folder. Running uv run or uv sync from WSL replaces the Windows .venv with a
Linux one, and Windows uv then fails with:

error: failed to remove file `...\.venv\lib64`: Access is denied. (os error 5)

To recover, delete .venv from WSL (rm .venv/lib64, then remove the folder)
and let Windows uv rebuild it on the next start.

Step 1 — Ensure Revit is running

Open Autodesk Revit and ensure the required model is open.

For the Harrismith training project, the observed model during validation was:

HFS-ARC

The particular project/model may differ during future use.

Step 2 — Verify Revit / pyRevit Routes

From Windows PowerShell:

curl.exe -i http://localhost:48884/revit_mcp/status/

Expected:

HTTP/1.0 200 OK

with a response containing values equivalent to:

{
  "api_name": "revit_mcp",
  "health": "healthy",
  "revit_available": true,
  "document_title": "HFS-ARC",
  "status": "active"
}

The exact document_title depends on the model currently open in Revit.

If port 48884 fails

Try the next ports first:

curl.exe -i http://localhost:48885/revit_mcp/status/

A healthy answer there means Revit is on 48885. FastMCP will find it by
itself; no change is needed.

If no port answers, troubleshoot the Revit / pyRevit layer before continuing.

FastMCP cannot successfully control Revit if the pyRevit Routes API isunavailable.

Step 3 — Start or restart FastMCP

Normally FastMCP is already running from the scheduled task (see "How to
check it is running"). If it is not, start the task:

Start-ScheduledTask -TaskName "CogStack - Revit MCP Server"

To run it by hand instead, for example to watch the output, open Windows
PowerShell.

Change to the repository:

cd C:\Users\charles\Documents\Autodesk\MCP_Repos\revit-mcp-triviron

Start the FastMCP HTTP server:

uv run python main.py --http

Expected output includes:

Started server process [...]
Waiting for application startup.
Application startup complete.
Uvicorn running on http://0.0.0.0:8000

Leave this PowerShell process running while the MCP is required.

Important

Pressing:

Ctrl+C

terminates FastMCP.

After that:

port 48884 may still be healthy
port 8000 will be unavailable
Claude Code will lose revit-triviron connectivity

Restart with:

uv run python main.py --http

or start the scheduled task again.

Step 4 — Verify FastMCP from WSL

From WSL:

curl -i --max-time 5 \
  http://laptop.tailfd6deb.ts.net:8000/mcp

A result such as:

HTTP/1.1 406 Not Acceptable

with:

Client must accept text/event-stream

is acceptable for this raw curl test.

The 406 does not mean the server is broken.

It proves that:

MagicDNS resolved the Windows machine;

Tailscale connectivity works;

Windows port 8000 is reachable;

Uvicorn / FastMCP is running;

the plain curl request is simply not a complete MCP Streamable HTTP client.

The numeric Tailscale address can also be tested:

curl -i --max-time 5 \
  http://100.65.78.118:8000/mcp

Failure interpretation

If this produces:

connection refused

or:

timeout

then FastMCP is not running or the network path is unavailable.

Step 5 — Reconnect Claude Code

In Claude Code:

/mcp

Select:

revit-triviron

then choose:

Reconnect

Expected:

revit-triviron · connected · 14 tools

Normal recovery does not require selecting Authenticate.

The browser authentication option shown by Claude Code is generic behaviourfor HTTP MCP connections and is not part of the normal localrevit-triviron recovery procedure.

Step 6 — End-to-end verification

After reconnecting, use read-only MCP tools.

Recommended:

get_revit_status
get_revit_model_info

Confirm that:

API = revit_mcp;

health = healthy;

status = active;

Revit available = true;

the expected current Revit document is returned.

Do not use a modifying MCP tool merely to test connectivity.

A successful test validates the complete chain:

Claude Code
        |
        v
FastMCP :8000
        |
        v
pyRevit Routes :48884
        |
        v
Revit API
        |
        v
current Revit model

Fast diagnosis

Scenario A — Port 48884 healthy, port 8000 unavailable

Test the Revit / pyRevit side:

curl.exe -i http://localhost:48884/revit_mcp/status/

If that succeeds, but this WSL test fails:

curl -i --max-time 5 \
  http://laptop.tailfd6deb.ts.net:8000/mcp

then:

Revit / pyRevit is healthy
FastMCP is not running

Start FastMCP:

Start-ScheduledTask -TaskName "CogStack - Revit MCP Server"

or by hand:

cd C:\Users\charles\Documents\Autodesk\MCP_Repos\revit-mcp-triviron
uv run python main.py --http

Scenario B — Port 48884 unavailable

Check 48885 and up first: Revit may be on another port (see "Port 48884 —
Revit / pyRevit bridge"). If none answer, the problem is below FastMCP.

Check:

Revit running?
pyRevit loaded?
revit-mcp-python extension loaded?
pyRevit Routes service active?

Restore the Revit / pyRevit layer before troubleshooting Claude Code.

Scenario C — Port 8000 reachable but Claude Code shows disconnected

In Claude Code:

/mcp
→ revit-triviron
→ Reconnect

Then run:

get_revit_status

Scenario D — Both services are healthy but one MCP tool fails

First verify:

get_revit_status

If status works, the general MCP transport is healthy.

Investigate the specific MCP tool and its corresponding Revit-side routeinstead of restarting the entire stack immediately.

Scenario E — Port 8000 answers, but Claude Code gets HTTP 500

Symptom in Claude Code:

Failed to reconnect to revit-triviron: HTTP 500

and every MCP request to port 8000 returns "Internal Server Error", while the
server process is still running.

Cause (seen 2026-11-19 with mcp 1.9.0): in mcp versions before about 1.10,
one failed request in stateless HTTP mode, for example a client dropping
its connection mid-request, cancels the task group shared by all requests.
The process stays up but every later request fails. Upgraded to mcp 1.30.0,
which catches and logs such errors instead.

The startup script's health check restarts a stuck server within about
90 seconds. To restart it at once, close the "Revit MCP Server :8000" window
and run:

Start-ScheduledTask -TaskName "CogStack - Revit MCP Server"

Endpoint path

Since mcp 1.30.0 the endpoint is /mcp (no trailing slash). /mcp/ still
works through a 307 redirect, but clients should use /mcp.

Network binding requirement

FastMCP is configured in main.py to listen on:

host="0.0.0.0"

This is required for the current deployment because Claude Code runs on theseparate laptop-wsl Tailscale node and connects to the FastMCP service onthe Windows laptop.

Using:

host="127.0.0.1"

would restrict FastMCP to Windows loopback and prevent the WSL/Tailscale MCPclient from reaching port 8000.

The network binding fix was recorded in Git as:

9d2ef5e fix: expose Revit MCP server to network clients

Validated recovery example

During the validated recovery, the Revit-side health check returned:

{
  "api_name": "revit_mcp",
  "health": "healthy",
  "revit_available": true,
  "document_title": "HFS-ARC",
  "status": "active"
}

FastMCP was then started from Windows PowerShell:

uv run python main.py --http

with:

Uvicorn running on http://0.0.0.0:8000

A request from laptop-wsl reached the Windows FastMCP server:

100.96.97.18 - "GET /mcp/ HTTP/1.1" 406 Not Acceptable

The 406 was expected for the raw curl request.

Claude Code then showed:

revit-triviron · connected · 14 tools

and the read-only tools:

get_revit_status
get_revit_model_info

successfully returned the active Revit model HFS-ARC.

This validated the complete deployment path:

Claude Code / laptop-wsl
        |
        | Tailscale
        v
Windows FastMCP :8000
        |
        | localhost
        v
pyRevit Routes :48884
        |
        v
Revit / HFS-ARC

Recovery checklist

[ ] Revit running
[ ] Correct Revit model open
[ ] pyRevit Routes :48884 (or :48885+) returns HTTP 200
[ ] FastMCP running (scheduled task "CogStack - Revit MCP Server", or `uv run python main.py --http`)
[ ] Uvicorn listening on 0.0.0.0:8000
[ ] WSL can reach Windows :8000
[ ] Claude Code shows revit-triviron connected
[ ] get_revit_status succeeds
[ ] get_revit_model_info succeeds

When all checks pass, revit-triviron is operational.

Repository

Local Windows repository:

C:\Users\charles\Documents\Autodesk\MCP_Repos\revit-mcp-triviron

GitHub repository:

CognitiveStack/revit-mcp

Current Git remote:

https://github.com/CognitiveStack/revit-mcp.git

The local repository folder and Claude MCP name retain the historicalrevit-mcp-triviron name even though the GitHub repository is nowCognitiveStack/revit-mcp.

Future improvements

FastMCP now starts automatically at sign-in, restarts itself if it stops or
gets stuck, logs to logs\, and finds the Revit port by itself (validated
2026-11-19 with Revit on port 48885 and HFS-ARC open).

The task starts only at sign-in. If the window is closed, FastMCP stays off
until the task is started again or the next sign-in.

A possible improvement is changing the Claude Code MCP endpoint fromthe numeric Tailscale IP:

http://100.65.78.118:8000/mcp

to the MagicDNS endpoint:

http://laptop.tailfd6deb.ts.net:8000/mcp

Both were successfully tested during recovery.
