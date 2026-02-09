# Feature: Fix Revit MCP Tools for Revit 2024+ Compatibility

The following plan should be complete, but its important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Fix all broken MCP tools that were discovered during end-to-end testing with Claude Desktop against a live Revit 2024+ model (Snowdon Towers Sample Structural). The tools have five categories of issues: ElementId API incompatibility, response serialization losing data, view export not supporting 3D views and images not displaying, color_splash parameter reading producing only 1 group, and tools returning "Operation completed successfully" instead of actual data.

## User Story

As a BIM professional using Claude Desktop with the Revit MCP server,
I want all MCP tools to work reliably against Revit 2024+ models,
So that I can query model data, export views, place families, and visualize elements through natural language conversation without encountering errors or missing data.

## Problem Statement

During live testing with Claude Desktop, 7 out of 12 MCP tools either crashed, returned incomplete data, or produced incorrect results. The root causes are:

1. **ElementId.IntegerValue** was deprecated in Revit 2024 and replaced with **ElementId.Value** (64-bit). Code using the old API crashes with "ElementId object has no attribute IntegerValue".
2. **format_response()** in `tools/utils.py` discards all structured data for "success" responses, returning only "Operation completed successfully" when no `output`, `message`, `result`, or `data` key is found.
3. **get_revit_view** returns `str(Image)` instead of the Image object itself, and 3D views are not filtered out of the "not found" error's available_views list but are silently unsupported by the export logic.
4. **color_splash** parameter reading works but the MCP-side format_response discards the detailed results.
5. The **extension copy** (`revit-mcp-python.extension/lib/revit_mcp/`) must be kept in sync with the source (`revit_mcp/`).

## Solution Statement

