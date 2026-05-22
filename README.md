# CogStack Revit MCP

**AI-powered Revit integration via the Model Context Protocol**

*"The Full Stack for AI Intelligence"* — [cogstack.co.za](https://cogstack.co.za)

---

## Why This Repo Exists

The MCP (Model Context Protocol) ecosystem for Autodesk Revit is fragmented. Multiple implementations exist, each with different architectures, trade-offs, and levels of maturity. This repository documents our evaluation, philosophy, and chosen approach for production deployments.

**Our focus:** Government building projects in South Africa — schools, courts, and community centers — where data sovereignty, local execution, and reliability matter more than bleeding-edge features.

---

## The Revit MCP Landscape (2026)

### Overview of Options

| Repository | Language | Architecture | Maturity | Notes |
|------------|----------|--------------|----------|-------|
| **Demolinator/revit-mcp-server** | Python | pyRevit Routes | ⭐⭐⭐ | 45 tools, best Python option |
| Sam-AEC/Autodesk-Revit-MCP-Server | Python + C# | HTTP Bridge | ⭐⭐⭐ | Production-ready architecture |
| oakplank/RevitMCP | Python | pyRevit Routes | ⭐⭐ | Includes Web UI |
| mcp-servers-for-revit | TypeScript + C# | WebSocket | ⭐⭐ | npm package, mono repo |
| revit-mcp/revit-mcp-python | Python | pyRevit Routes | ⭐⭐ | Basic CRUD operations |
| autodesk-platform-services/aps-sample-mcp-server-revit-automation | .NET/C# | Cloud API | ⭐ | Official Autodesk (cloud-only) |

### The Official Autodesk Version

Autodesk has released an official MCP sample: `aps-sample-mcp-server-revit-automation`.

However, it has significant limitations:

- ❌ **Cloud-only** — Requires Autodesk Construction Cloud (ACC) or BIM 360
- ❌ **Service-to-Service Auth** — Complex setup with Forge credentials, service accounts, and private keys
- ❌ **No local execution** — Cannot query models on your workstation
- ❌ **Vibe-coded** — Their own README calls it "an exploratory proof-of-concept"

**This is not suitable for:**
- Standalone Revit installations
- Air-gapped or restricted networks
- Organizations that haven't adopted ACC/BIM 360
- Quick demos and pilot projects

**Our assessment:** Autodesk is signaling intent but hasn't delivered a production-ready solution. The community implementations are currently more practical.

---

## Our Philosophy: pyRevit First

### Why pyRevit?

pyRevit is the foundation of our approach. Here's why:

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE PYREVIT ADVANTAGE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Open source and battle-tested (since 2016)                  │
│  ✅ Huge community (10k+ GitHub stars)                          │
│  ✅ Routes API provides HTTP server inside Revit                │
│  ✅ No need for custom C# add-in development                    │
│  ✅ Works with Revit 2020-2027                                  │
│  ✅ Extensive documentation and tutorials                       │
│  ✅ Active maintenance by pyrevitlabs                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Comparison

**Custom C# Add-in Approach** (more complex):

```
Claude Desktop → MCP Server → Custom C# HTTP Server → Revit API
                              ↑
                              Requires Visual Studio, .NET knowledge,
                              manual add-in registration, version-specific builds
```

**pyRevit Routes Approach** (simpler):

```
Claude Desktop → MCP Server (Python/FastMCP) → pyRevit Routes → Revit API
                                                ↑
                                                Already built-in, just enable it,
                                                works across Revit versions
```

### The Trade-off

The C# approach gives you lower-level Revit API access. But for most use cases — querying models, generating schedules, exporting views — pyRevit Routes provides everything you need with dramatically less complexity.

**Our position:** Start with pyRevit. Only build custom C# when you hit its limits.

---

## Our Chosen Implementation

Based on our evaluation, we recommend **Demolinator/revit-mcp-server** as the foundation.

### Why Demolinator?

Despite having only 2 GitHub stars (as of writing), this implementation is exceptional:

| Feature | Details |
|---------|---------|
| **45 tools** | Building design, editing, analysis, MEP, interop, documentation |
| **Python + FastMCP** | Clean, modern implementation |
| **pyRevit Routes** | Uses the robust Routes API |
| **Multi-version support** | Revit 2024, 2025, 2026, 2027 |
| **Unit handling** | Accepts millimeters, converts to feet internally |
| **LLM.txt included** | AI-ready documentation |
| **UV compatible** | Works with modern Python tooling |

### Example Queries This Enables

- *"How many classrooms are in this school?"*
- *"Generate a door schedule for procurement"*
- *"List all rooms larger than 100m² that need fire exits"*
- *"Export the Level 1 floor plan as an image"*
- *"What elements are visible in the current view?"*
- *"Summarize this building for a handover report"*

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       YOUR WORKSTATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────┐                                          │
│   │  Claude Desktop  │  ← AI Interface (natural language)      │
│   └────────┬─────────┘                                          │
│            │ MCP Protocol (stdio)                               │
│            ▼                                                     │
│   ┌──────────────────┐                                          │
│   │   MCP Server     │  ← Python + FastMCP                      │
│   │   (main.py)      │     Runs as subprocess                   │
│   └────────┬─────────┘                                          │
│            │ HTTP (localhost:48884)                             │
│            ▼                                                     │
│   ┌──────────────────┐                                          │
│   │  pyRevit Routes  │  ← REST API inside Revit process        │
│   └────────┬─────────┘                                          │
│            │ Revit API                                          │
│            ▼                                                     │
│   ┌──────────────────┐                                          │
│   │  Autodesk Revit  │  ← Your BIM model                       │
│   └──────────────────┘                                          │
│                                                                  │
│   🔒 100% LOCAL — No data leaves your network                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Windows 10/11
- Autodesk Revit 2024, 2025, 2026, or **2027**
- pyRevit (**v6.4.0+ required for Revit 2027**)
- UV (Python package manager)
- Claude Desktop

---

### Step 1: Install pyRevit

#### For Revit 2027 Users

**⚠️ CRITICAL:** Revit 2027 requires pyRevit **v6.4.0 or later**!

##### 1.1 Download pyRevit 6.4.0+

Visit: https://github.com/pyrevitlabs/pyRevit/releases

Download: **`pyRevit_6.4.x_signed.exe`** (latest version)

##### 1.2 Install as Administrator

1. Right-click the downloaded `.exe` file
2. Select **"Run as administrator"**
3. Follow the installation wizard
4. Accept defaults (installs to `%APPDATA%\pyRevit-Master`)

##### 1.3 Verify Installation

Open PowerShell and run:

```powershell
pyrevit --version
```

Should output: `pyrevit v6.4.0` or later ✅

##### 1.4 Register the Clone

```powershell
# Register the installed pyRevit as a clone named "master"
pyrevit clones add master "$env:APPDATA\pyRevit-Master"

# Verify it's registered
pyrevit clones
```

##### 1.5 Attach to Revit 2027

```powershell
# Attach using default engine for all installed Revits
pyrevit attach master default --installed

# Verify attachment
pyrevit attached
```

Should show: `Attachments: 2027` ✅

##### 1.6 Launch Revit

1. Open Revit 2027
2. Look for the **pyRevit tab** in the ribbon
3. If you see it → SUCCESS! 🎉

#### For Revit 2024-2026 Users

pyRevit v5.0+ works fine. Follow the same installation steps above, but any recent pyRevit version will work.

---

### Step 2: Enable pyRevit Routes

**IMPORTANT:** The MCP server communicates with Revit via pyRevit Routes — this MUST be enabled!

1. Open Revit with a project
2. Click **pyRevit tab** → **Settings**
3. Navigate to **Routes** section
4. Click **Enable Server**
5. Confirm it's running at: http://localhost:48884

Test it:

```powershell
# Should return JSON status
curl http://localhost:48884/revit_mcp/status/
```

---

### Step 3: Install MCP Server Dependencies

```bash
# Clone this repository
git clone https://github.com/CognitiveStack/revit-mcp.git
cd revit-mcp

# Create virtual environment with UV
uv venv

# Install dependencies
uv pip install -r requirements.txt
```

---

### Step 4: Configure Claude Desktop

Edit your Claude Desktop config:

**Location:** `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "revit": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "C:\\path\\to\\revit-mcp\\main.py"
      ]
    }
  }
}
```

**Replace** `C:\\path\\to\\revit-mcp\\main.py` with your actual path!

---

### Step 5: Verify Connection

1. **Open Revit** with a project
2. **Confirm pyRevit Routes** is running: http://localhost:48884/revit_mcp/status/
3. **Open Claude Desktop** — look for the hammer icon (🔨) in the bottom right
4. **Test the connection:**

Ask Claude:
```
Is Revit connected? What project is open?
```

If Claude responds with project details → **YOU'RE DONE!** 🎉

---

## Use Cases

### Government Building Projects

This implementation is optimized for construction companies working on:

| Project Type | Example Queries |
|--------------|----------------|
| **Schools** | *"How many classrooms? What's the total floor area?"* |
| **Courts** | *"List all secure areas and their access points"* |
| **Community Centers** | *"Generate a room schedule for the tender"* |
| **Accessibility** | *"Show all wheelchair-accessible entrances"* |
| **Compliance** | *"Count emergency exits per floor"* |

### Workflow Integration

| Workflow | Query Example |
|----------|---------------|
| **Tender Documentation** | *"Generate door/window schedules"* |
| **Design Review** | *"What elements are in this view?"* |
| **Handover Reports** | *"Summarize key building metrics"* |
| **Procurement** | *"Count all doors by type and size"* |

---

## Security

### Data Stays Local

✅ MCP server runs on your workstation  
✅ No data sent to external servers  
✅ Open source — fully auditable  
✅ Works offline (after initial setup)

### What Connects to the Internet?

| Component | Internet Required? |
|-----------|-------------------|
| MCP Server | ❌ No |
| pyRevit Routes | ❌ No |
| Revit (license check) | ⚠️ Every 30 days |
| Claude Desktop | ✅ Yes (AI inference) |

**Note:** Claude Desktop sends your queries to Anthropic's servers for AI processing. Your Revit model data stays local — only the queries and responses traverse the network.

---

## Troubleshooting

### pyRevit Won't Attach

**Error:** `Can not find engine or more than one engine found with specified version "2027"`

**Solution:** Specify the engine explicitly:

```powershell
pyrevit attach master default --installed
```

The command format is:
```
pyrevit attach <clone_name> (default | <engine_version>) (<revit_year> | --installed)
```

---

### pyRevit Tab Not Appearing in Revit 2027

**Issue:** Revit 2027 opens but no pyRevit tab in ribbon

**Root cause:** You're using pyRevit v5.x which doesn't support Revit 2027

**Solution:** Upgrade to pyRevit v6.4.0+

```powershell
# Check your version
pyrevit --version

# If < 6.4.0:
# 1. Download pyRevit 6.4.0+ from GitHub releases
# 2. Uninstall old version
# 3. Install new version as administrator
# 4. Re-attach to Revit 2027
```

---

### Routes Server Not Starting

**Issue:** pyRevit Routes not responding at http://localhost:48884

**Solution:**

1. Open Revit 2027
2. Click **pyRevit tab** → **Settings**
3. Go to **Routes** section
4. Click **Enable Server**
5. Restart Revit if necessary
6. Test: http://localhost:48884/revit_mcp/status/

---

### MCP Server Connection Failed

**Issue:** Claude Desktop shows "MCP server error" or hammer icon is red

**Checklist:**

1. ✅ Revit is open with a project loaded
2. ✅ pyRevit tab is visible in Revit ribbon
3. ✅ Routes server is enabled (http://localhost:48884 responds)
4. ✅ UV dependencies installed (`uv pip install -r requirements.txt`)
5. ✅ Path in `claude_desktop_config.json` is correct
6. ✅ Claude Desktop restarted after config change

**Debug:**

```powershell
# Test Routes directly
curl http://localhost:48884/revit_mcp/status/

# Test MCP server manually
cd C:\path\to\revit-mcp
uv run python main.py
```

---

### Old pyRevit Installation Conflicts

**Issue:** Multiple pyRevit versions installed

**Solution:** Clean install

```powershell
# Remove old installation
Remove-Item "C:\Program Files\pyRevit-Master" -Recurse -Force

# Remove user installation if exists
Remove-Item "$env:APPDATA\pyRevit-Master" -Recurse -Force

# Install fresh pyRevit 6.4.0+
# Download from GitHub releases
# Run as administrator
```

---

## Roadmap

### Phase 1: Demo ✅

- ✅ Evaluate MCP server options
- ✅ Document architecture and philosophy
- ✅ Prepare presentation materials

### Phase 2: Pilot

- [ ] Deploy on client workstation
- [ ] Test with real government building projects
- [ ] Gather feedback on tool coverage

### Phase 3: Customization

- [ ] Add tools specific to SA construction workflows
- [ ] Integrate with BEE compliance queries
- [ ] Build procurement schedule exports

### Phase 4: Enterprise

- [ ] Multi-workstation deployment guide
- [ ] Network topology documentation
- [ ] Training materials

---

## Contributing

We welcome contributions, especially:

- Additional tools for government building workflows
- Documentation improvements
- Bug reports and fixes
- Translation to other languages

---

## Related Resources

### pyRevit

- [pyRevit Documentation](https://pyrevitlabs.notion.site/pyRevit-Documentation-d1d9e5c6e1824a6f9e8a5b8f8c6e6e6e)
- [pyRevit GitHub](https://github.com/pyrevitlabs/pyRevit)
- [Routes API Guide](https://pyrevitlabs.notion.site/Routes-API-Guide)

### MCP Protocol

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [FastMCP](https://github.com/jlowin/fastmcp)

### Revit API

- [Erik Frits — Excellent tutorials](https://www.youtube.com/@ErikFrits)
- [Revit API Docs](https://www.revitapidocs.com/)

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

## Contact

**CogStack — The Full Stack for AI Intelligence**

🌐 [cogstack.co.za](https://cogstack.co.za)  
📧 charles@cogstack.co.za  
🐙 [github.com/CognitiveStack](https://github.com/CognitiveStack)

---

**Last updated:** May 2026
