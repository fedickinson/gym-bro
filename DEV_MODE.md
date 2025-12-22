# Dev Mode - Debugging Features

This document describes the development/debugging features available in Gym Bro.

## Enabling Dev Mode

Add to your `.env` file:

```bash
DEV_MODE=true
```

For Streamlit Cloud, add to your app secrets (Settings → Secrets):

```toml
DEV_MODE = "true"
```

## Features

### 1. Chat Log Export

When dev mode is enabled, the Chat page displays export buttons in the sidebar under "🛠️ Dev Tools".

**Available Formats:**

- **JSON**: Structured data with full metadata, timestamps, agent info, and errors
- **Markdown**: Human-readable conversation log with formatting

**What's Captured:**

```json
{
  "export_timestamp": "2025-12-22T16:00:00",
  "session_metadata": {
    "session_type": "chat",
    "total_messages": 10
  },
  "conversation": [
    {
      "index": 0,
      "role": "user",
      "content": "What should I do today?",
      "timestamp": "2025-12-22T15:30:00"
    },
    {
      "index": 1,
      "role": "assistant",
      "content": "Based on your weekly split...",
      "timestamp": "2025-12-22T15:30:05",
      "agent": "orchestrator"
    }
  ]
}
```

**Metadata Captured:**
- Message role (user/assistant)
- Message content
- Timestamp (ISO format)
- Agent used (if available)
- Error details (if any)
- Tool calls (if any)

### 2. When to Export Logs

**Export logs when:**
- The AI gives unexpected responses
- Conversations don't go as planned
- You encounter errors
- You want to analyze agent behavior
- You need to debug recommendation logic

**Use cases:**
1. **Failed conversations**: Export when the AI doesn't understand or gives wrong recommendations
2. **Error debugging**: Capture the full context when errors occur
3. **Training data**: Use successful conversations to improve prompts
4. **Analysis**: Review agent reasoning and tool usage patterns

### 3. Using Exported Logs

**JSON Format** (best for):
- Programmatic analysis
- Feeding to other AI systems for analysis
- Database storage
- Automated testing

**Markdown Format** (best for):
- Quick human review
- Sharing with team members
- Documentation
- Issue reports

### 4. Example Analysis Workflow

1. Have a problematic conversation
2. Export as JSON
3. Analyze with Claude or other LLM:

```
Analyze this conversation log and identify where the AI coach failed:
[paste JSON]

Questions:
- What did the user expect?
- Where did the conversation go wrong?
- Which agent was involved?
- What tool calls were made?
- How can we improve the response?
```

## Privacy & Security

**Important:**
- Chat logs may contain personal workout data
- Timestamps can reveal usage patterns
- Errors may expose internal system details

**Best Practices:**
- Only enable dev mode in development/testing
- Don't share logs publicly without redacting personal info
- Store exported logs securely
- Disable dev mode in production (set `DEV_MODE=false`)

## File Naming

Exported files use timestamps:
- `gym_bro_chat_log_YYYYMMDD_HHMMSS.json`
- `gym_bro_chat_log_YYYYMMDD_HHMMSS.md`

Example: `gym_bro_chat_log_20251222_163045.json`

## Future Dev Tools

Planned additions:
- Workout log export (similar to chat)
- Agent performance metrics
- Tool usage statistics
- Error rate tracking
- Response time monitoring

---

**Note:** Dev mode is for debugging only. Disable in production to avoid exposing debug information.
