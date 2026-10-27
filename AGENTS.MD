# guy
Minimal, extensible coding agent. Python 3.13, PydanticAI.

## Philosophy
- Owner must understand every line. Small beats clever.
- Build only the current step. No speculative abstraction.
- Extend by adding files, not editing core.
- One job per module. Deps point inward: ui/commands -> harness -> agent/tools/models/sessions.
- PydanticAI is the engine. Use its types directly. Wrap only at edges (model providers). Never reimplement it.
- Unsure -> propose options + tradeoffs. No code until picked.

## Layout
use `showTree.ps1` to discover current files structure
- `guy.py` entry, composition root only (wires ui, agent, deps, store, command_registry into Harness)
- `agent.py` builds Agent from given tool list
- `harness.py` conversation loop, history. Sub-agents run inside it. Deps injected by guy.py
- `commands/` Command/Registry/parser + `command_registry` instance; each domain registers via `<domain>_commands.py` (e.g. `session_commands.py`) imported in `commands/__init__.py`
- `models/` ModelFactory ABC + registry, one file per provider
- `tools/` ToolsRegistry + one file per group
- `sessions.py` JSONL persistence
- `ui/` UserInterface ABC + implementations
- `deps.py`, `config.py`, `paths.py`
- ! Empty files are reminders for future implementations, do not delete them and do not commit them to GIT

## Code
- Registry over if/elif. New provider/tool/command = one file + one register call.
- Frozen dataclass for data. ABC for contracts.
- Inject deps. No globals outside `guy.py`.
- Fail loud. Catch only recoverable (rate limit, token limit).
- Comments say why. Docstring only on public contracts, one line.
- No dead code, no unused config, no unrequested features.
- New dependency needs approval.
- Import only from the module’s __init__.py. If an item is defined in a sub-file, re-export it from __init__.py first.

## State
- Project: `<project>/.guy/` (gitignored). Sessions, per-project config.
- Global: `~/.guy/`. Config, credentials. Secrets never in project.

## Work
- Smallest diff. Touch only what's asked.
- Library docs: llms.txt / SKILL first, else Context7.

## Area rules (read before touching area)
- `.agents/models.md`
- `.agents/tools.md`
- `.agents/sessions.md`
- `.agents/ui.md`

# UPDATE THIS & INSTRUCTIONS FILES whenever there are changes in the project structure or developer notes or corrections.