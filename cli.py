#!/usr/bin/env python3
"""CLI entry point for the Termux AI Agent."""

import argparse
import glob
import os
import readline
import sys
from pathlib import Path

from agent.config import Config
from agent.core import Agent


def cmd_process(args: argparse.Namespace) -> int:
    """Process a single audio file."""
    config = Config(args.config)
    agent = Agent(config)

    print(f"Processing: {args.file}")
    result = agent.process(args.file)

    print(f"\nStatus: {result.status}")
    if result.transcription:
        print(f"\n--- Transcription ---\n{result.transcription}")
    if result.translation:
        print(f"\n--- Translation (Tamil) ---\n{result.translation}")
    if result.summary:
        print(f"\n--- Summary ---\n{result.summary}")
    if result.error:
        print(f"\nError: {result.error}", file=sys.stderr)
        return 1

    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    """Process all .opus files in a directory."""
    config = Config(args.config)
    agent = Agent(config)

    print(f"Batch processing: {args.directory}")
    results = agent.process_batch(args.directory)

    success = 0
    errors = 0
    for result in results:
        if result.status == "complete":
            success += 1
            print(f"  OK: {result.filename}")
        else:
            errors += 1
            print(f"  FAIL: {result.filename} - {result.error}")

    print(f"\nCompleted: {success} success, {errors} errors")
    return 1 if errors > 0 else 0


def cmd_report(args: argparse.Namespace) -> int:
    """Display a report of all processed files."""
    config = Config(args.config)
    agent = Agent(config)
    print(agent.get_report())
    return 0


class _Completer:
    """Tab completer for interactive mode commands and file paths."""

    COMMANDS = ["process", "batch", "report", "config", "help", "quit", "exit"]

    def __init__(self) -> None:
        self._matches: list[str] = []

    def complete(self, text: str, state: int) -> str | None:
        if state == 0:
            line = readline.get_line_buffer().lstrip()
            if " " in line:
                # Complete file/directory paths after a command
                self._matches = glob.glob(text + "*")
            else:
                # Complete command names
                self._matches = [c for c in self.COMMANDS if c.startswith(text)]
        if state < len(self._matches):
            return self._matches[state]
        return None


def cmd_interactive(args: argparse.Namespace) -> int:
    """Start an interactive session."""
    config = Config(args.config)
    agent = Agent(config)

    # Set up readline for tab completion and history
    completer = _Completer()
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")

    # Persistent history file
    history_file = os.path.expanduser("~/.termux_ai_agent_history")
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    print("Termux AI Agent - Interactive Mode")
    print("Type 'help' for commands, 'quit' to exit.")
    print("Tab completion is available for commands and file paths.\n")

    while True:
        try:
            user_input = input("agent> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            readline.write_history_file(history_file)
            break

        if not user_input:
            continue

        if user_input in ("quit", "exit", "q"):
            print("Goodbye!")
            readline.write_history_file(history_file)
            break

        if user_input == "help":
            print("Commands:")
            print("  process <file>    - Process an audio file")
            print("  batch <dir>       - Process all .opus files in directory")
            print("  report            - Show tracking report")
            print("  config            - Show current configuration")
            print("  help              - Show this help")
            print("  quit              - Exit")
            continue

        if user_input == "config":
            import yaml
            print(yaml.dump(config.as_dict(), default_flow_style=False))
            continue

        if user_input == "report":
            print(agent.get_report())
            continue

        parts = user_input.split(maxsplit=1)
        command = parts[0]

        if command == "process" and len(parts) == 2:
            file_path = parts[1]
            if not Path(file_path).exists():
                print(f"File not found: {file_path}")
                continue

            result = agent.process(file_path)
            print(f"Status: {result.status}")
            if result.transcription:
                print(f"Transcription: {result.transcription[:200]}")
            if result.translation:
                print(f"Translation: {result.translation[:200]}")
            if result.summary:
                print(f"Summary: {result.summary}")
            if result.error:
                print(f"Error: {result.error}")

        elif command == "batch" and len(parts) == 2:
            dir_path = parts[1]
            if not Path(dir_path).is_dir():
                print(f"Not a directory: {dir_path}")
                continue

            results = agent.process_batch(dir_path)
            for r in results:
                status_icon = "OK" if r.status == "complete" else "FAIL"
                print(f"  [{status_icon}] {r.filename}")

        else:
            print(f"Unknown command: {user_input}. Type 'help' for commands.")

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Show current configuration."""
    import yaml

    config = Config(args.config)
    print(yaml.dump(config.as_dict(), default_flow_style=False))
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Termux AI Agent - Lightweight agentic AI for Android",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # process
    p_process = subparsers.add_parser("process", help="Process a single audio file")
    p_process.add_argument("file", help="Path to .opus audio file")
    p_process.set_defaults(func=cmd_process)

    # batch
    p_batch = subparsers.add_parser("batch", help="Process all .opus files in a directory")
    p_batch.add_argument("directory", help="Directory containing .opus files")
    p_batch.set_defaults(func=cmd_batch)

    # report
    p_report = subparsers.add_parser("report", help="Display tracking report")
    p_report.set_defaults(func=cmd_report)

    # interactive
    p_interactive = subparsers.add_parser("interactive", help="Start interactive mode")
    p_interactive.set_defaults(func=cmd_interactive)

    # config
    p_config = subparsers.add_parser("config", help="Show current configuration")
    p_config.set_defaults(func=cmd_config)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
