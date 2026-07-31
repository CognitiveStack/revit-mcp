# Revit MCP Recovery Runbook

## Purpose

Recovery procedure for the `revit-triviron` MCP integration when Claude Code
reports that the Revit MCP server has failed, disconnected, or timed out.

## Architecture

Claude Code runs in WSL and connects over HTTP/Tailscale to the FastMCP server
running on the Windows laptop.

FastMCP communicates locally with the pyRevit Routes API running inside Revit.

Claude Code / laptop-wsl
        |
        | MCP Streamable HTTP over Tailscale
        v
Windows FastMCP
port 8000
        |
        | HTTP localhost
        v
pyRevit Routes
port 48884
        |
        v
Autodesk Revit

## Important distinction

There are two independent services:

- Port 48884 — pyRevit Routes / Revit bridge
- Port 8000 — FastMCP / Claude-facing MCP server

Stopping FastMCP with Ctrl+C does not stop the pyRevit Routes service.

---

## Step 1 — Verify Revit / pyRevit

Ensure Revit is running and the required model is open.

From Windows PowerShell:

```powershell
curl.exe -i http://localhost:48884/revit_mcp/status/
