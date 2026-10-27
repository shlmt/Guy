---
description: Describe when these instructions should be loaded by the agent based on task context
applyTo: '**/sessions/**'
---

# Session storage
Path: <project>/.guy/sessions/<id>.jsonl.
Line 1 header: title, modified. Rest: one PydanticAI message per line.
Store each fact once. Derive, don't duplicate.
Message line shape lives in one function. Changing what's saved = edit there only.
API: create, append, load, list_recent(n). No UI or command knowledge.
