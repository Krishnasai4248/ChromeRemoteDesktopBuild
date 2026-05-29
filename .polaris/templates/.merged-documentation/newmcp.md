---
description: Scaffold an MCP server with FastMCP framework and organization conventions.
---

## User Input

**Telemetry**: Run: `polaris telemetry record newmcp --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Scaffold a new Model Context Protocol (MCP) server using FastMCP with auto-discovery, health checks, and authentication following organization patterns.

## Execution Steps

### 1. Discovery

Ask the user:

- **Domain name**: What domain does this MCP server cover? (e.g., `database`, `monitoring`, `deployment`)
- **Initial tools**: List 2-3 tools this server should expose (e.g., `query`, `list-tables`, `run-migration`)
- **Auth requirements**: None, API key, or OAuth
- **Transport**: stdio (default for local) or SSE (for remote)

### 2. Scaffold from Template

**Online mode** (preferred): Clone the MCP template:

```bash
git clone --depth 1 -b tool-list-require-headers https://github.com/Shared-Technology-Group/next-ai-mcp-tools.git <domain>-mcp-server
cd <domain>-mcp-server
python -c "import shutil; shutil.rmtree('.git')"
git init --initial-branch main
```

**Offline mode** (fallback): Generate the standard MCP structure:

```
<domain>-mcp-server/
  framework/
    auto_discovery.py
    auth.py
    health.py
  src/
    <domain>/
      __init__.py
      tools.py
  tests/
    test_tools.py
  run_server.py
  Dockerfile
  pyproject.toml
  README.md
```

### 3. Generate Tool Stubs

For each initial tool, create a stub in `src/<domain>/tools.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("<domain>")

@mcp.tool()
async def <tool_name>(param: str) -> str:
    """<tool_description>"""
    # TODO: Implement
    return f"<tool_name> called with {param}"
```

### 4. Configure Auth

Based on auth requirements:

- **None**: Skip auth middleware
- **API key**: Add API key validation in `framework/auth.py`
- **OAuth**: Configure OAuth provider settings

### 5. Add Health Endpoints

Set up standard health check at `/health` in `framework/health.py`.

### 6. Initialize Polaris

```bash
polaris init --here --merge
```

### 7. Validation

1. Install dependencies: `pip install -e ".[test]"` or `uv sync`
2. Run tests: `pytest`
3. Start server locally: `python run_server.py` (verify it starts without errors)
4. Create initial git commit (include `Co-Authored-By: Aptean Polaris <polaris@aptean.com>` trailer)

### 8. Summary

```
MCP Server scaffolded!

  Domain:    <domain>
  Tools:     <tool1>, <tool2>, <tool3>
  Auth:      <auth-type>
  Transport: <transport>
  Location:  <domain>-mcp-server/

Next steps:
  1. Implement tool logic in src/<domain>/tools.py
  2. Add tests in tests/test_tools.py
  3. Configure in your AI agent's MCP settings
```

## Operating Principles

- **FastMCP first**: Use FastMCP framework for tool registration and discovery
- **Auto-discovery**: Tools should be auto-discovered, not manually registered
- **Health checks**: Every MCP server must have a health endpoint
- **Test stubs**: Generate test stubs alongside tool stubs
- **Never overwrite**: Warn if target directory exists

## Context

{ARGS}


**Telemetry**: Run: `polaris telemetry record newmcp --feature <slug> --phase complete --agent {{AGENT_NAME}}`
