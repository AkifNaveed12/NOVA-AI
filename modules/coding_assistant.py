"""
MODULE 26 — Coding Assistant (Agentic Version)
==============================================
A Groq-powered code assistant with its own conversation history, a
code-focused system prompt, and native tool-calling capabilities.
It can navigate, read, write, delete files, and run commands on the local PC.

Used exclusively through the app's Dev tab — never routed to TTS
because code is unreadable when spoken.

Model: llama-3.3-70b-versatile (supports tool calling natively)
"""

import os
import time
import json
import re
import subprocess
import shutil
from typing import Optional, List, Dict, Any
from groq import Groq


_SYSTEM_PROMPT = """You are a senior software engineer assistant embedded in NOVA AI.
Your job is to help the user write, debug, review, and understand code.
You have direct access to the user's local PC filesystem and terminal via tools.

Available tools:
- change_directory: Change the current working directory.
- get_cwd: Get the current working directory.
- list_directory: List files and directories in the current working directory.
- read_file: Read a text file's contents.
- write_file: Write (create or overwrite) a file with specified content.
- delete_file_or_folder: Delete a file or a folder recursively.
- run_command: Run a shell/terminal command in the current working directory.

Rules:
1. Always use Markdown for your responses. When you output code, wrap it in fenced code blocks with the correct language tag.
2. Before writing code in a new path or modifying a file, check if the file or directory exists.
3. Be careful when deleting files. Ask for confirmation if it seems destructive, unless the user explicitly told you to.
4. When writing code, write clean, minimal, production-quality code.
5. All file operations and commands run in the current working directory (CWD) unless absolute paths are specified.
6. The terminal has access to the entire PC. You are running as the user on their Windows PC.
"""

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_cwd",
            "description": "Get the current working directory of the coding assistant.",
            "parameters": {"type": "object", "properties": {}},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "change_directory",
            "description": "Change the current working directory of the assistant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute or relative path to navigate to."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List all files and folders in the current working directory.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file in the current directory or an absolute path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The relative or absolute path of the file to read."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new file or overwrite an existing file with the provided content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The relative or absolute path of the file to write."},
                    "content": {"type": "string", "description": "The content to write into the file."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file_or_folder",
            "description": "Delete a file or a folder (recursively) at the specified path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to delete."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a terminal/shell command in the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command line string to run."}
                },
                "required": ["command"]
            }
        }
    }
]


def _parse_failed_generation(failed_gen: str) -> Optional[List[Dict[str, Any]]]:
    """
    Parses failed_generation from Groq API error response.
    Example raw output: <function=write_file>{"content":"...", "path": "sort.py"}</function>
    """
    pattern = r"<function=(\w+)>(.*?)</function>"
    matches = re.findall(pattern, failed_gen, re.DOTALL)
    if not matches:
        return None

    tool_calls = []
    for idx, (name, args_str) in enumerate(matches):
        try:
            # Clean up and parse JSON arguments
            args = json.loads(args_str)
            tool_calls.append({
                "id": f"call_failed_{int(time.time())}_{idx}",
                "name": name,
                "arguments": args
            })
        except Exception as e:
            print(f"[CodingAssistant] Failed to parse tool JSON directly: {e}")
            # Attempt to recover double-escaped sequences
            try:
                cleaned = args_str.replace("\\\\", "\\")
                args = json.loads(cleaned)
                tool_calls.append({
                    "id": f"call_failed_{int(time.time())}_{idx}",
                    "name": name,
                    "arguments": args
                })
            except Exception:
                pass
    return tool_calls if tool_calls else None


