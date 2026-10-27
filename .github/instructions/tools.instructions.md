---
description: rules for tools
applyTo: '**/tools/**'
---

# tools
- Plain async/sync function + type hints + one-line docstring (it is the LLM description).
- Register: `register(func, group, mutates, dangerous)`. Select by group/mutates.
- `ToolSpec` frozen. Agent receives tool list, never imports tools.
- File paths only via `Deps.resolve_work_path`. No escape from work_dir.
- Return str. Errors as readable str the LLM can act on.
- Dangerous/mutating tools gated by permission layer, not inside the tool.