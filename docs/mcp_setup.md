# MCP Setup for Gym Bro

## What are MCPs?

**Model Context Protocol (MCP)** servers extend Claude's capabilities with specialized tools. They provide domain-specific functionality that goes beyond Claude's base capabilities.

---

## MCPs Currently Configured

Your Claude Desktop already has these MCPs configured:

### 1. **Time MCP** ✅ HIGHLY USEFUL
- **Status**: Configured and ready
- **Use cases for Gym Bro**:
  - Weekly split date calculations (start/end of week)
  - "Last 30 days" date range queries
  - Workout frequency analysis
  - Progress tracking over time periods
- **When to use**: Any date/time operations in weekly split or query tools

### 2. **Coffee Bean MCP** (Custom)
- **Status**: Configured
- **Relevance**: Not needed for Gym Bro

### 3. **Playwright MCP**
- **Status**: Configured
- **Relevance**: Not needed for Gym Bro (no web scraping needed)

### 4. **Task Master MCP**
- **Status**: Configured
- **Relevance**: Not needed for Gym Bro

---

## MCPs NOT Needed for Gym Bro

### Filesystem MCP ❌ NOT NEEDED
**Why not needed**: Claude Code has native Read/Write/Edit tools that work perfectly for JSON operations. Adding a filesystem MCP would be redundant.

**What we're using instead**:
- `Read` tool - Read JSON files
- `Write` tool - Create/overwrite JSON files
- `Edit` tool - Modify specific parts of files
- Native tools are faster and more integrated with Claude Code

---

## MCP Usage in Gym Bro

### Current Usage: Time MCP

The Time MCP will be useful in these areas:

#### Weekly Split Tracking
```python
# In recommend_tools.py
def get_weekly_split_status():
    # Get Monday of current week
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Could use Time MCP for more complex date operations
    # - Find "2 weeks ago Monday"
    # - Calculate "end of next week"
    # - etc.
```

#### Date Range Queries
```python
# In query_tools.py
def search_workouts(query: str, days: int = 30):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Time MCP could help with:
    # - "Last month" (accounting for different month lengths)
    # - "This quarter"
    # - "Last 3 Mondays"
```

### Example Time MCP Tool Usage

If you need to use the Time MCP tools in Phase 2+, they would look like:

```python
# First, load the MCP tools
from claude_code import MCPSearch

# Find available time tools
time_tools = MCPSearch(query="time")

# Then use them in your agents/chains
# Example: Get current week start/end
```

---

## Recommendations

### For Phase 2 (Agents & Chains)
- ✅ **Use Time MCP** if you need complex date calculations
- ✅ **Use native Read/Write** for all JSON operations
- ❌ **Don't install filesystem MCP** - it's redundant

### For Phase 3+ (Advanced Features)
Consider these MCPs if you add new features:

- **GitHub MCP**: If you want to log workouts via GitHub commits
- **Google Calendar MCP**: If you want to integrate with user's calendar
- **Weather MCP**: If you want to suggest indoor/outdoor workouts based on weather

---

## How to Add New MCPs (If Needed)

If you want to add MCPs in the future:

1. **Edit Claude Desktop config**:
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Add MCP server**:
   ```json
   {
     "mcpServers": {
       "existing-mcp": { ... },
       "new-mcp": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-name"]
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Load MCP tools in code**:
   ```python
   from claude_code import MCPSearch
   tools = MCPSearch(query="select:mcp__name__tool")
   ```

---

## Summary

✅ **Time MCP**: Already configured, useful for date operations
✅ **Native File Tools**: Perfect for JSON operations
❌ **Filesystem MCP**: Not needed (would be redundant)
💡 **Future MCPs**: Consider GitHub, Calendar, Weather for advanced features

**You're all set for Phase 2!** The MCPs you have are sufficient for building the core Gym Bro functionality.