class CodingAssistant:
    HISTORY_WINDOW = 30
    MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 4096

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Complete the setup first.")
        self.client = Groq(api_key=api_key)
        self.history: list = []
        self.cwd = os.getcwd()

    def _execute_tool(self, name: str, args: dict) -> str:
        try:
            if name == "get_cwd":
                return self.cwd

            elif name == "change_directory":
                target = args.get("path", "")
                if not target:
                    return "Error: Path not provided."
                # Resolve relative to current CWD
                full_path = os.path.abspath(os.path.join(self.cwd, target))
                if os.path.exists(full_path) and os.path.isdir(full_path):
                    self.cwd = full_path
                    return f"Changed directory to: {self.cwd}"
                else:
                    return f"Error: Directory '{target}' does not exist."

            elif name == "list_directory":
                if not os.path.exists(self.cwd):
                    return f"Error: Current directory '{self.cwd}' does not exist."
                items = os.listdir(self.cwd)
                result = []
                for item in items:
                    item_path = os.path.join(self.cwd, item)
                    is_dir = os.path.isdir(item_path)
                    type_str = "DIR" if is_dir else "FILE"
                    size_str = "" if is_dir else f" ({os.path.getsize(item_path)} bytes)"
                    result.append(f"[{type_str}] {item}{size_str}")
                return "\n".join(result) if result else "(Empty directory)"

            elif name == "read_file":
                target = args.get("path", "")
                full_path = os.path.abspath(os.path.join(self.cwd, target))
                if not os.path.exists(full_path):
                    return f"Error: File '{target}' does not exist."
                if os.path.isdir(full_path):
                    return f"Error: '{target}' is a directory, not a file."
                # Read text
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()

            elif name == "write_file":
                target = args.get("path", "")
                content = args.get("content", "")
                full_path = os.path.abspath(os.path.join(self.cwd, target))
                # Create parent directories if they don't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Successfully wrote {len(content.encode('utf-8'))} bytes to '{target}'"

            elif name == "delete_file_or_folder":
                target = args.get("path", "")
                full_path = os.path.abspath(os.path.join(self.cwd, target))
                if not os.path.exists(full_path):
                    return f"Error: Path '{target}' does not exist."
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    return f"Successfully deleted directory '{target}' and all its contents."
                else:
                    os.remove(full_path)
                    return f"Successfully deleted file '{target}'."

            elif name == "run_command":
                cmd = args.get("command", "")
                if not cmd:
                    return "Error: Command not provided."
                # Run the command with subprocess
                res = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, cwd=self.cwd, timeout=30
                )
                output = f"Return Code: {res.returncode}\n"
                if res.stdout:
                    output += f"STDOUT:\n{res.stdout}\n"
                if res.stderr:
                    output += f"STDERR:\n{res.stderr}\n"
                return output

            else:
                return f"Error: Unknown tool '{name}'"
        except Exception as e:
            return f"Error executing tool '{name}': {e}"

    def chat(self, user_message: str) -> str:
        # Trim history if it exceeds window
        if len(self.history) >= self.HISTORY_WINDOW:
            self.history = self.history[-(self.HISTORY_WINDOW - 1):]

        self.history.append({"role": "user", "content": user_message})

        # Process up to 5 tool-calling loops
        for loop_count in range(5):
            system_msg = {
                "role": "system",
                "content": _SYSTEM_PROMPT + f"\n\nCURRENT WORKING DIRECTORY: {self.cwd}"
            }
            messages = [system_msg] + self.history

            try:
                completion = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=self.MAX_TOKENS,
                    tools=_TOOLS,
                    tool_choice="auto",
                )

                response_message = completion.choices[0].message

                if response_message.tool_calls:
                    # Append assistant tool call request to history as dict
                    tool_calls_list = []
                    for tc in response_message.tool_calls:
                        tool_calls_list.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        })

                    self.history.append({
                        "role": "assistant",
                        "content": response_message.content,
                        "tool_calls": tool_calls_list
                    })

                    # Execute each tool call requested
                    for tc in response_message.tool_calls:
                        tool_name = tc.function.name
                        tool_args = json.loads(tc.function.arguments)
                        print(f"[CodingAssistant] Tool call: {tool_name} with args {tool_args}")
                        
                        tool_output = self._execute_tool(tool_name, tool_args)
                        
                        # Append tool response
                        self.history.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tool_name,
                            "content": tool_output
                        })
                    
                    # Continue looping to let LLM process the results
                    continue

                else:
                    # Normal text response
                    response_text = response_message.content.strip()
                    self.history.append({"role": "assistant", "content": response_text})
                    return response_text

            except Exception as e:
                # 1. Try to extract failed_generation from e.body (cleanest way)
                failed_gen = None
                body = getattr(e, "body", None)
                if isinstance(body, dict) and "error" in body:
                    failed_gen = body["error"].get("failed_generation")

                # 2. Fallback to parsing str(e) if body parsing failed
                if not failed_gen:
                    err_str = str(e)
                    if "failed_generation" in err_str:
                        # Extract the string inside 'failed_generation': '...'
                        match = re.search(r"'failed_generation':\s*'([^']+)'", err_str)
                        if match:
                            failed_gen = match.group(1)
                            # Unescape string representation
                            try:
                                failed_gen = failed_gen.encode('utf-8').decode('unicode_escape', errors='ignore')
                            except Exception:
                                pass

                if failed_gen:
                    print(f"[CodingAssistant] Detected failed_generation. Attempting recovery...")
                    failed_calls = _parse_failed_generation(failed_gen)
                    if failed_calls:
                        # Append mock assistant tool calls
                        self.history.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tc["name"],
                                        "arguments": json.dumps(tc["arguments"])
                                        if isinstance(tc["arguments"], dict)
                                        else tc["arguments"]
                                    }
                                } for tc in failed_calls
                            ]
                        })

                        # Execute the tool calls
                        for tc in failed_calls:
                            tool_name = tc["name"]
                            tool_args = tc["arguments"]
                            print(f"[CodingAssistant] Executing recovered tool: {tool_name} with args {tool_args}")
                            
                            tool_output = self._execute_tool(tool_name, tool_args)
                            
                            self.history.append({
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "name": tool_name,
                                "content": tool_output
                            })
                        # Continue looping to let LLM process the tool outputs!
                        continue

                # If no failed_generation, handle as normal error
                print(f"[CodingAssistant] Chat Error: {e}")
                if self.history and self.history[-1]["role"] == "user":
                    self.history.pop()
                return f"Error during code assistance: {e}"

        return "Agent stopped. The request required too many consecutive file/terminal operations."


    def reset(self):
        self.history = []
        return "Conversation cleared."


# ── Lazy singleton — created only after setup is complete ─────────
_assistant: Optional[CodingAssistant] = None

def get_coding_assistant() -> CodingAssistant:
    """Returns the singleton, creating it on first call. Raises if GROQ_API_KEY not set."""
    global _assistant
    if _assistant is None:
        _assistant = CodingAssistant()
    return _assistant

def reset_coding_assistant():
    """Force re-creation on next call (e.g., after a new Groq key is saved via setup)."""
    global _assistant
    _assistant = None
