#!/usr/bin/env python3
"""Agent Forge TUI — an agent (not just a chatbot) that can execute tools."""

import os
import sys
import subprocess
import json
from pathlib import Path

from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# ── Config ──────────────────────────────────────────────────────────
REPO_DIR = Path(__file__).parent
ENV_FILE = REPO_DIR / ".env"
MODEL = "openai/gpt-5.2"
MAX_TOOL_ROUNDS = 10  # prevent infinite loops

# Load API key from .env
api_key = None
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
if not api_key:
    api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: No OPENROUTER_API_KEY found in .env or environment")
    sys.exit(1)

# ── Tool definitions (OpenAI function calling format) ───────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": (
                "Execute a bash/shell command on this machine and return its output. "
                "Use this for: gh CLI (GitHub), gitagent CLI, git, file operations, "
                "curl, yt-dlp, and any other system commands."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": (
                "Search YouTube for videos matching a query, or list recent uploads "
                "from a channel handle. Returns titles, URLs, upload dates, and durations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query, or a channel handle like @zquad"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["search", "channel"],
                        "description": "search = keyword search, channel = list a channel's uploads"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 10, max 50)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file on disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative file path to read"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file on disk. Creates the file if it doesn't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write to"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
]

# ── Tool execution ──────────────────────────────────────────────────

def exec_run_bash(command: str) -> str:
    """Execute a shell command and return output."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=120, cwd=str(REPO_DIR)
        )
        output = result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 120 seconds"
    except Exception as e:
        return f"ERROR: {e}"


def exec_search_youtube(query: str, mode: str = "search", max_results: int = 10) -> str:
    """Search YouTube or list channel uploads using yt-dlp."""
    max_results = min(max_results or 10, 50)

    if mode == "channel":
        # Channel uploads — handle with or without @
        handle = query if query.startswith("@") else f"@{query}"
        url = f"https://www.youtube.com/{handle}/videos"
    else:
        # Keyword search
        url = f"ytsearch{max_results}:{query}"

    try:
        cmd = [
            "yt-dlp", "--flat-playlist", "--dump-json",
            "--playlist-end", str(max_results),
            "--no-warnings", url
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            return f"yt-dlp error: {result.stderr.strip()}"

        videos = []
        for line in result.stdout.strip().splitlines():
            try:
                data = json.loads(line)
                video = {
                    "title": data.get("title", "Unknown"),
                    "url": data.get("url") or f"https://www.youtube.com/watch?v={data.get('id', '')}",
                    "duration": data.get("duration_string") or data.get("duration", "?"),
                    "upload_date": data.get("upload_date", "?"),
                    "view_count": data.get("view_count", "?"),
                    "channel": data.get("channel") or data.get("uploader", "?"),
                }
                videos.append(video)
            except json.JSONDecodeError:
                continue

        if not videos:
            return "No results found."

        # Format as readable table
        lines = [f"Found {len(videos)} video(s):\n"]
        for i, v in enumerate(videos, 1):
            date = v["upload_date"]
            if len(date) == 8:
                date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            lines.append(
                f"{i}. {v['title']}\n"
                f"   URL: {v['url']}\n"
                f"   Duration: {v['duration']} | Uploaded: {date} | Views: {v['view_count']}"
            )
        return "\n".join(lines)

    except subprocess.TimeoutExpired:
        return "ERROR: YouTube search timed out"
    except FileNotFoundError:
        return "ERROR: yt-dlp not installed. Run: pip install yt-dlp"
    except Exception as e:
        return f"ERROR: {e}"


def exec_read_file(path: str) -> str:
    """Read a file."""
    try:
        p = Path(path)
        if not p.is_absolute():
            p = REPO_DIR / p
        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > 20000:
            content = content[:20000] + "\n... (truncated)"
        return content or "(empty file)"
    except Exception as e:
        return f"ERROR: {e}"


def exec_write_file(path: str, content: str) -> str:
    """Write a file."""
    try:
        p = Path(path)
        if not p.is_absolute():
            p = REPO_DIR / p
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {p}"
    except Exception as e:
        return f"ERROR: {e}"


TOOL_HANDLERS = {
    "run_bash": lambda args: exec_run_bash(args["command"]),
    "search_youtube": lambda args: exec_search_youtube(
        args["query"], args.get("mode", "search"), args.get("max_results", 10)
    ),
    "read_file": lambda args: exec_read_file(args["path"]),
    "write_file": lambda args: exec_write_file(args["path"], args["content"]),
}


# ── Build system prompt from gitagent export ────────────────────────
def load_system_prompt():
    """Export the gitagent system prompt via CLI, or fall back to reading files."""
    try:
        result = subprocess.run(
            ["gitagent", "export", "-f", "system-prompt"],
            capture_output=True, text=True, cwd=str(REPO_DIR)
        )
        lines = result.stdout.splitlines()
        prompt_lines = []
        capture = False
        for line in lines:
            if line.startswith("# agent-forge") or capture:
                capture = True
                prompt_lines.append(line)
        if prompt_lines:
            return "\n".join(prompt_lines)
    except FileNotFoundError:
        pass

    # Fallback: read files directly
    parts = []
    soul = REPO_DIR / "SOUL.md"
    rules = REPO_DIR / "RULES.md"
    if soul.exists():
        parts.append(soul.read_text())
    if rules.exists():
        parts.append(rules.read_text())
    for skill_dir in sorted((REPO_DIR / "skills").iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            parts.append(skill_file.read_text())
    return "\n\n".join(parts)


SYSTEM_PROMPT = load_system_prompt()

# Append tool usage instructions to system prompt
SYSTEM_PROMPT += """

