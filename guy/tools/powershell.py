from pydantic_ai import RunContext
import subprocess
import tempfile

from .deps import Deps
from ..ui import app_ui

MAX_OUTPUT = 10_000
TIMEOUT = 120

def run_cmd(ctx: RunContext[Deps], command: str) -> str:
    """
    Run a PowerShell command in the project directory. 
    Returns the first 10,000 chars of combined stdout+stderr. 
    The full output is saved to a temp file whose path is reported when truncated, so it can be read in full later with read_file.
    """
    app_ui.display_message(f"run command: {command}", "Tool")
    try:

        try:
            proc = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command,
                ],
                cwd=ctx.deps.work_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {TIMEOUT}s"

        output = proc.stdout + proc.stderr
        header = f"(exit code {proc.returncode})\n"

        if len(output) <= MAX_OUTPUT:
            return header + output

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".txt",
            prefix=".powerSell_output-",
            encoding="utf-8",
        ) as fh:
            fh.write(output)
            tmp_path = fh.name

        return (
            header
            + output[:MAX_OUTPUT]
            + f"\n\n[output truncated; full output saved to {tmp_path} — read it with read_file]"
        )

    except Exception as e:
        print(f"Error running command: {e}")
        return e