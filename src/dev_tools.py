"""
Development Tools - Debugging utilities for development.

Features:
- Chat conversation log export
- System diagnostics
- Debug mode checks
"""

import os
import json
from datetime import datetime
from typing import Optional


def is_dev_mode() -> bool:
    """Check if dev mode is enabled via environment variable."""
    return os.getenv("DEV_MODE", "false").lower() == "true"


def export_chat_logs(chat_history: list, metadata: Optional[dict] = None) -> dict:
    """
    Export chat conversation logs for debugging.

    Args:
        chat_history: List of chat messages from session state
        metadata: Optional metadata (timestamp, session info, etc.)

    Returns:
        Dict with formatted logs ready for JSON export
    """
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "session_metadata": metadata or {},
        "total_messages": len(chat_history),
        "conversation": []
    }

    # Process each message
    for i, msg in enumerate(chat_history):
        message_data = {
            "index": i,
            "role": msg.get("role", "unknown"),
            "content": msg.get("content", ""),
            "timestamp": msg.get("timestamp", "unknown")
        }

        # Add any additional metadata if present
        if "agent" in msg:
            message_data["agent"] = msg["agent"]

        if "tool_calls" in msg:
            message_data["tool_calls"] = msg["tool_calls"]

        if "error" in msg:
            message_data["error"] = msg["error"]

        export_data["conversation"].append(message_data)

    return export_data


def format_chat_logs_as_json(chat_history: list, metadata: Optional[dict] = None) -> str:
    """
    Format chat logs as pretty-printed JSON string.

    Args:
        chat_history: List of chat messages
        metadata: Optional metadata

    Returns:
        JSON string ready for download
    """
    export_data = export_chat_logs(chat_history, metadata)
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def format_chat_logs_as_markdown(chat_history: list, metadata: Optional[dict] = None) -> str:
    """
    Format chat logs as Markdown for easier reading.

    Args:
        chat_history: List of chat messages
        metadata: Optional metadata

    Returns:
        Markdown string ready for download
    """
    export_data = export_chat_logs(chat_history, metadata)

    md_lines = [
        "# Chat Conversation Log",
        "",
        f"**Exported:** {export_data['export_timestamp']}",
        f"**Total Messages:** {export_data['total_messages']}",
        ""
    ]

    if export_data["session_metadata"]:
        md_lines.append("## Session Metadata")
        md_lines.append("```json")
        md_lines.append(json.dumps(export_data["session_metadata"], indent=2))
        md_lines.append("```")
        md_lines.append("")

    md_lines.append("## Conversation")
    md_lines.append("")

    for msg in export_data["conversation"]:
        role = msg["role"]
        content = msg["content"]
        timestamp = msg.get("timestamp", "unknown")

        # Message header
        if role == "user":
            md_lines.append(f"### 👤 User (Message {msg['index']})")
        else:
            md_lines.append(f"### 🤖 Assistant (Message {msg['index']})")

        md_lines.append(f"**Time:** {timestamp}")

        # Add agent info if present
        if "agent" in msg:
            md_lines.append(f"**Agent:** {msg['agent']}")

        md_lines.append("")
        md_lines.append(content)
        md_lines.append("")

        # Add tool calls if present
        if "tool_calls" in msg and msg["tool_calls"]:
            md_lines.append("**Tool Calls:**")
            md_lines.append("```json")
            md_lines.append(json.dumps(msg["tool_calls"], indent=2))
            md_lines.append("```")
            md_lines.append("")

        # Add errors if present
        if "error" in msg:
            md_lines.append(f"**❌ Error:** {msg['error']}")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

    return "\n".join(md_lines)


def generate_filename(extension: str = "json") -> str:
    """
    Generate a filename for log export.

    Args:
        extension: File extension (json or md)

    Returns:
        Filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"gym_bro_chat_log_{timestamp}.{extension}"
