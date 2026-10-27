---
description: "Rich terminal UI implementation rules and guidelines for the project."
applyTo: "**/ui/rich.py"
---

# UI layer rules

Scope: implement the terminal UI behind the `UserInterface` contract in `ui/base.py`. Nothing else.

## Contract
- `ui/base.py` is the single source of truth. Never edit it unless explicitly asked.
- Implement every abstract method; do not add public methods the harness would need to call.
- No agent/business logic here. No imports from outside `ui/`.

## Stack
- use `rich` and `prompt_toolkit` only. Ask before adding any dependency.
- Before using any API, check current docs via Context7.

## Async & rendering
- Never call blocking `prompt()`; use `PromptSession.prompt_async` inside `patch_stdout()`.
- Use ONE injected `rich.console.Console`. No `print()` outside this layer.
- Rich allows only one active `Live` at a time: thinking, response streaming and tool tail
  must share one managed live region, never nest.
- Cap refresh at ~12 fps. No animation when `not console.is_terminal`; honor `NO_COLOR`.

## Style
- All colors, styles and symbols live in THEME object (Rich `Theme` names).
  No color literals anywhere else. Provide ASCII fallbacks for symbols.
- Palette, by meaning only (no other colors):
  - red: errors only. Dangerous-permission icon `!` is also red.
  - yellow-orange: permission request frame (always) and warnings. Icon/title vary by risk: `▲` judgment, `!` dangerous.
  - purple: user-related: input prompt, user text label, selections/choices, confirmations.
  - green: success, completed-ok marks and safe permissions requests.
  - turquoise-blue: agent-related: assistant header, thinking, tool panels, toolbar, banner.
  - white: readable text. Gray: system messages (e.g. session resume).

## Tool output
- While running: panel with the last N lines, spinner and elapsed time.
- On finish: collapse to a single summary line (name, short args, ok/fail, duration).
- Keep the full output in the UI; `show_tool_output` opens it in a scrollable viewer
  (prompt_toolkit app or pager) and returns to the prompt on `q`.

## Verification
- After every change run `python -m <pkg>.ui.demo` (scripted fake session that exercises
  every contract method). Keep the demo in sync with the contract.
- Keep modules small; prefer simple code over abstraction.

These Rich-specific rules apply only to the Rich UI implementation; the Plain UI must implement every method added to the base UI and may use only Python's built-in print() and input().