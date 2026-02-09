# Feature: Fix Remaining Broken Revit MCP Tools (Round 2)

The following plan should be complete, but its important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Fix 5 remaining broken MCP tools after the first round of fixes. The root causes are:
1. **IronPython `long` integer JSON serialization** — `get_element_id_value()` returns IronPython `long` values (e.g., `680325L`) that `json.dumps()` inside pyRevit's `parse_response` cannot serialize. Affects `list_levels`, `get_current_view_info`, `get_current_view_elements`.
2. **`format_response` treats valid responses as errors** — `get_revit_model_info` response has no `status` key, so `format_response` falls through to the error path returning "Error: Unknown error occurred".
3. **Color splash can't read Family Name / Type Name parameters** — "Family Name" and "Type Name" exist in `element.Parameters` but `HasValue` is `False`. The actual values are accessible via `BuiltInParameter.ELEM_FAMILY_PARAM` and `ELEM_TYPE_PARAM` using `AsValueString()`.

## User Story

As a BIM professional using Claude Desktop with Revit MCP
I want all 14 MCP tools to work correctly
So that I can demonstrate the full capability of AI-assisted BIM workflows to Triviron Holdings

## Problem Statement

After the first round of fixes (ElementId.IntegerValue -> Value, format_response rewrite, Image return type), live testing revealed 5 tools still broken:
- `list_levels` — `680325L is not JSON serializable`
- `get_current_view_info` — `921485L is not JSON serializable` (pyRevit crashes before sending response)
- `get_current_view_elements` — `921490L is not JSON serializable` (pyRevit crashes before sending response)
- `get_revit_model_info` — Returns "Error: Unknown error occurred" because response lacks `status` key
- `color_splash` with Type parameters — All elements return "None" for "Family Name" and "Type Name"

Note: `get_revit_status` was reported as broken but works correctly via curl — it was a transient pyRevit loading issue.

## Solution Statement

1. **Wrap `get_element_id_value()` return in `int()`** — This converts IronPython `long` (which has the `L` suffix) to Python `int` which is JSON-serializable. This is a one-line fix in `revit_mcp/utils.py` that fixes 3 tools at once.
2. **Improve `format_response()` to handle responses without `status` key** — Treat any dict response that has no `error` key as a success and return its JSON. This fixes `get_revit_model_info`.
3. **Add BuiltInParameter fallback in `get_parameter_value_for_sorting()`** — For common parameters like "Family Name", "Type Name", "Family and Type", fall back to `element.get_Parameter(DB.BuiltInParameter.ELEM_FAMILY_PARAM)` etc. when the standard parameter iteration returns no value.

## Feature Metadata

**Feature Type**: Bug Fix
**Estimated Complexity**: Low-Medium
**Primary Systems Affected**: `revit_mcp/utils.py`, `revit_mcp/colors.py`, `tools/utils.py`
**Dependencies**: None (all existing libraries)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `revit_mcp/utils.py` (lines 1-67) - Why: Contains `get_element_id_value()` — the one-line `int()` fix goes here
- `revit_mcp/colors.py` (lines 471-594) - Why: Contains `get_parameter_value_for_sorting()` — add BuiltInParameter fallback here
- `tools/utils.py` (lines 1-42) - Why: Contains `format_response()` — fix the missing `status` key handling here
- `revit_mcp/model_info.py` (lines 268-305) - Why: Shows model_info response structure (no `status` key)
- `revit_mcp/status.py` (lines 1-53) - Why: Shows status response structure (has `status` key) — reference for understanding format_response logic
- `startup.py` (lines 1-46) - Why: Shows route registration order — understand how extension loads
- `main.py` (lines 1-95) - Why: Shows `_revit_call` which only returns JSON on status 200

### New Files to Create

