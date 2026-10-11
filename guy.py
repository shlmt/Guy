import asyncio
import os

from guy.harness import main

os.environ["PYDANTIC_AI_NO_BANNER"] = "1"

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (EOFError, KeyboardInterrupt):
        exit(1)