Apply targeted fixes in dependency order:
1. Add a version-safe ElementId helper using pyRevit's `compat` module
2. Fix `format_response()` to return structured JSON data instead of discarding it
3. Fix view export to return Image objects correctly and handle 3D views
4. Ensure color_splash results flow through properly (mostly fixed by #2)
5. Add a sync script and update the deployed extension copy

## Feature Metadata

**Feature Type**: Bug Fix
**Estimated Complexity**: Medium
**Primary Systems Affected**: `revit_mcp/` (IronPython backend), `tools/` (FastMCP server), `revit-mcp-python.extension/`
**Dependencies**: pyRevit compat module, FastMCP Image class

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `revit_mcp/views.py` (lines 238, 288, 329, 330, 350, 382) - **ElementId.IntegerValue** used in `get_current_view_info` and `get_current_view_elements`. These crash on Revit 2024+.
- `revit_mcp/placement.py` (lines 131, 266, 275) - **ElementId.IntegerValue** used in `place_family` (logging) and `list_levels` (response data).
- `revit_mcp/colors.py` (lines 196, 451) - **ElementId.IntegerValue** used in `get_parameter_value_safe` and warning logs inside `color_elements_by_parameter`.
- `revit_mcp/utils.py` - Shared utility functions. **No** ElementId usage currently. This is where the version-safe helper should live.
- `tools/utils.py` (entire file) - **format_response()** is the critical bottleneck. Success responses with structured data (dicts with `views_by_type`, `families`, `levels`, `parameters`, `color_assignments`) all fall through to returning "Operation completed successfully".
- `tools/view_tools.py` (line 12) - `get_revit_view` converts Image to string with `str(response)`, losing the image data.
- `main.py` (line 44-52) - `revit_image()` correctly returns an `Image` object, but the tool wrapper converts it to string.
- `startup.py` - Route registration (identical in both locations).
- `revit_mcp/__init__.py` - Module init (no changes needed).

### New Files to Create

- None. All fixes are in existing files.

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [pyRevit compat module](https://docs.pyrevitlabs.io/reference/pyrevit/compat/)
  - Provides `get_elementid_value_func()` which returns the correct property accessor based on Revit version
  - Usage: `get_value = get_elementid_value_func(); id_value = get_value(element.Id)`
  - Why: This is pyRevit's official solution for the IntegerValue/Value breaking change

- [Revit 2024 ElementId breaking change - pyRevit GitHub Issue #1796](https://github.com/pyrevitlabs/pyRevit/issues/1796)
  - Documents the Int32 to Int64 migration
  - Fixed in pyRevit via PR #1844
  - Why: Confirms the exact nature of the breaking change

- [FastMCP Image handling](https://gofastmcp.com/servers/tools)
  - Image objects must be returned directly from tools, not converted to strings
  - `Image(data=bytes, format="png")` creates a proper MCP ImageContent block
  - Returning `str(Image)` gives the Python repr, not the image data
  - Why: Explains why view export images don't display in Claude Desktop

- [Autodesk Revit API 2024 Changes](https://www.revitapidocs.com/2024/news)
  - ElementId.IntegerValue deprecated, use ElementId.Value (Int64)
  - Why: Official Autodesk documentation of the change

### Patterns to Follow

**Naming Conventions:**
- IronPython backend: snake_case functions, PEP 8 style with `.format()` string formatting (no f-strings — IronPython 2.7)
- FastMCP tools: snake_case, f-strings allowed (Python 3.11+)
- Utility helpers: `get_*_safe()` pattern for defensive access

**Error Handling Pattern (backend):**
```python
try:
    # operation
except Exception as e:
    logger.error("Description: {}".format(str(e)))
    return routes.make_response(data={"error": "Description: {}".format(str(e))}, status=500)
```

**Error Handling Pattern (tools):**
```python
response = await revit_get("/endpoint/", ctx)
return format_response(response)
```

**Logging Pattern:**
```python
logger = logging.getLogger(__name__)
logger.info("Action: {}".format(detail))
logger.warning("Non-critical: {}".format(detail))
logger.error("Failed: {}".format(detail))
```

**Response Pattern (backend):**
All routes return `routes.make_response(data={...})` with a dict containing `status`, relevant data keys, and sometimes `message`.

**CRITICAL PATTERN - IronPython 2.7 Constraints:**
- No f-strings: use `"text {}".format(var)`
- No `from __future__` imports
- No `pathlib`
- Use `StringIO` from `StringIO` module (not `io`)
- Use `print` as function via custom lambda (already set up in code_execution.py)

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation - ElementId Compatibility Helper

Add a version-safe ElementId value accessor to `revit_mcp/utils.py` using pyRevit's `compat` module. This is the foundation that unblocks `get_current_view_info` and `get_current_view_elements`.

**Tasks:**
- Add `get_element_id_value()` helper to `revit_mcp/utils.py`
- Replace all `ElementId.IntegerValue` usages across backend files

### Phase 2: Core Fix - Response Serialization

Fix `tools/utils.py:format_response()` to return structured data as formatted text instead of discarding it. This single fix unblocks `list_families`, `list_levels`, `list_family_categories`, `list_category_parameters`, `color_splash`, `list_revit_views`, and `get_revit_model_info`.

**Tasks:**
- Rewrite `format_response()` to serialize dict responses as readable formatted text
- Ensure all data fields are preserved in output

### Phase 3: View Export Fix

Fix `tools/view_tools.py:get_revit_view` to return the Image object directly instead of converting to string. This enables image display in Claude Desktop.

**Tasks:**
- Fix return type of `get_revit_view` tool
- Verify 3D views are listed and exportable

### Phase 4: Sync Extension Copy & Validate

Copy updated `revit_mcp/` files to the extension directory and provide validation commands.

**Tasks:**
- Copy updated files to extension
- Validate with curl commands against live Revit

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: UPDATE `revit_mcp/utils.py` - Add ElementId compatibility helper

- **IMPLEMENT**: Add a `get_element_id_value(element_id)` function that safely extracts the numeric value from an ElementId using pyRevit's compat module.
- **PATTERN**: Follow the existing `get_element_name()` helper pattern at `revit_mcp/utils.py:18-26`
- **IMPORTS**: Add `from pyrevit.compat import get_elementid_value_func` at top of file
- **GOTCHA**: The `compat` module may not be available in very old pyRevit versions. Add a try/except fallback that tries `.Value` first, then `.IntegerValue`.
- **IMPLEMENTATION DETAIL**:
```python
# At module level, after imports:
try:
    from pyrevit.compat import get_elementid_value_func
    _get_eid_value = get_elementid_value_func()
except (ImportError, Exception):
    # Fallback for environments without compat module
    def _get_eid_value(eid):
        try:
            return eid.Value
        except AttributeError:
            return eid.IntegerValue

def get_element_id_value(element_id):
    """Get numeric value from ElementId, compatible with Revit 2024+"""
    try:
        return _get_eid_value(element_id)
    except Exception:
        return -1
```
- **VALIDATE**: `curl -s http://localhost:48884/revit_mcp/status/` (should still return healthy after pyRevit reload)

### Task 2: UPDATE `revit_mcp/views.py` - Fix ElementId.IntegerValue usages

- **IMPLEMENT**: Replace all `ElementId.IntegerValue` with `get_element_id_value()` calls
- **IMPORTS**: Add `from utils import normalize_string, get_element_name, get_element_id_value` (update existing import)
- **LOCATIONS TO FIX** (6 occurrences):
  - Line ~238: `"view_id": current_view.Id.IntegerValue` -> `"view_id": get_element_id_value(current_view.Id)`
  - Line ~288: `"view_id": current_view.Id.IntegerValue` (in `get_current_view_elements`) -> same fix
  - Line ~329: `"element_id": elem.Id.IntegerValue` -> `"element_id": get_element_id_value(elem.Id)`
  - Line ~340: `"category_id": elem.Category.Id.IntegerValue` -> `"category_id": get_element_id_value(elem.Category.Id)`
  - Line ~352: `level_id.IntegerValue` -> `get_element_id_value(level_id)` (in level info dict)
  - Line ~382: `elem.Id.IntegerValue` (in warning log) -> `get_element_id_value(elem.Id)`
  - Line ~399: `current_view.Id.IntegerValue` (in result dict) -> `get_element_id_value(current_view.Id)`
- **GOTCHA**: Make sure the import path is `from utils import ...` (not `from .utils import ...`) — IronPython uses flat imports in the pyRevit context.
- **VALIDATE**: `curl -s http://localhost:48884/revit_mcp/current_view_info/` (should return view info without IntegerValue error)

### Task 3: UPDATE `revit_mcp/placement.py` - Fix ElementId.IntegerValue usages

- **IMPLEMENT**: Replace all `ElementId.IntegerValue` with `get_element_id_value()` calls
- **IMPORTS**: Add `get_element_id_value` to the import from utils: `from utils import get_element_name, find_family_symbol_safely, get_element_id_value`
- **LOCATIONS TO FIX** (3 occurrences):
  - Line ~131: `new_instance.Id.IntegerValue` (logger.info) -> `get_element_id_value(new_instance.Id)`
  - Line ~266: `"element_id": new_instance.Id.IntegerValue` (response dict) -> `"element_id": get_element_id_value(new_instance.Id)`
  - Line ~318 (list_levels): `"id": level.Id.IntegerValue` -> `"id": get_element_id_value(level.Id)`
- **VALIDATE**: `curl -s http://localhost:48884/revit_mcp/list_levels/` (should return levels with numeric IDs)

### Task 4: UPDATE `revit_mcp/colors.py` - Fix ElementId.IntegerValue usages

- **IMPLEMENT**: Replace all `ElementId.IntegerValue` with `get_element_id_value()` calls
- **IMPORTS**: Update import: `from .utils import normalize_string, get_element_id_value` (note: colors.py uses relative import `.utils`)
- **GOTCHA**: colors.py uses `from .utils import normalize_string` (relative import). Keep it relative.
- **LOCATIONS TO FIX** (2 occurrences):
  - Line ~196 (in `get_parameter_value_safe`): `str(elem_id.IntegerValue)` -> `str(get_element_id_value(elem_id))`
  - Line ~451 (in `color_elements_by_parameter` warning log): `element.Id.IntegerValue` -> `get_element_id_value(element.Id)`
- **VALIDATE**: `curl -s -X POST http://localhost:48884/revit_mcp/color_splash/ -H "Content-Type: application/json" -d "{\"category_name\":\"Structural Framing\",\"parameter_name\":\"Family\"}"` (should not crash)

### Task 5: UPDATE `tools/utils.py` - Fix format_response() to preserve data

- **IMPLEMENT**: Rewrite `format_response()` so that successful responses with structured data are returned as formatted JSON text, not discarded. The key insight: when a response dict has `status=success` but no `output`/`message`/`result`/`data` key, ALL the data is being lost and replaced with "Operation completed successfully".
- **PATTERN**: The `execute_revit_code` tool works because its response has an `output` key. Other tools return structured dicts with keys like `views_by_type`, `families`, `levels`, `parameters`, `color_assignments` — none of which match the hardcoded key checks.
- **IMPLEMENTATION DETAIL**: For success responses, instead of the chain of if/elif checks, serialize the entire response dict as formatted JSON. This ensures all data flows through to Claude.
```python
import json

def format_response(response):
    """Format API responses for MCP tools."""
    if isinstance(response, dict):
        status = response.get("status", "").lower()
        health = response.get("health", "").lower()
        
        is_success = (status == "success" or 
                     (status == "active" and health == "healthy") or
                     (status == "active" and "revit_available" in response and response["revit_available"]))
        
        if is_success:
            # For code execution, return just the output
            if "output" in response:
                return response["output"]
            # For all other successful responses, return formatted JSON
            return json.dumps(response, indent=2, default=str)
        else:
            # Error responses - keep verbose error formatting
            error_msg = response.get("error", "Unknown error occurred")
            if "traceback" in response:
                return "Error: {}\n\nTraceback:\n{}".format(error_msg, response["traceback"])
            return "Error: {}".format(error_msg)
    else:
        return str(response)
```
- **GOTCHA**: Do NOT break the `execute_revit_code` tool — it relies on the `output` key check. Keep that specific check first.
- **GOTCHA**: Use `default=str` in `json.dumps` to handle any non-serializable values (like Revit objects that leaked through).
- **VALIDATE**: `uv --directory "C:/Users/charles/projects/revit-mcp-triviron" run python -c "from tools.utils import format_response; print(format_response({'status': 'success', 'levels': [{'name': 'L1', 'elevation': 0.0}], 'total_levels': 1}))"` (should print JSON with levels data, not "Operation completed successfully")

### Task 6: UPDATE `tools/view_tools.py` - Fix image return type

- **IMPLEMENT**: Change `get_revit_view` to return the Image object directly instead of converting to string. When `revit_image()` returns an Image object, return it as-is. When it returns an error string, return the string.
- **PATTERN**: FastMCP Image handling: tools that return `Image` objects get automatic base64 encoding. Returning `str(Image)` gives the Python repr.
- **IMPLEMENTATION DETAIL**:
```python
@mcp.tool()
async def get_revit_view(view_name: str, ctx: Context = None):
    """Export a specific Revit view as an image"""
    from mcp.server.fastmcp import Image
    response = await revit_image(f"/get_view/{view_name}", ctx)
    if isinstance(response, Image):
        return response  # Return Image object directly for MCP to encode
    return response  # Return error string as-is
```
- **GOTCHA**: Remove the `-> str` return type annotation. FastMCP needs to see the Image type to handle it correctly.
- **VALIDATE**: Manual test via Claude Desktop: "Show me the L3 floor plan" (should display image inline)

### Task 7: SYNC extension copy

- **IMPLEMENT**: Copy all updated `revit_mcp/` files to `revit-mcp-python.extension/lib/revit_mcp/` AND to the deployed location at `%APPDATA%/pyRevit/Extensions/revit-mcp-python.extension/lib/revit_mcp/`
- **VALIDATE**: 
```bash
# Sync to extension directory in repo
cp -r revit_mcp/* revit-mcp-python.extension/lib/revit_mcp/

# Sync to deployed pyRevit extension
cp -r revit_mcp/* "$APPDATA/pyRevit/Extensions/revit-mcp-python.extension/lib/revit_mcp/"
```
- **GOTCHA**: After syncing, user must reload pyRevit in Revit (pyRevit ribbon -> Reload) for backend changes to take effect. MCP server (tools/) changes take effect on next Claude Desktop restart.

---

## TESTING STRATEGY

### Unit Tests

No formal test framework exists in this project. Validation is done via curl commands against the live Revit instance and manual testing via Claude Desktop.

### Integration Tests

All testing is integration testing against a live Revit instance with pyRevit Routes running on localhost:48884.

### Edge Cases

- **ElementId with large values (>32-bit)**: The compat helper must handle both old and new API. Test with `get_element_id_value(DB.ElementId.InvalidElementId)` — should return -1.
- **Empty collections**: `list_families` with no families loaded, `list_levels` with no levels — should return empty lists, not errors.
- **3D view export**: May require different handling (ShadowViewsFileType vs HLRandWFViewsFileType). The existing backend code already sets `ieo.ShadowViewsFileType = DB.ImageFileType.PNG` which should handle 3D views. The issue was that the view name didn't match exactly.
- **Large responses**: `list_families` caps at 50 results. `get_current_view_elements` could return thousands of elements — consider if truncation is needed.
- **Non-ASCII characters**: The backend uses UTF-8 encoding headers. `normalize_string()` handles None values.

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
# Verify Python 3 tools code has no syntax errors
uv --directory "C:/Users/charles/projects/revit-mcp-triviron" run python -c "from tools.utils import format_response; print('OK')"
uv --directory "C:/Users/charles/projects/revit-mcp-triviron" run python -c "from tools.view_tools import register_view_tools; print('OK')"
uv --directory "C:/Users/charles/projects/revit-mcp-triviron" run python -c "import main; print('OK')"
```

Note: IronPython backend files (`revit_mcp/`) cannot be syntax-checked outside Revit since they import `pyrevit` and Revit API modules.

### Level 2: format_response Unit Test

```bash
# Test that format_response preserves structured data
uv --directory "C:/Users/charles/projects/revit-mcp-triviron" run python -c "
from tools.utils import format_response
import json

# Test 1: Success with structured data (was returning 'Operation completed successfully')
result = format_response({'status': 'success', 'levels': [{'name': 'L1'}], 'total_levels': 1})
parsed = json.loads(result)
assert 'levels' in parsed, 'FAIL: levels not in response'
print('Test 1 PASS: Structured data preserved')

# Test 2: Code execution output still works
result = format_response({'status': 'success', 'output': 'Hello World'})
assert result == 'Hello World', 'FAIL: output not returned'
print('Test 2 PASS: Code execution output works')

# Test 3: Error responses work
result = format_response({'status': 'error', 'error': 'Something broke'})
assert 'Something broke' in result, 'FAIL: error not in response'
print('Test 3 PASS: Error responses work')

# Test 4: String passthrough
result = format_response('Error: 500')
assert result == 'Error: 500', 'FAIL: string passthrough broken'
print('Test 4 PASS: String passthrough works')

print('All tests passed!')
"
```

### Level 3: Integration Tests (requires live Revit)

```bash
# These require Revit running with pyRevit Routes and the updated extension loaded

# Test status endpoint
curl -s http://localhost:48884/revit_mcp/status/

# Test model info
curl -s http://localhost:48884/revit_mcp/model_info/ | python -m json.tool | head -20

# Test list views
curl -s http://localhost:48884/revit_mcp/list_views/ | python -m json.tool | head -20

# Test list levels
curl -s http://localhost:48884/revit_mcp/list_levels/ | python -m json.tool

# Test current view info (was crashing with IntegerValue error)
curl -s http://localhost:48884/revit_mcp/current_view_info/ | python -m json.tool

# Test current view elements (was crashing with IntegerValue error)
curl -s http://localhost:48884/revit_mcp/current_view_elements/ | python -m json.tool | head -40

# Test list families
curl -s http://localhost:48884/revit_mcp/list_families/ | python -m json.tool | head -20

# Test list family categories
curl -s http://localhost:48884/revit_mcp/list_family_categories/ | python -m json.tool

# Test view export (use an actual floor plan name from the model)
curl -s "http://localhost:48884/revit_mcp/get_view/L3" | python -c "import sys,json; d=json.load(sys.stdin); print('Image size:', d.get('file_size_bytes', 'N/A'), 'bytes')"
```

### Level 4: Manual Validation via Claude Desktop

After deploying all changes:
1. Restart Revit and reload pyRevit
2. Restart Claude Desktop
3. Test each tool through natural language:
   - "Are you connected to Revit?" (get_revit_status)
   - "What model do I have open?" (get_revit_model_info)
   - "List all levels" (list_levels - was returning "Operation completed successfully")
   - "What view am I looking at?" (get_current_view_info - was crashing)
   - "What elements are in this view?" (get_current_view_elements - was crashing)
   - "Show me the L3 floor plan" (get_revit_view - was not displaying image)
   - "List available families" (list_families - was returning "Operation completed successfully")
   - "Color structural framing by Family" (color_splash - was showing only 1 group)
   - "Clear the colors on structural framing" (clear_colors)

---

## ACCEPTANCE CRITERIA

- [ ] `get_current_view_info` returns view details without ElementId errors
- [ ] `get_current_view_elements` returns element list without ElementId errors
- [ ] `list_levels` returns level names and elevations (not "Operation completed successfully")
- [ ] `list_families` returns family names and types (not "Operation completed successfully")
- [ ] `list_family_categories` returns categories with counts (not "Operation completed successfully")
- [ ] `list_category_parameters` returns parameter info (not "Operation completed successfully")
- [ ] `list_revit_views` returns views organized by type (not "Operation completed successfully")
- [ ] `get_revit_model_info` returns full model info as structured data
- [ ] `get_revit_view` displays an image inline in Claude Desktop
- [ ] `color_splash` returns statistics showing multiple color groups
- [ ] `execute_revit_code` still works correctly (no regression)
- [ ] `get_revit_status` still works correctly (no regression)
- [ ] `place_family` still works correctly (no regression)
- [ ] `clear_colors` still works correctly (no regression)
- [ ] Extension copy in `revit-mcp-python.extension/lib/revit_mcp/` matches source
- [ ] Deployed extension at `%APPDATA%/pyRevit/Extensions/` is updated

---

## COMPLETION CHECKLIST

- [ ] All 7 tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All Level 1 syntax checks pass
- [ ] All Level 2 format_response tests pass
- [ ] Level 3 curl tests return valid JSON (requires live Revit)
- [ ] Level 4 Claude Desktop manual tests all work
- [ ] No linting or import errors
- [ ] Extension copy synced
- [ ] pyRevit reloaded in Revit
- [ ] Claude Desktop restarted

---

## NOTES

### Design Decisions

1. **Using pyRevit compat module with fallback**: Rather than hardcoding `.Value`, we use pyRevit's official compat module which automatically selects the correct accessor. The fallback chain (compat -> .Value -> .IntegerValue) ensures it works across all Revit versions from 2020-2026.

2. **format_response returns JSON strings for structured data**: The simplest fix that preserves all data. An alternative was to return raw dicts from tools and let FastMCP serialize them, but that would require changing the return type annotation on every tool and testing how FastMCP handles dict returns vs string returns. JSON string is safest.

3. **Image return type**: FastMCP's Image class must be returned directly from tools. It cannot be stringified. The fix removes the `-> str` type annotation and returns Image objects as-is.

4. **No changes to backend response format**: The backend (revit_mcp/) already returns well-structured JSON. The issue is entirely on the MCP server side (tools/) where format_response() was discarding the data.

5. **Extension sync is manual**: There's no build system to automate this. The plan includes explicit copy commands. A future improvement could add a sync script.

### Key Risk: IronPython Import Paths

The `revit_mcp/` files use a mix of relative (`from .utils import`) and flat (`from utils import`) imports. When running inside pyRevit, the import resolution depends on how pyRevit configures `sys.path`. The existing code works with both patterns. When adding `get_element_id_value` to utils.py, ensure files that use `from utils import` (views.py, placement.py) add the new function there, while files using `from .utils import` (colors.py) use the relative import.

### Revit Version Matrix

| Revit Version | ElementId API | pyRevit compat |
|--------------|---------------|----------------|
| 2020-2023    | .IntegerValue | Returns .IntegerValue accessor |
| 2024+        | .Value (64-bit) | Returns .Value accessor |
| 2025-2026    | .Value only (.IntegerValue deprecated) | Returns .Value accessor |

### What Version of Revit is Running

From the demo setup docs and screenshot: **Revit 2026** (based on the title bar showing "Snowdon Towers Sample Structural" and the pyRevit ribbon). The `docs/Revit-mcp-demo-setup.md` mentions "Revit 2026". This means `.IntegerValue` will definitely fail.
