from .codebase import list_dir, search_content, search_files
from .files import edit_file, read_file, write_file
from .powershell import run_cmd
from .registry import ToolsRegistry

tools_registry = ToolsRegistry()

tools_registry.register(read_file, group="files")
tools_registry.register(write_file, group="files", mutates=True)
tools_registry.register(edit_file, group="files", mutates=True)

tools_registry.register(run_cmd, group="terminal", mutates=True, dangerous=True)

tools_registry.register(search_files, group="search")
tools_registry.register(search_content, group="search")
tools_registry.register(list_dir, group="search")


# in future: todo, plan, web, ask_user, delegate
