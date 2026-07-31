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
port 48884
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

http://100.65.78.118:8000/mcp/

The MagicDNS equivalent is:

http://laptop.tailfd6deb.ts.net:8000/mcp/

Important distinction

There are two independent services.

Port 48884 — Revit / pyRevit bridge

This is provided by pyRevit Routes inside the Windows Revit environment.

Health endpoint:

http://localhost:48884/revit_mcp/status/

Port 8000 — Claude-facing FastMCP server

This is started separately from Windows PowerShell with:

uv run python main.py --http

Stopping FastMCP with Ctrl+C stops port 8000 but does not stop Revit orthe pyRevit Routes service on port 48884.

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

If the command gives a timeout or connection failure, troubleshoot theRevit / pyRevit layer before continuing.

FastMCP cannot successfully control Revit if the pyRevit Routes API isunavailable.

Step 3 — Start or restart FastMCP

Open Windows PowerShell.

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

Step 4 — Verify FastMCP from WSL

From WSL:

curl -i --max-time 5 \
  http://laptop.tailfd6deb.ts.net:8000/mcp/

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
  http://100.65.78.118:8000/mcp/

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
  http://laptop.tailfd6deb.ts.net:8000/mcp/

then:

Revit / pyRevit is healthy
FastMCP is not running

Start FastMCP:

cd C:\Users\charles\Documents\Autodesk\MCP_Repos\revit-mcp-triviron
uv run python main.py --http

Scenario B — Port 48884 unavailable

The problem is below FastMCP.

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
[ ] pyRevit Routes :48884 returns HTTP 200
[ ] FastMCP started with `uv run python main.py --http`
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

The FastMCP process currently requires manual startup from Windows PowerShell.

A future improvement may run FastMCP automatically using an appropriateWindows startup or service mechanism.

A second possible improvement is changing the Claude Code MCP endpoint fromthe numeric Tailscale IP:

http://100.65.78.118:8000/mcp/

to the MagicDNS endpoint:

http://laptop.tailfd6deb.ts.net:8000/mcp/

Both were successfully tested during recovery.

Do not introduce automatic startup or further deployment changes until thecurrent manual deployment and its failure behaviour have been deliberatelyreviewed.