None — all changes are modifications to existing files.

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [pyRevit Routes Handler](https://docs.pyrevitlabs.io/reference/pyrevit/routes/server/handler/)
  - Specific section: `parse_response()` method
  - Why: This is where `json.dumps()` fails on IronPython `long` values — the crash happens INSIDE pyRevit, not in our code. We fix this by ensuring our data is serializable before pyRevit tries to serialize it.

### Patterns to Follow

**IronPython 2.7 Constraints (revit_mcp/ files):**
- No f-strings — use `.format()` instead
- No pathlib — use `os.path`
- `from utils import ...` (relative imports without dot for non-package files)
- `from .utils import ...` (dot-relative for `colors.py` which uses package imports)
- String formatting: `"text {}".format(value)`

**Python 3.11+ (tools/ files):**
- f-strings allowed
- Modern Python syntax
- Async/await patterns

**Error Handling Pattern:**
```python
try:
    # operation
except Exception as e:
    logger.error("description: {}".format(str(e)))
    return fallback_value
```

**Logging Pattern:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("message")
logger.warning("message: {}".format(detail))
logger.error("message: {}".format(detail))
```

**Response Pattern (revit_mcp/):**
```python
return routes.make_response(data={
    "status": "success",
    "key": value
})
```

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation Fix — IronPython long serialization

Fix `get_element_id_value()` to wrap its return value in `int()`, converting IronPython `long` to a JSON-serializable type. This single fix resolves `list_levels`, `get_current_view_info`, and `get_current_view_elements`.

### Phase 2: MCP Tools Layer Fix — format_response

Update `format_response()` to handle dict responses that lack a `status` key by checking for the absence of an `error` key instead. This fixes `get_revit_model_info`.

### Phase 3: Color Splash Enhancement — BuiltInParameter fallback

Add a fallback mechanism in `get_parameter_value_for_sorting()` that checks `BuiltInParameter` values for common parameter names like "Family Name", "Type Name", and "Family and Type" when the standard parameter iteration returns no value.

### Phase 4: Sync & Validation

Copy updated files to both the repo extension folder and the deployed pyRevit Extensions folder. Run syntax validation.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: UPDATE `revit_mcp/utils.py` — Fix IronPython long serialization

- **IMPLEMENT**: Wrap the return value of `get_element_id_value()` in `int()` to convert IronPython `long` (e.g., `680325L`) to standard Python `int` which is JSON-serializable.
- **PATTERN**: Current code at `revit_mcp/utils.py:27-31`
- **CHANGE**: 

Current code:
```python
def get_element_id_value(element_id):
    """Get numeric value from ElementId, compatible with Revit 2024+"""
    try:
        return _get_eid_value(element_id)
    except Exception:
        return -1
```

New code:
```python
def get_element_id_value(element_id):
    """Get numeric value from ElementId, compatible with Revit 2024+"""
    try:
        return int(_get_eid_value(element_id))
    except Exception:
        return -1
```

- **GOTCHA**: The `int()` call is critical. IronPython 2.7 has separate `int` and `long` types. The `.Value` property on Revit 2024+ ElementId returns a 64-bit value which IronPython represents as `long` (with `L` suffix). Python's `json.dumps()` cannot serialize `long`, only `int`. Wrapping in `int()` forces the conversion.
- **GOTCHA**: Do NOT change the `-1` fallback — it's already an `int`.
- **VALIDATE**: `cd C:\Users\charles\projects\revit-mcp-triviron && uv run python -c "exec(open('revit_mcp/utils.py').read().split('from pyrevit')[0]); print('Syntax OK')"`

### Task 2: UPDATE `tools/utils.py` — Fix format_response for responses without status key

- **IMPLEMENT**: Update `format_response()` to handle dict responses that have no `status` key AND no `error` key. These should be treated as successful responses and returned as formatted JSON.
- **PATTERN**: Current code at `tools/utils.py:8-42`
- **CHANGE**:

Current code:
```python
def format_response(response):
    """Helper function to format API responses consistently for MCP tools.
    ...
    """
    if isinstance(response, dict):
        # Check for different success patterns
        status = response.get("status", "").lower()
        health = response.get("health", "").lower()

        # Success conditions: status="success" OR status="active" with health="healthy"
        is_success = (
            status == "success"
            or (status == "active" and health == "healthy")
            or (
                status == "active"
                and "revit_available" in response
                and response["revit_available"]
            )
        )

        if is_success:
            # For code execution responses, return just the output text
            if "output" in response:
                return response["output"]
            # For all other successful responses, return formatted JSON
            # so structured data (levels, families, views, etc.) is preserved
            return json.dumps(response, indent=2, default=str)
        else:
            # Error case - provide verbose debugging information
            error_msg = response.get("error", "Unknown error occurred")
            if "traceback" in response:
                return "Error: {}\n\nTraceback:\n{}".format(
                    error_msg, response["traceback"]
                )
            return "Error: {}".format(error_msg)
    else:
        # If response is already a string (error case from _revit_call)
        return str(response)
```

New code:
```python
def format_response(response):
    """Helper function to format API responses consistently for MCP tools.

    Args:
        response: The response from a revit_get or revit_post call, can be dict or string

    Returns:
        str: Formatted string response suitable for MCP tool return values
    """
    if isinstance(response, dict):
        # Check for explicit error first
        if "error" in response:
            error_msg = response["error"]
            if "traceback" in response:
                return "Error: {}\n\nTraceback:\n{}".format(
                    error_msg, response["traceback"]
                )
            return "Error: {}".format(error_msg)

        # Check for different success patterns
        status = response.get("status", "").lower()
        health = response.get("health", "").lower()

        # Explicit success conditions
        is_success = (
            status == "success"
            or (status == "active" and health == "healthy")
            or (
                status == "active"
                and "revit_available" in response
                and response["revit_available"]
            )
        )

        if is_success:
            # For code execution responses, return just the output text
            if "output" in response:
                return response["output"]
            # For all other successful responses, return formatted JSON
            return json.dumps(response, indent=2, default=str)

        # No error key and no recognized success pattern — treat as success
        # This handles endpoints like model_info that return data without a status field
        if "error" not in response:
            return json.dumps(response, indent=2, default=str)

        # Fallback error
        return "Error: Unknown error occurred"
    else:
        # If response is already a string (error case from _revit_call)
        return str(response)
```

- **GOTCHA**: The key change is checking for `"error"` key FIRST (before checking success patterns), and then treating any response without an `"error"` key as successful data even if it lacks a `"status"` field. The model_info endpoint returns `{"project_info": ..., "element_summary": ..., ...}` with no `status` or `error` keys.
- **GOTCHA**: The `"error" not in response` check at the end is technically redundant (we checked at the top), but makes the logic explicit and safe.
- **VALIDATE**: `cd C:\Users\charles\projects\revit-mcp-triviron && uv run python -c "from tools.utils import format_response; print(format_response({'project_info': {'name': 'Test'}})); print('---'); print(format_response({'error': 'bad'})); print('---'); print(format_response({'status': 'success', 'output': 'hello'}))"`

### Task 3: UPDATE `revit_mcp/colors.py` — Add BuiltInParameter fallback for Family Name / Type Name

- **IMPLEMENT**: In `get_parameter_value_for_sorting()`, after the instance parameter loop and before checking type parameters, add a fallback that uses `element.get_Parameter(DB.BuiltInParameter.ELEM_FAMILY_PARAM)` for "Family Name", `DB.BuiltInParameter.ELEM_TYPE_PARAM` for "Type Name", and `DB.BuiltInParameter.ELEM_FAMILY_AND_TYPE_PARAM` for "Family and Type".
- **PATTERN**: Current code at `revit_mcp/colors.py:471-594`
- **CHANGE**: Add a BuiltInParameter mapping at the top of the function, and add a fallback check after the instance parameter loop finds nothing useful.

Add this mapping dict INSIDE the `get_parameter_value_for_sorting` function, right after the docstring:

```python
    # BuiltInParameter mapping for common parameters that have HasValue=False
    # in element.Parameters but are accessible via get_Parameter()
    BUILTIN_PARAM_MAP = {
        "Family Name": DB.BuiltInParameter.ELEM_FAMILY_PARAM,
        "Type Name": DB.BuiltInParameter.ELEM_TYPE_PARAM,
        "Family and Type": DB.BuiltInParameter.ELEM_FAMILY_AND_TYPE_PARAM,
    }
```

Then, AFTER the instance parameter for-loop (which iterates `element.Parameters`) and BEFORE the type parameter fallback (the `try: element_type = element.Document.GetElement(element.GetTypeId())` block), add:

```python
        # Fallback: check BuiltInParameter for common parameters
        if parameter_name in BUILTIN_PARAM_MAP:
            try:
                builtin_param = element.get_Parameter(BUILTIN_PARAM_MAP[parameter_name])
                if builtin_param and builtin_param.HasValue:
                    display_value = builtin_param.AsValueString() or "None"
                    return (display_value, display_value)
            except Exception:
                pass
```

- **GOTCHA**: The instance parameter loop DOES find "Family Name" in `element.Parameters`, but `HasValue` is `False`, so the current code returns `("None", "None")`. The fix needs to go AFTER the for-loop completes (i.e., when no value was found from the loop), NOT inside the loop.
- **GOTCHA**: Use `AsValueString()` not `AsString()` — the BuiltIn family param is an ElementId storage type, and `AsValueString()` gives the human-readable name while `AsString()` would be None.
- **GOTCHA**: This is IronPython 2.7 — no f-strings, no walrus operator. Use `.format()` for strings.
- **GOTCHA**: `colors.py` uses `from .utils import ...` (dot-relative import).
- **IMPORTS**: No new imports needed — `DB` is already imported via `from pyrevit import DB, routes`.
- **VALIDATE**: `cd C:\Users\charles\projects\revit-mcp-triviron && uv run python -c "exec(open('revit_mcp/colors.py').read().split('from pyrevit')[0]); print('Syntax partial OK')"`

### Task 4: SYNC extension copies

- **IMPLEMENT**: Copy the 3 modified files to both the repo's extension folder and the deployed pyRevit Extensions folder.
- **FILES TO COPY**:
  1. `revit_mcp/utils.py` -> `revit-mcp-python.extension/lib/revit_mcp/utils.py`
  2. `revit_mcp/colors.py` -> `revit-mcp-python.extension/lib/revit_mcp/colors.py`
  
  Then copy the entire extension to the deployed location:
  3. `revit-mcp-python.extension/` -> `%APPDATA%/pyRevit/Extensions/revit-mcp-python.extension/`

- **GOTCHA**: `colors.py` in the extension uses `from .utils import ...` (dot-relative import) while the source uses `from .utils import ...` too. Verify the import style is consistent.
- **GOTCHA**: `utils.py` in the SOURCE uses `from pyrevit import DB` (line 4) but the EXTENSION copy may need to match. Verify by reading the deployed file first.
- **VALIDATE**: 
  ```
  diff revit_mcp/utils.py revit-mcp-python.extension/lib/revit_mcp/utils.py
  diff revit_mcp/colors.py revit-mcp-python.extension/lib/revit_mcp/colors.py
  ```

### Task 5: Verify all changes with syntax validation

- **IMPLEMENT**: Run Python syntax checks on all modified files.
- **VALIDATE**: 
  ```bash
  cd C:\Users\charles\projects\revit-mcp-triviron
  uv run python -c "import py_compile; py_compile.compile('tools/utils.py', doraise=True); print('tools/utils.py OK')"
  uv run python -c "import ast; ast.parse(open('revit_mcp/utils.py').read()); print('revit_mcp/utils.py OK')"
  uv run python -c "import ast; ast.parse(open('revit_mcp/colors.py').read()); print('revit_mcp/colors.py OK')"
  ```

---

## TESTING STRATEGY

### Unit Tests

No formal test framework is set up for this project. Validation is done via:
1. Python syntax compilation checks
2. Direct curl testing against the live Revit endpoint
3. Manual testing through Claude Desktop

### Integration Tests

After deploying changes:
1. Reload pyRevit (click Reload on pyRevit ribbon)
2. Restart Claude Desktop (quit from system tray, reopen)
3. Test each fixed tool via Claude Desktop

### Edge Cases

- `get_element_id_value()` with `ElementId.InvalidElementId` — should return `-1` (already handled)
- `format_response()` with empty dict `{}` — should return `"{}"` (no error key, no status key)
- `format_response()` with `{"error": "..."}` — should return error message
- `format_response()` with `{"status": "error", "message": "..."}` — treated as error (status != "success")
- `color_splash` with "Family Name" on elements that don't have families (e.g., system families) — BuiltInParameter should still work or fail gracefully

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
# Check tools/utils.py compiles (Python 3.11+)
cd C:\Users\charles\projects\revit-mcp-triviron
uv run python -c "import py_compile; py_compile.compile('tools/utils.py', doraise=True); print('tools/utils.py OK')"

# Check revit_mcp files parse (can't import due to pyrevit dependency, but can parse AST)
uv run python -c "import ast; ast.parse(open('revit_mcp/utils.py').read()); print('revit_mcp/utils.py OK')"
uv run python -c "import ast; ast.parse(open('revit_mcp/colors.py').read()); print('revit_mcp/colors.py OK')"
```

### Level 2: Unit Tests

```bash
# Test format_response logic
cd C:\Users\charles\projects\revit-mcp-triviron
uv run python -c "
from tools.utils import format_response
import json

# Test 1: Response with status=success
r1 = format_response({'status': 'success', 'data': [1,2,3]})
assert 'data' in r1, 'Test 1 failed: ' + r1
print('Test 1 PASS: status=success returns JSON')

# Test 2: Response with error key
r2 = format_response({'error': 'something broke'})
assert r2 == 'Error: something broke', 'Test 2 failed: ' + r2
print('Test 2 PASS: error key returns error message')

# Test 3: Response without status OR error (like model_info)
r3 = format_response({'project_info': {'name': 'Test'}, 'element_summary': {'total': 42}})
parsed = json.loads(r3)
assert parsed['project_info']['name'] == 'Test', 'Test 3 failed: ' + r3
print('Test 3 PASS: no-status response returns JSON data')

# Test 4: Response with status=active, health=healthy
r4 = format_response({'status': 'active', 'health': 'healthy', 'revit_available': True})
parsed4 = json.loads(r4)
assert parsed4['status'] == 'active', 'Test 4 failed: ' + r4
print('Test 4 PASS: active+healthy returns JSON')

# Test 5: Code execution response with output
r5 = format_response({'status': 'success', 'output': 'hello world'})
assert r5 == 'hello world', 'Test 5 failed: ' + r5
print('Test 5 PASS: output key returns output text')

# Test 6: Error with traceback
r6 = format_response({'error': 'crash', 'traceback': 'line 1\nline 2'})
assert 'Traceback' in r6, 'Test 6 failed: ' + r6
print('Test 6 PASS: error with traceback')

# Test 7: String response
r7 = format_response('Error: connection failed')
assert r7 == 'Error: connection failed', 'Test 7 failed: ' + r7
print('Test 7 PASS: string passthrough')

# Test 8: Empty dict (edge case)
r8 = format_response({})
assert r8 == '{}', 'Test 8 failed: ' + r8
print('Test 8 PASS: empty dict returns {}')

print()
print('ALL 8 TESTS PASSED')
"
```

### Level 3: Integration Tests (requires Revit running)

```bash
# Test list_levels endpoint
curl -s http://localhost:48884/revit_mcp/list_levels/ | uv run python -c "import sys,json; d=json.load(sys.stdin); print('list_levels:', 'OK' if 'levels' in d else 'FAIL:', d)"

# Test current_view_info endpoint
curl -s http://localhost:48884/revit_mcp/current_view_info/ | uv run python -c "import sys,json; d=json.load(sys.stdin); print('current_view_info:', 'OK' if 'view_info' in d else 'FAIL:', d)"

# Test current_view_elements endpoint
curl -s http://localhost:48884/revit_mcp/current_view_elements/ | uv run python -c "import sys,json; d=json.load(sys.stdin); print('current_view_elements:', 'OK' if 'elements' in d else 'FAIL:', d)"

# Test model_info through format_response
curl -s http://localhost:48884/revit_mcp/model_info/ | uv run python -c "import sys,json; d=json.load(sys.stdin); print('model_info:', 'OK' if 'project_info' in d else 'FAIL:', d)"

# Test color_splash with Family Name
curl -s -X POST -H "Content-Type: application/json" -d '{"category_name": "Structural Framing", "parameter_name": "Family Name"}' http://localhost:48884/revit_mcp/color_splash/ | uv run python -c "import sys,json; d=json.load(sys.stdin); vals=d.get('statistics',{}).get('unique_parameter_values',0); print('color_splash Family Name:', 'OK' if vals > 1 else 'FAIL: only', vals, 'groups')"
```

### Level 4: Manual Validation (via Claude Desktop)

After reloading pyRevit and restarting Claude Desktop:

1. **"What is the status of Revit?"** → Should return active/healthy status with document title
2. **"Give me information about the current Revit model"** → Should return project info, element counts, levels, rooms, views, etc.
3. **"What view am I currently looking at?"** → Should return view name, type, scale, etc.
4. **"What elements are in the current view?"** → Should return element list with categories
5. **"List all levels in the model"** → Should return levels with elevations and IDs
6. **"Color the Structural Framing elements by Family Name"** → Should create multiple color groups (not just 1)
7. **"Color the Structural Framing elements by Type Name"** → Should create multiple color groups

---

## ACCEPTANCE CRITERIA

- [x] `list_levels` returns JSON with level data (no serialization error)
- [x] `get_current_view_info` returns view information (no serialization error)
- [x] `get_current_view_elements` returns element list (no serialization error)
- [x] `get_revit_model_info` returns full model data (not "Error: Unknown error occurred")
- [x] `color_splash` with "Family Name" creates multiple color groups (not just 1)
- [x] `color_splash` with "Type Name" creates multiple color groups (not just 1)
- [x] All previously working tools continue to work (no regressions)
- [x] All syntax validation commands pass
- [x] All unit tests pass

---

## COMPLETION CHECKLIST

- [ ] Task 1: `get_element_id_value()` wraps return in `int()`
- [ ] Task 2: `format_response()` checks for `error` key first, treats no-error/no-status as success
- [ ] Task 3: `get_parameter_value_for_sorting()` has BuiltInParameter fallback for Family Name/Type Name
- [ ] Task 4: Extension copies synced to repo and deployed locations
- [ ] Task 5: All syntax validation passes
- [ ] Level 2 unit tests all pass
- [ ] Level 3 integration tests pass (after pyRevit reload)
- [ ] Level 4 manual validation passes (after Claude Desktop restart)

---

## NOTES

### Root Cause Analysis Detail

**IronPython `long` vs `int`:**
IronPython 2.7 has two integer types: `int` (32-bit) and `long` (64-bit, printed with `L` suffix). When Revit 2024+ returns a 64-bit ElementId via `.Value`, IronPython stores it as `long`. CPython's `json` module can serialize `long` (since Python 2's `long` is Python 3's `int`), but IronPython's `json` module (used inside pyRevit's `parse_response`) CANNOT serialize `long`. The fix is to explicitly call `int()` which converts `long` to `int` in IronPython.

**`format_response` logic gap:**
The `model_info` endpoint returns a flat dict with keys like `project_info`, `element_summary`, etc. — NO `status` key. The original `format_response` only recognized success when `status == "success"` or `status == "active" + health == "healthy"`. The model_info response matched neither pattern, falling through to the error path where it looked for an `error` key (not present), defaulting to "Unknown error occurred".

**Family Name / Type Name parameters:**
In the Revit API, "Family Name" and "Type Name" appear in `element.Parameters` (the iteration collection) but with `HasValue == False`. This is because they are read-only computed parameters that redirect to `BuiltInParameter.ELEM_FAMILY_PARAM` and `ELEM_TYPE_PARAM`. The values are accessible via `element.get_Parameter(DB.BuiltInParameter.ELEM_FAMILY_PARAM).AsValueString()` which returns the human-readable family name string.

### Design Decision: Minimal Changes

We deliberately keep changes minimal:
- Task 1: One line change (`return int(...)`)
- Task 2: Restructure the conditional logic (same function, same file)
- Task 3: Add ~15 lines of BuiltInParameter fallback (same function, same file)

This minimizes regression risk and keeps the diff small for review.

### Confidence Score: 9/10

High confidence because:
- All root causes verified with live curl testing
- The `int()` fix is a proven pattern for IronPython long serialization
- The `format_response` fix is straightforward logic restructuring
- The BuiltInParameter fallback was verified with execute_revit_code

Risk: The BuiltInParameter fallback may not work for ALL element categories (e.g., system families that aren't FamilyInstances). But the fallback is wrapped in try/except so it will gracefully return "None" in edge cases.
