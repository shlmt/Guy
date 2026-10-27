# 🤖 guy - Coding Agent

A command-line coding agent. It understands your project and can read, write, and run files and commands inside the working directory.

אגב, לבחור הזה אפשר לקרוא גם "גיא" ;)

> **Notice:** This project is under active development and constantly evolving.


## ✨ Key Features

- **LLM chat** with persisted history and the ability to resume previous sessions.
- **Project tools:** read, write, and edit files; search files and content; list directories.
- **PowerShell execution** inside the project directory.
- **File and URL attachments** added to the conversation via `#ref` references in the text.
- **Slash commands** for managing models, API keys, and sessions.
- **Two UIs:** a plain interface (default) or a rich interface via `rich`.

## 🧰 Technologies

- **Language:** Python 3.13
- **Agent framework:** pydantic-ai
- **CLI interface:** prompt-toolkit, rich
- **Code quality:** Ruff (configured in `pyproject.toml`)

## 🏗️ Structure

- `guy.py` - entry point; wires the components together
- `guy/harness.py` - conversation loop
- `guy/agent.py` - builds the agent from the tool list
- `guy/models/` - model providers (currently Gemini only)
- `guy/tools/` - agent tools, grouped
- `guy/commands/` - slash commands
- `guy/session/` - session save and load
- `guy/attachments/` - resolves `#ref` references to files and URLs
- `guy/ui/` - user interfaces (`plain`, `rich`)

## 🚀 Setup and Run

Requirements: Python 3.13 and a Gemini API key.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set the API key (either option):

```powershell
$env:GEMINI_API_KEY = "your-key"
```

or inside the agent:

```text
/model gemini set-api-key <key>
```

Run it from the project directory you want the agent to work in:

```powershell
python guy.py          # plain interface (default)
python guy.py --rich   # rich interface
```

## 💬 Slash Commands

| Command | Description |
|---|---|
| `/model` | Pick a model from a list |
| `/model <model>` | Switch directly to a model, e.g. `/model gemini:pro` |
| `/model current` | Show the active model |
| `/model gemini set-api-key <key>` | Save an API key |
| `/model gemini remove-api-key` | Remove the saved API key |
| `/new` | Start a new session |
| `/resume <session-id>` | Resume a saved session |
| `/rename <title> [session-id]` | Rename a session |
| `/exit` | Exit |

Available models: `gemini:flash-lite`, `gemini:flash` (default), `gemini:pro`.

## 🗂️ Files and Storage

- **Global settings:** `~/.guy/config.json` (default model and API keys)
- **Per-project sessions:** `<project>/.guy/sessions/`
- File tools are restricted to the project directory; paths outside it are rejected.

## 🛣️ Notes

- The command tool runs through PowerShell, so the project is currently aimed at Windows.