# Revit MCP Recovery Runbook

## Purpose

Recovery procedure for the `revit-triviron` MCP integration when Claude Code
reports that the Revit MCP server has failed, disconnected, or timed out.

This runbook documents the validated Windows + WSL deployment used for the
Triviron Revit MCP.

---

## Architecture

Claude Code runs in WSL and connects over MCP Streamable HTTP through
Tailscale to the FastMCP server running on the Windows laptop.

FastMCP then communicates locally with the pyRevit Routes API running inside
Autodesk Revit.

```text
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
