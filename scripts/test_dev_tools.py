"""
Test Dev Tools - Export functionality.
"""

import sys
sys.path.insert(0, '/Users/franklindickinson/Projects/gym-bro')

from src.dev_tools import (
    is_dev_mode,
    export_chat_logs,
    format_chat_logs_as_json,
    format_chat_logs_as_markdown,
    generate_filename
)

print("=" * 80)
print("DEV TOOLS TEST")
print("=" * 80)

# Test 1: Check dev mode
print(f"\n1. Dev Mode Status: {is_dev_mode()}")

# Test 2: Create sample chat history
sample_chat = [
    {
        "role": "user",
        "content": "What should I do today?",
        "timestamp": "2025-12-22T16:00:00"
    },
    {
        "role": "assistant",
        "content": "Based on your weekly split, I recommend Pull workout today.",
        "timestamp": "2025-12-22T16:00:05",
        "agent": "orchestrator"
    },
    {
        "role": "user",
        "content": "How many workouts did I do this month?",
        "timestamp": "2025-12-22T16:01:00"
    },
    {
        "role": "assistant",
        "content": "Sorry, I encountered an error: Database connection failed",
        "timestamp": "2025-12-22T16:01:05",
        "agent": "query_agent",
        "error": "Database connection failed"
    }
]

print("\n2. Sample Chat History:")
print(f"   Total messages: {len(sample_chat)}")

# Test 3: Export as JSON
print("\n3. JSON Export:")
json_export = format_chat_logs_as_json(sample_chat, metadata={"test": True})
print(f"   Length: {len(json_export)} characters")
print(f"   First 200 chars: {json_export[:200]}...")

# Test 4: Export as Markdown
print("\n4. Markdown Export:")
md_export = format_chat_logs_as_markdown(sample_chat, metadata={"test": True})
print(f"   Length: {len(md_export)} characters")
print(f"   First 300 chars:")
print(md_export[:300])

# Test 5: Filename generation
print("\n5. Filename Generation:")
print(f"   JSON: {generate_filename('json')}")
print(f"   MD: {generate_filename('md')}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

# Save sample exports
with open("/tmp/sample_chat_export.json", "w") as f:
    f.write(json_export)
print(f"\nSample JSON saved to: /tmp/sample_chat_export.json")

with open("/tmp/sample_chat_export.md", "w") as f:
    f.write(md_export)
print(f"Sample Markdown saved to: /tmp/sample_chat_export.md")
