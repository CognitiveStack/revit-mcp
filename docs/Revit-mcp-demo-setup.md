# Revit MCP Demo Setup Guide

> **Purpose**: Set up a local demo environment to showcase Claude Desktop controlling Autodesk Revit via MCP (Model Context Protocol) for Triviron Holdings presentation.
> 
> **Author**: Charles  
> **Organization**: CognitiveStack (CogStack) - *"The Full Stack for AI Intelligence"*  
> **Website**: cogstack.co.za  
> **Date**: February 2026  
> **Target**: Windows Laptop with Revit 2026 (30-day trial)
> 
> **Client Context**: Triviron Holdings - South African construction company specializing in government buildings (schools, courts, community centers)

--eyazi

## Two-Phase Workflow

This project follows a two-phase approach:

### Phase 1: Desktop Preparation (Current)
- Fork and customize the revit-mcp-python repository
- Use Claude Code to understand the codebase
- Prepare demo scripts and documentation
- Push to CognitiveStack GitHub

### Phase 2: Laptop Execution (When Hardware Arrives)
- Clone the prepared repository
- Install Revit 2026 + pyRevit
- Configure and run the de

## Table of Contents

### Phase 1: Desktop Preparation
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites Checklist](#prerequisites-checklist)
3. [Fork Repository to CognitiveStack](#fork-repository-to-cognitivestack)
4. [Explore with Claude Code](#explore-with-claude-code)

### Phase 2: Laptop Execution
5. [Install Revit 2026](#step-1-install-revit-2026)
6. [Install pyRevit](#step-2-install-pyrevit)
7. [Install UV Package Manager](#step-3-install-uv-package-manager)
8. [Clone Your Repository](#step-4-clone-your-repository)
9. [Install Python Dependencies](#step-5-install-python-dependencies)
10. [Install the pyRevit Extension](#step-6-install-the-pyrevit-extension)
11. [Enable pyRevit Routes Server](#step-7-enable-pyrevit-routes-server)
12. [Configure Claude Desktop](#step-8-configure-claude-desktop)
13. [Test the Connection](#step-9-test-the-connection)
14. [Load Sample Project](#step-10-load-sample-project)

### Demo & Reference
15. [Demo Script: Government Building Prompts](#demo-script-government-building-prompts)
16. [Troubleshooting](#troubleshooting)
17. [Screen Recording Setup (Backup)](#screen-recording-setup-backup)
18. [Future: Enterprise Architecture](#future-enterprise-architecture)
19. [Resources](#resources)

---

## Architecture Overview

For the demo, everything runs **locally** on your Windows laptop. No cloud infrastructure needed.

```
┌─────────────────────────────────────────────────────────────────┐
│              YOUR WINDOWS LAPTOP (Demo Environment)              │
│                                                                  │
│  ┌──────────────────┐                                           │
│  │  Claude Desktop  │◄──── You type natural language prompts    │
│  │  (LLM Client)    │                                           │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           │ MCP Protocol (stdio)                                 │
│           ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  revit-mcp-python MCP Server (main.py)                    │   │
│  │  - Runs via UV                                            │   │
│  │  - Translates MCP tool calls → HTTP requests              │   │
│  └────────┬─────────────────────────────────────────────────┘   │
│           │                                                      │
│           │ HTTP (localhost:48884)                               │
│           ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Revit 2026                             │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  pyRevit Extension                                  │  │   │
│  │  │  └── revit-mcp-python.extension                     │  │   │
│  │  │      └── Routes API (exposed via pyRevit)           │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                           │   │
│  │  📁 Sample Project (.rvt file loaded)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. You ask Claude Desktop: "How many doors are in this building?"
2. Claude Desktop calls the MCP tool `get_revit_model_info`
3. The MCP server (main.py) sends HTTP request to `localhost:48884/revit_mcp/model_info/`
4. pyRevit Routes API inside Revit queries the Revit API
5. Response flows back: Revit → pyRevit → MCP Server → Claude Desktop
6. Claude responds: "The model contains 47 doors across 3 levels..."

---

## Prerequisites Checklist

Before starting, ensure you have:

**Phase 1 (Desktop - Now):**
- [ ] GitHub account with CognitiveStack organization access
- [ ] Claude Pro subscription (for Claude Code in Zed Editor)
- [ ] Git installed on desktop

**Phase 2 (Laptop - Later):**
- [ ] Windows 10/11 laptop
- [ ] Administrator access
- [ ] Autodesk account (for Revit trial)
- [ ] Claude Desktop installed
- [ ] Internet connection (for downloads)
- [ ] ~15GB free disk space (Revit is large)

---

## Fork Repository to CognitiveStack

### Step 1: Fork the Repository

1. Go to: https://github.com/revit-mcp/revit-mcp-python
2. Click **Fork** (top right)
3. Select **CognitiveStack** as the destination organization
4. Name it: `revit-mcp-triviron` (or similar)
5. Click **Create Fork**

Your repo will be at: `https://github.com/CognitiveStack/revit-mcp-triviron`

### Step 2: Clone to Desktop

```bash
cd ~/Projects  # or your preferred location
git clone https://github.com/CognitiveStack/revit-mcp-triviron.git
cd revit-mcp-triviron
```

---

## Explore with Claude Code

Use Claude Code in Zed Editor to understand and customize the codebase.

### Key Files to Explore

| File | Purpose | Priority |
|------|---------|----------|
| `main.py` | MCP Server entry point | ⭐ High |
| `tools/` | MCP tool definitions | ⭐ High |
| `revit_mcp/` | pyRevit Routes API endpoints | Medium |
| `LLM.txt` | Context file for LLMs | Read first! |
| `pyproject.toml` | Python dependencies (UV) | Reference |

### Suggested Claude Code Prompts

```
@file LLM.txt
Explain the architecture of this Revit MCP system. 
How does Claude Desktop communicate with Revit?
```

```
@file main.py @file tools/
List all the available MCP tools and what they do.
Which ones would be most useful for querying a school building model?
```

```
@workspace
What customizations could we make to tailor this for 
a construction company that builds schools and government buildings?
```

### Customization Ideas

Consider adding custom prompts or tools for Triviron's use cases:

- **Room schedules**: "List all classrooms with their areas"
- **Accessibility compliance**: "Show all wheelchair-accessible entrances"
- **Safety**: "Count emergency exits per floor"
- **Procurement**: "Generate a door schedule for ordering"

---

## Step 1: Install Revit 2026

### Download

1. Go to: https://www.autodesk.com/products/revit/free-trial
2. Sign in with your Autodesk account
3. Download **Revit 2026** (30-day trial)
4. Run the installer and follow prompts

### Verify Installation

1. Launch Revit 2026
2. Close any "Welcome" dialogs
3. You should see the Revit start screen
4. Close Revit for now (we'll configure pyRevit first)

---

## Step 2: Install pyRevit

pyRevit is the foundation that enables the MCP bridge inside Revit.

### Download pyRevit

1. Go to: https://github.com/pyrevitlabs/pyRevit/releases
2. Download the latest **stable** release: `pyRevit_5.x.x.xxxxx_signed.msi`
   - Use the `.msi` installer (more reliable than `.exe`)
   - As of January 2026, version **5.1.0+** supports Revit 2026

### Install

1. Run the MSI installer
2. Accept defaults (All Users installation recommended)
3. Complete the installation

### Verify pyRevit Installation

1. Launch Revit 2026
2. Look for the **pyRevit** tab in the ribbon
3. If you see it, pyRevit loaded successfully!

**Note**: First launch may take longer as pyRevit initializes.

---

## Step 3: Install UV Package Manager

UV is a fast Python package manager. The MCP server uses it.

### Install UV on Windows

Open **PowerShell as Administrator** and run:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Add UV to PATH

After installation, add UV to your PATH:

```powershell
# Add to current session
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"

# Verify installation
uv --version
```

To make this permanent, add `%USERPROFILE%\.local\bin` to your System PATH via:
- Settings → System → About → Advanced system settings → Environment Variables

---

## Step 4: Clone Your Repository

### Clone from CognitiveStack

```powershell
# Create a directory for the project
mkdir C:\Projects
cd C:\Projects

# Clone YOUR customized repository (not the original)
git clone https://github.com/CognitiveStack/revit-mcp-triviron.git
cd revit-mcp-triviron
```

**Important**: Note the full path to `main.py`:
```
C:\Projects\revit-mcp-triviron\main.py
```
You'll need this for Claude Desktop configuration.

---

## Step 5: Install Python Dependencies

### Install with UV Sync

```powershell
cd C:\Users\charles\projects\revit-mcp-triviron

# UV sync creates .venv and installs all dependencies from pyproject.toml
uv sync
```

### Verify Dependencies

```powershell
# Verify key packages are available
uv --directory "C:\Users\charles\projects\revit-mcp-triviron" run python -c "import httpx; import mcp; print('Dependencies OK')"
```

> **Note**: The project uses `pyproject.toml` with `uv sync`, not `requirements.txt` with `pip install`. The `requirements.txt` is a reference listing only. `uv sync` reads `pyproject.toml` and the `uv.lock` lockfile.

---

## Step 6: Install the pyRevit Extension

The repository contains a pyRevit extension (`revit-mcp-python.extension/`) that must be copied into pyRevit's Extensions directory.

### Copy Extension to pyRevit

```powershell
# Copy the extension folder to pyRevit's Extensions directory
# Using PowerShell:
Copy-Item -Recurse -Force ".\revit-mcp-python.extension" "$env:APPDATA\pyRevit\Extensions\revit-mcp-python.extension"

# Or using Git Bash:
cp -r revit-mcp-python.extension "$APPDATA/pyRevit/Extensions/revit-mcp-python.extension"
```

### Verify Extension Installed

```powershell
# Confirm the files are in place
ls "$env:APPDATA\pyRevit\Extensions\revit-mcp-python.extension\"
```

You should see: `extension.json`, `lib/`, `startup.py`

### Reload pyRevit

In Revit, click the **pyRevit** ribbon tab and click **Reload** (circular arrow icon). This loads the new extension without restarting Revit.

> **Important - Keeping in Sync**: When you modify files in `revit_mcp/` (the backend source), you must re-copy them to both `revit-mcp-python.extension/lib/revit_mcp/` (in the repo) and `%APPDATA%\pyRevit\Extensions\revit-mcp-python.extension\lib\revit_mcp\` (deployed), then reload pyRevit.
>
> Quick sync commands:
> ```bash
> cp -r revit_mcp/* revit-mcp-python.extension/lib/revit_mcp/
> cp -r revit_mcp/* "$APPDATA/pyRevit/Extensions/revit-mcp-python.extension/lib/revit_mcp/"
> ```

---

## Step 7: Enable pyRevit Routes Server

The Routes server is what exposes the HTTP API inside Revit.

### Enable Routes

1. In Revit, go to **pyRevit tab** → **Settings**
2. Navigate to the **Routes** section
3. Check/enable **Routes Server**
4. Note the port: default is `48884`
5. Save settings
6. Restart Revit

### Verify Routes Server

After restarting Revit with a project open:

1. Open your web browser
2. Navigate to: `http://localhost:48884/revit_mcp/status/`
3. You should see a JSON response like:

```json
{
  "status": "active",
  "health": "healthy",
  "revit_available": true,
  "document_title": "your_project_name",
  "api_name": "revit_mcp"
}
```

If you see this, the Revit side is working!

---

## Step 8: Configure Claude Desktop

### Locate Claude Desktop Config

The configuration file is at:
```
%APPDATA%\Claude\claude_desktop_config.json
```

> **Note**: This is different from Claude Code's config (`config.json`). 
> Claude Desktop uses `claude_desktop_config.json`.

### Edit Configuration

Open the file in a text editor and add the MCP server configuration:

```json
{
  "mcpServers": {
    "revit": {
      "command": "uv",
      "args": ["--directory", "C:/Users/charles/projects/revit-mcp-triviron", "run", "python", "main.py"],
      "env": {}
    }
  }
}
```

**Important**: 
- The `--directory` flag tells `uv` where to find `pyproject.toml` and the `.venv` with dependencies (like `httpx`). Without it, `uv` cannot resolve the project dependencies and the server will fail with `ModuleNotFoundError: No module named 'httpx'`.
- Forward slashes `/` work in the path (even on Windows)
- Update the path to match your actual installation location
- This references YOUR CognitiveStack fork, not the original repo

### Restart Claude Desktop

1. Completely close Claude Desktop (check system tray)
2. Reopen Claude Desktop
3. Look for the **hammer icon** (🔨) in the input area
4. Click it to see available MCP tools

---

## Step 9: Test the Connection

### Ensure Everything is Running

1. **Revit 2026** is open with a project loaded
2. **pyRevit Routes Server** is enabled (check via browser: `http://localhost:48884/revit_mcp/status/`)
3. **Claude Desktop** is open and shows the hammer icon

### First Test Prompt

In Claude Desktop, type:

```
Can you check if Revit is connected and tell me about the current model?
```

Claude should:
1. Call `get_revit_status` tool
2. Call `get_revit_model_info` tool
3. Respond with information about your loaded project

---

## Step 10: Load Sample Project

### Metric System Requirement

Triviron operates in South Africa, so **metric units** are required. Choose one of these options:

### Option 1: School Project (Recommended) ⭐

Download from Library Revit - perfect for Triviron's government building focus:

**URL**: https://libraryrevit.com/rvt/school-project-developed/

- **Size**: 38.31 MB
- **Type**: Educational facility
- **Why**: Directly relevant to Triviron's work (schools, courts, community centers)

### Option 2: DACH Sample (Built-in, Metric)

Revit includes a metric sample project:

**Location**: `C:\Program Files\Autodesk\Revit 2026\Samples\DACH_sample_project.rvt`

- **Units**: Metric (German/Austrian/Swiss standards)
- **Type**: General building
- **Why**: Guaranteed to work, no download needed

### Option 3: Convert Imperial to Metric

If using `rac_advanced_sample_project.rvt`:

1. Open the project
2. Go to **Manage** → **Project Units**
3. Change from Imperial to Metric
4. Save as a new file

### Recommended Workflow

1. **Primary**: Download and use the School Project
2. **Backup**: Have DACH_sample_project ready
3. **Testing**: Use rac_advanced_sample_project for initial setup verification

---

## Demo Script: Government Building Prompts

These prompts are tailored for Triviron's focus on schools, courts, and community centers.

### 1. Connection & Overview

```
Is Revit connected? What project is currently open?
```

```
Give me an overview of this building - how many floors, 
what type of spaces does it contain?
```

### 2. Educational Facility Queries (School Demo)

```
How many classrooms are in this school building?
```

```
What is the total floor area of all educational spaces?
```

```
List all the rooms on the ground floor with their areas in square meters.
```

### 3. Safety & Compliance

```
How many emergency exits are there? Show me a breakdown by floor.
```

```
Are there any rooms larger than 100 square meters that might 
require additional fire exits?
```

```
List all doors - I need to verify fire door specifications.
```

### 4. Accessibility (Critical for Government Buildings)

```
How many entrances does this building have? 
Which ones could accommodate wheelchair access?
```

```
What's the distance from the main entrance to the lift?
```

### 5. Procurement & Scheduling

```
Generate a door schedule showing type, size, and quantity.
```

```
How many windows of each type are in the building? 
I need this for a procurement order.
```

```
What wall types are used? Give me quantities for estimating.
```

### 6. Visual Documentation

```
Can you show me a screenshot of the Level 1 floor plan?
```

```
Export the building section view as an image.
```

```
What views are available for documentation?
```

### 7. Advanced Analysis

```
If we needed to add another classroom on Level 2, 
what's the available space?
```

```
Summarize this building's key metrics for a project handover report:
- Total gross floor area
- Number of levels
- Room count by type
- Key building systems
```

### Demo Tips for Triviron Presentation

1. **Start simple**: "Is Revit connected?" → builds confidence
2. **Show relevance**: Use school/government building vocabulary
3. **Demonstrate value**: Focus on time-saving queries (schedules, counts)
4. **Visual impact**: Export a view to show integration depth
5. **End strong**: "Generate a summary for handover" → shows practical application

### If Something Fails

- Move gracefully to the next prompt
- Say: "Let me try a different approach..."
- Have backup screen recording ready!

---

## Troubleshooting

### "MCP revit: Server disconnected" in Claude Desktop

This is the most common error. Check the MCP server log at:
```
%APPDATA%\Claude\logs\mcp-server-revit.log
```

**Common causes:**

1. **`ModuleNotFoundError: No module named 'httpx'`**: The Claude Desktop config is missing the `--directory` flag. UV cannot find the project's `.venv` without it. Fix: ensure your config uses `"args": ["--directory", "C:/path/to/project", "run", "python", "main.py"]`

2. **Invalid JSON in config**: Check `%APPDATA%\Claude\claude_desktop_config.json` for syntax errors.

3. **Wrong path**: Ensure the path to the project directory is correct and `main.py` exists there.

### "Connection Refused" Error (curl to Revit)

1. **Is Revit running?** Must have a project open.
2. **Is Routes Server enabled?** Check pyRevit Settings → Routes → ensure enabled on port 48884.
3. **Is the extension loaded?** Files must exist at `%APPDATA%\pyRevit\Extensions\revit-mcp-python.extension\`
4. **Test manually**: `curl http://localhost:48884/revit_mcp/status/`

### Claude Desktop Doesn't Show Hammer/Tools Icon

1. **Check config path**: `%APPDATA%\Claude\claude_desktop_config.json`
2. **Restart Claude Desktop completely** (right-click system tray icon → Quit, then reopen)
3. **Check logs**: `%APPDATA%\Claude\logs\mcp-server-revit.log`

### "ElementId object has no attribute IntegerValue"

This occurs on Revit 2024+ due to an API breaking change. The `revit_mcp/utils.py` file includes a compatibility helper `get_element_id_value()` that uses pyRevit's `compat` module. If you see this error:

1. Ensure you have the latest code (with the compat fix)
2. Re-sync the extension: `cp -r revit_mcp/* "$APPDATA/pyRevit/Extensions/revit-mcp-python.extension/lib/revit_mcp/"`
3. Reload pyRevit in Revit (pyRevit ribbon → Reload)

### Tools Return "Operation completed successfully" But No Data

This was caused by `tools/utils.py:format_response()` discarding structured response data. The fix returns full JSON for successful responses. If you see this:

1. Ensure you have the latest `tools/utils.py`
2. Restart Claude Desktop to pick up the change

### View Export Shows No Image

If `get_revit_view` returns text instead of an image, ensure `tools/view_tools.py` returns the `Image` object directly (not `str(response)`). The fix removes the `-> str` return type annotation.

### After Code Changes: What to Reload

| What Changed | What to Reload |
|-------------|----------------|
| `revit_mcp/*.py` (backend) | Sync to extension folder + Reload pyRevit in Revit |
| `tools/*.py` or `main.py` (MCP server) | Restart Claude Desktop |
| Both | Sync + Reload pyRevit + Restart Claude Desktop |

### pyRevit Not Loading

1. Check pyRevit logs: `%APPDATA%\pyRevit\`
2. Ensure correct pyRevit version for Revit 2026
3. Try: pyRevit tab → Reload

### Port 48884 Already in Use

If running multiple Revit instances, each uses a different port:
- 1st instance: 48884
- 2nd instance: 48885
- etc.

The MCP server finds the right port by itself: it tries 48884–48889 and uses the first one where `/revit_mcp/status/` answers, and looks again if Revit stops answering. To pin one port instead, set the `REVIT_PORT` environment variable before starting the server (PowerShell: `$env:REVIT_PORT = "48885"`), or set `$RevitPort` in `scripts/start-revit-mcp.ps1`.

---

## Screen Recording Setup (Backup)

If live demo has issues, show a pre-recorded video.

### Recommended: OBS Studio (Free)

1. Download from: https://obsproject.com/
2. Install and launch
3. Add **Display Capture** source
4. Set output format: MP4, 1080p, 30fps
5. Record your demo session

### Recording Tips

- Close unnecessary applications
- Use a clean desktop
- Increase font sizes in Claude Desktop and Revit for visibility
- Narrate what you're doing
- Keep it under 5 minutes

---

## Future: Enterprise Architecture

After proving the concept, discuss with Triviron about enterprise deployment:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HOSTINGER (bigtorig.com)                          │
│  ┌─────────┐    ┌──────────────┐    ┌─────────────────────────────┐ │
│  │  Caddy  │───▶│  Chat UI     │───▶│  MCP Bridge Service         │ │
│  │         │    │  (Next.js)   │    │  (WebSocket/SSE relay)      │ │
│  └─────────┘    └──────────────┘    └──────────────┬──────────────┘ │
│       ▲  revit.bigtorig.com                        │                │
└───────┼────────────────────────────────────────────┼────────────────┘
        │                                            │
        │                               Secure Tunnel (TBD)
        │                               - Cloudflare Tunnel?
        │                               - Tailscale?
        │                               - Custom VPN?
        │                                            │
┌───────┴────────────────────────────────────────────┼────────────────┐
│            TRIVIRON CORPORATE NETWORK              │                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Workstation 1                                                │  │
│  │  ┌─────────┐    ┌────────────────────────────────────────┐   │  │
│  │  │ Revit   │◄──▶│ pyRevit + revit-mcp-python              │   │  │
│  │  └─────────┘    │ + Tunnel Client                         │   │  │
│  │                 └────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  (Repeat for each Revit workstation)                               │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Questions for Triviron Meeting:**
1. How many Revit workstations?
2. Corporate network/firewall policies?
3. Can we install tunnel clients?
4. Single model or multiple concurrent projects?
5. Authentication requirements?

---

## Resources

### CogStack Resources
- **CogStack Website**: https://cogstack.co.za
- **CogStack GitHub**: https://github.com/CognitiveStack
- **This Project**: https://github.com/CognitiveStack/revit-mcp-triviron

### Primary Repository
- **revit-mcp-python (Original)**: https://github.com/revit-mcp/revit-mcp-python

### Sample Projects (Metric)
- **School Project**: https://libraryrevit.com/rvt/school-project-developed/ (38.31 MB) ⭐
- **DACH Sample**: Built into Revit at `C:\Program Files\Autodesk\Revit 2026\Samples\DACH_sample_project.rvt`

### pyRevit
- **Website**: https://www.pyrevitlabs.io/
- **GitHub**: https://github.com/pyrevitlabs/pyRevit
- **Documentation**: https://pyrevitlabs.notion.site/

### Learning Revit API
- **Erik Frits**: https://www.youtube.com/@ErikFrits
- **LearnRevitAPI.com**: https://www.learnrevitapi.com/

### MCP Protocol
- **Anthropic MCP Docs**: https://modelcontextprotocol.io/
- **MCP GitHub**: https://github.com/modelcontextprotocol

### Tools
- **UV Package Manager**: https://docs.astral.sh/uv/
- **Claude Desktop**: https://claude.ai/download
- **OBS Studio** (screen recording): https://obsproject.com/

---

## Available MCP Tools (Reference)

| Tool | Description | Demo Value | Status |
|------|-------------|------------|--------|
| `get_revit_status` | Check if Revit MCP is active | ⭐ Essential | Verified |
| `get_revit_model_info` | Get comprehensive model info | ⭐ Essential | Verified |
| `list_levels` | Get all levels with elevations | High | Verified |
| `get_revit_view` | Export view as PNG image | ⭐ Essential | Verified |
| `list_revit_views` | Get all exportable views by type | High | Verified |
| `place_family` | Place a family instance at coordinates | Advanced | Verified |
| `list_families` | Get available family types (up to 50) | Medium | Verified |
| `list_family_categories` | Get family categories with counts | Medium | Verified |
| `get_current_view_info` | Info about active view | High | Verified |
| `get_current_view_elements` | Elements in current view with locations | High | Verified |
| `color_splash` | Color elements by parameter value | Visual Impact | Verified |
| `clear_colors` | Remove color overrides from a category | Visual Impact | Verified |
| `list_category_parameters` | List parameters available for coloring | Medium | Verified |
| `execute_revit_code` | Run IronPython code in Revit context | Power User | Verified |

> **All 14 tools verified working** on 10 February 2026 against Snowdon Towers Sample Structural model (Revit 2024+).
>
> **Revit 2024+ Compatibility**: The backend uses `get_element_id_value()` from `revit_mcp/utils.py` which wraps pyRevit's `compat` module to handle the `ElementId.IntegerValue` -> `ElementId.Value` breaking change, with `int()` conversion to prevent IronPython `long` serialization errors.

---

## Checklist: Two-Phase Approach

### Phase 1: Desktop Preparation
- [x] Fork created at github.com/CognitiveStack/revit-mcp-triviron
- [x] Codebase explored with Claude Code in Zed Editor
- [x] Demo prompts customized for government buildings
- [x] This documentation prepared

### Phase 2: Laptop Execution
- [x] Revit installed with sample project (Snowdon Towers Sample Structural)
- [x] pyRevit v5.1.0+ installed and loading (pyRevit ribbon visible)
- [x] Routes Server enabled in pyRevit Settings -> Routes (port 48884)
- [x] revit-mcp-triviron cloned from CognitiveStack GitHub
- [x] UV installed (`uv --version`), dependencies installed (`uv sync`)
- [x] Extension copied to `%APPDATA%\pyRevit\Extensions\revit-mcp-python.extension\`
- [x] pyRevit reloaded in Revit after extension install
- [x] Connection verified: `curl http://localhost:48884/revit_mcp/status/`
- [x] Claude Desktop configured with `claude_desktop_config.json` (using `--directory` flag)
- [x] Claude Desktop restarted and shows tools icon
- [x] Sample project opened in Revit
- [x] Test prompt in Claude Desktop: "Are you connected to Revit?"
- [x] **All 14 MCP tools verified working (10 Feb 2026)**
- [ ] Backup screen recording ready (OBS)
- [ ] Presentation materials for Triviron prepared

---

## Notes

**Created for**: Triviron Holdings AI Transformation Proposal  
**Organization**: CognitiveStack - *"The Full Stack for AI Intelligence"*  
**Phase**: Proof of Concept / Demo  
**Next Steps**: Enterprise architecture design pending Triviron meeting

### Questions to Ask Triviron
1. How many Revit workstations do you operate?
2. What's your typical project size (m², floors)?
3. Most common compliance checks you perform?
4. Interest in automated schedule generation?
5. Current pain points in documentation workflow?

---

*Document prepared by CogStack*  
*https://cogstack.co.za*  
*Last updated: 10 February 2026*  
*All 14 MCP tools verified working. Fixes applied: Revit 2024+ ElementId compat (int() wrap for IronPython long), format_response for status-less responses, BuiltInParameter fallback for Family Name/Type Name, Claude Desktop --directory flag, extension sync workflow.*