## Available Runtime Tools

You have access to these tools and MUST use them when the user's request requires action:

- **run_bash** — Execute any shell command (gh, gitagent, git, curl, etc.)
- **search_youtube** — Search YouTube videos or list a channel's uploads (uses yt-dlp)
- **read_file** — Read any file on disk
- **write_file** — Write/create files on disk

When a user asks you to do something (search YouTube, create a repo, look up info), USE the tools.
Do not tell the user you "can't" do something if a tool can accomplish it.
Always prefer action over asking the user to do it manually.
"""

# ── OpenRouter client ───────────────────────────────────────────────
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# ── Theme & Console ─────────────────────────────────────────────────
theme = Theme({
    "user": "bold cyan",
    "agent": "bold green",
    "dim": "dim white",
    "header": "bold magenta",
    "tool": "bold yellow",
})
console = Console(theme=theme, width=90)

# ── Conversation state ──────────────────────────────────────────────
messages = [{"role": "system", "content": SYSTEM_PROMPT}]


def run_agent_turn(user_input: str) -> str:
    """Send a message and loop through tool calls until the agent gives a final response."""
    messages.append({"role": "user", "content": user_input})

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=8192,
            temperature=0.3,
            tools=TOOLS,
            extra_headers={"X-Title": "Agent Forge TUI"},
        )

        choice = response.choices[0]
        msg = choice.message

        # If the model wants to call tools
        if msg.tool_calls:
            # Add the assistant message with tool calls
            messages.append(msg)

            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                # Show tool call to user
                console.print()
                console.print(Text(f" Tool: {fn_name} ", style="bold black on yellow"), end="")
                if fn_name == "run_bash":
                    console.print(f"  {fn_args.get('command', '')}", style="dim")
                elif fn_name == "search_youtube":
                    mode = fn_args.get("mode", "search")
                    console.print(f"  [{mode}] {fn_args.get('query', '')}", style="dim")
                elif fn_name == "read_file":
                    console.print(f"  {fn_args.get('path', '')}", style="dim")
                elif fn_name == "write_file":
                    console.print(f"  {fn_args.get('path', '')}", style="dim")
                else:
                    console.print()

                # Execute the tool
                handler = TOOL_HANDLERS.get(fn_name)
                if handler:
                    result = handler(fn_args)
                else:
                    result = f"Unknown tool: {fn_name}"

                # Show truncated result
                preview = result[:200] + "..." if len(result) > 200 else result
                console.print(Text(preview, style="dim"))

                # Feed result back to the model
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            # Continue the loop — the model may call more tools or give a final answer
            continue

        # No tool calls — this is the final text response
        response_text = msg.content or ""
        messages.append({"role": "assistant", "content": response_text})

        console.print()
        console.print(Text(" Agent Forge ", style="bold white on green"))
        console.print(Markdown(response_text))
        console.print()
        return response_text

    # If we hit the max rounds, return what we have
    console.print("[dim](max tool rounds reached)[/dim]")
    return ""


def print_header():
    console.print()
    console.print(Panel(
        Text.from_markup(
            "[header]Agent Forge[/header]\n"
            "[dim]An agent that builds other agents[/dim]\n"
            "[dim]Model: openai/gpt-5.2 via OpenRouter[/dim]\n"
            "[dim]Tools: bash, youtube, read/write files[/dim]\n"
            "[dim]Type 'quit' to exit, 'clear' to reset[/dim]"
        ),
        border_style="green",
        padding=(1, 2),
    ))
    console.print()


def main():
    print_header()

    while True:
        try:
            console.print(Text(" You ", style="bold white on cyan"), end="")
            user_input = console.input(" ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input.strip():
            continue
        if user_input.strip().lower() == "quit":
            console.print("[dim]Goodbye.[/dim]")
            break
        if user_input.strip().lower() == "clear":
            messages.clear()
            messages.append({"role": "system", "content": SYSTEM_PROMPT})
            console.clear()
            print_header()
            console.print("[dim]Conversation cleared.[/dim]\n")
            continue

        try:
            run_agent_turn(user_input)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")


if __name__ == "__main__":
    main()
