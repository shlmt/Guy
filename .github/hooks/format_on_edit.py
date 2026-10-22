# NOT IN USE!!!

import json
import subprocess
import sys

EDIT_TOOLS = {
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "edit_notebook_file",
}
FORMAT_COMMANDS = (
    ["-m", "ruff", "check", "--fix", "--exit-zero", "."],
    ["-m", "ruff", "format", "."],
)


def main():
    try:
        payload = json.load(sys.stdin)
        if payload.get("tool_name") not in EDIT_TOOLS:
            return
        for args in FORMAT_COMMANDS:
            subprocess.run(
                [sys.executable, *args],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
