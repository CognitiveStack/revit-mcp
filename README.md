# CogStack Revit MCP

> **AI-powered Revit integration via the Model Context Protocol**
>
> *"The Full Stack for AI Intelligence"* — [cogstack.co.za](https://cogstack.co.za)

---

## Why This Repo Exists

The MCP (Model Context Protocol) ecosystem for Autodesk Revit is fragmented. Multiple implementations exist, each with different architectures, trade-offs, and levels of maturity. This repository documents our evaluation, philosophy, and chosen approach for production deployments.

**Our focus:** Government building projects in South Africa — schools, courts, and community centers — where data sovereignty, local execution, and reliability matter more than bleeding-edge features.

---

## The Revit MCP Landscape (2026)

### Overview of Options

| Repository | Language | Architecture | Maturity | Notes |
|------------|----------|--------------|----------|-------|
| [Demolinator/revit-mcp-server](https://github.com/Demolinator/revit-mcp-server) | Python | pyRevit Routes | ⭐⭐⭐ | **45 tools**, best Python option |
| [Sam-AEC/Autodesk-Revit-MCP-Server](https://github.com/Sam-AEC/Autodesk-Revit-MCP-Server) | Python + C# | HTTP Bridge | ⭐⭐⭐ | Production-ready architecture |
| [oakplank/RevitMCP](https://github.com/oakplank/RevitMCP) | Python | pyRevit Routes | ⭐⭐ | Includes Web UI |
| [mcp-servers-for-revit](https://github.com/mcp-servers-for-revit/mcp-servers-for-revit) | TypeScript + C# | WebSocket | ⭐⭐ | npm package, mono repo |
| [revit-mcp/revit-mcp-python](https://github.com/revit-mcp/revit-mcp-python) | Python | pyRevit Routes | ⭐⭐ | Basic CRUD operations |
| [autodesk-platform-services/aps-sample-mcp-server-revit-automation](https://github.com/autodesk-platform-services/aps-sample-mcp-server-revit-automation) | .NET/C# | Cloud API | ⭐ | Official Autodesk (cloud-only) |

### The Official Autodesk Version

Autodesk has released an official MCP sample: [aps-sample-mcp-server-revit-automation](https://github.com/autodesk-platform-services/aps-sample-mcp-server-revit-automation).

**However, it has significant limitations:**

1. **Cloud-only** — Requires Autodesk Construction Cloud (ACC) or BIM 360
2. **Service-to-Service Auth** — Complex setup with Forge credentials, service accounts, and private keys
3. **No local execution** — Cannot query models on your workstation
4. **Vibe-coded** — Their own README calls it "an exploratory proof-of-concept"

This is **not suitable** for:
- Standalone Revit installations
- Air-gapped or restricted networks
- Organizations that haven't adopted ACC/BIM 360
- Quick demos and pilot projects

**Our assessment:** Autodesk is signaling intent but hasn't delivered a production-ready solution. The community implementations are currently more practical.

---

## Our Philosophy: pyRevit First

### Why pyRevit?

[pyRevit](https://github.com/pyrevitlabs/pyRevit) is the foundation of our approach. Here's why:

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE PYREVIT ADVANTAGE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Open source and battle-tested (since 2016)                  │
│  ✅ Huge community (10k+ GitHub stars)                          │
│  ✅ Routes API provides HTTP server inside Revit                │
│  ✅ No need for custom C# add-in development                    │
│  ✅ Works with Revit 2020-2026                                  │
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

Based on our evaluation, we recommend **[Demolinator/revit-mcp-server](https://github.com/Demolinator/revit-mcp-server)** as the foundation.

### Why Demolinator?

Despite having only 2 GitHub stars (as of writing), this implementation is exceptional:

| Feature | Details |
|---------|---------|
| **45 tools** | Building design, editing, analysis, MEP, interop, documentation |
| **Python + FastMCP** | Clean, modern implementation |
| **pyRevit Routes** | Uses the robust Routes API |
| **Multi-version support** | Revit 2024, 2025, 2026 |
| **Unit handling** | Accepts millimeters, converts to feet internally |
| **LLM.txt included** | AI-ready documentation |
| **UV compatible** | Works with modern Python tooling |

### Example Queries This Enables

```
"How many classrooms are in this school?"
"Generate a door schedule for procurement"
"List all rooms larger than 100m² that need fire exits"
"Export the Level 1 floor plan as an image"
"What elements are visible in the current view?"
"Summarize this building for a handover report"
```

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
- Autodesk Revit 2024, 2025, or 2026
- [pyRevit](https://github.com/pyrevitlabs/pyRevit/releases) (v5.0+)
- [UV](https://docs.astral.sh/uv/) (Python package manager)
- [Claude Desktop](https://claude.ai/download)

### Quick Start

```powershell
# Clone this repository
git clone https://github.com/CognitiveStack/revit-mcp.git
cd revit-mcp

# Install dependencies with UV
uv venv
uv pip install -r requirements.txt

# Enable pyRevit Routes in Revit
# Revit → pyRevit tab → Settings → Routes → Enable Server

# Configure Claude Desktop
# Edit: %APPDATA%\Claude\claude_desktop_config.json
```

### Claude Desktop Configuration

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

### Verify Connection

1. Open Revit with a project
2. Confirm pyRevit Routes is running: `http://localhost:48884/revit_mcp/status/`
3. Open Claude Desktop — look for the hammer icon (🔨)
4. Ask: *"Is Revit connected? What project is open?"*

---

## Use Cases

### Government Building Projects

This implementation is optimized for construction companies working on:

| Project Type | Example Queries |
|--------------|-----------------|
| **Schools** | "How many classrooms? What's the total floor area?" |
| **Courts** | "List all secure areas and their access points" |
| **Community Centers** | "Generate a room schedule for the tender" |
| **Accessibility** | "Show all wheelchair-accessible entrances" |
| **Compliance** | "Count emergency exits per floor" |

### Workflow Integration

```
Tender Documentation  →  "Generate door/window schedules"
Design Review         →  "What elements are in this view?"
Handover Reports      →  "Summarize key building metrics"
Procurement           →  "Count all doors by type and size"
```

---

## Security

### Data Stays Local

- ✅ MCP server runs on your workstation
- ✅ No data sent to external servers
- ✅ Open source — fully auditable
- ✅ Works offline (after initial setup)

### What Connects to the Internet?

| Component | Internet Required? |
|-----------|-------------------|
| MCP Server | ❌ No |
| pyRevit Routes | ❌ No |
| Revit (license check) | ⚠️ Every 30 days |
| Claude Desktop | ✅ Yes (AI inference) |

**Note:** Claude Desktop sends your queries to Anthropic's servers for AI processing. Your Revit model data stays local — only the queries and responses traverse the network.

---

## Roadmap

### Phase 1: Demo ✅
- [x] Evaluate MCP server options
- [x] Document architecture and philosophy
- [x] Prepare presentation materials

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
- [pyRevit Documentation](https://pyrevitlabs.notion.site/)
- [pyRevit GitHub](https://github.com/pyrevitlabs/pyRevit)
- [Routes API Guide](https://pyrevitlabs.notion.site/Routes-Server-f0e41be22cf64e3e9356e99f5bc68f97)

### MCP Protocol
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [FastMCP](https://github.com/jlowin/fastmcp)

### Revit API
- [Erik Frits](https://www.youtube.com/@ErikFrits) — Excellent tutorials
- [Revit API Docs](https://www.revitapidocs.com/)

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

## Contact

**CogStack** — *The Full Stack for AI Intelligence*

🌐 [cogstack.co.za](https://cogstack.co.za)  
📧 charles@cogstack.co.za  
🐙 [github.com/CognitiveStack](https://github.com/CognitiveStack)

---

*Last updated: May 2026*
