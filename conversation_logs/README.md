# Conversation Logs Directory

This directory tracks failed conversations for systematic analysis and improvement.

## Directory Structure

```
conversation_logs/
├── failed/           # Failed conversation exports (JSON)
├── analyzed/         # Analysis results (Markdown)
├── fixed/            # Fixed conversation re-runs (JSON)
├── examples/         # Example workflows
├── reviews/          # Monthly review reports
└── failure_tracker.csv  # Central tracking spreadsheet
```

## Quick Start

### 1. Export Failed Conversation
When something goes wrong in the Chat:
1. Enable dev mode: `DEV_MODE=true` in `.env`
2. Export conversation as JSON
3. Save to `failed/` with descriptive name:
   ```bash
   mv ~/Downloads/gym_bro_chat_log_*.json conversation_logs/failed/20251222_wrong_workout_suggestion.json
   ```

### 2. Analyze with Claude
```bash
python scripts/analyze_conversation.py conversation_logs/failed/20251222_wrong_workout_suggestion.json
```

This will:
- Load the conversation
- Send to Claude for analysis
- Save analysis to `analyzed/20251222_wrong_workout_suggestion_ANALYZED.md`
- Print next steps

### 3. Review Analysis
```bash
cat conversation_logs/analyzed/20251222_wrong_workout_suggestion_ANALYZED.md
```

The analysis includes:
- User intent
- System response
- Failure point
- Root cause
- Proposed fix
- Test case

### 4. Implement Fix
1. Create branch: `git checkout -b fix/conversation-20251222-description`
2. Make changes based on analysis
3. Write test case
4. Verify fix works

### 5. Update Tracker
```bash
echo "2025-12-22,wrong_workout_suggestion,Agent,Recommend,Prompt missing context,Fixed,#123,Suggested Push after already doing Push" >> conversation_logs/failure_tracker.csv
```

### 6. Test & Deploy
```bash
pytest tests/conversation_tests/
git commit -m "Fix: Wrong workout suggestion after PPL"
git push origin fix/conversation-20251222-description
# Create PR
```

## Example Workflow

See `examples/example_wrong_workout_suggestion.json` for a sample failed conversation.

Run the example:
```bash
python scripts/analyze_conversation.py conversation_logs/examples/example_wrong_workout_suggestion.json
```

## Failure Categories

Track in `failure_tracker.csv`:

| Category | Subcategory | Common Causes |
|----------|-------------|---------------|
| Intent Routing | Misclassification | Router prompt needs improvement |
| Agent | Query | Tool selection, prompt issues |
| Agent | Recommend | Missing context, wrong tool |
| Tool | Implementation | Bugs, edge cases |
| Tool | Missing | New capability needed |
| Data | Quality | Incomplete logs, validation |

## Monthly Reviews

Create reviews in `reviews/YYYY-MM.md`:
- Total conversations
- Failure rate
- Common issues
- Fixes deployed
- Trends and patterns

## Best Practices

✅ **Do:**
- Analyze every reported failure
- Write regression tests
- Update tracker immediately
- Link PRs to analysis

❌ **Don't:**
- Skip analysis for "obvious" fixes
- Fix without reproducing
- Deploy without testing
- Ignore failure patterns

## Tools

- `scripts/analyze_conversation.py` - Automated analysis
- `failure_tracker.csv` - Central tracking
- `CONVERSATION_ANALYSIS.md` - Full documentation

## Privacy

⚠️ **Conversation logs may contain personal data**
- Only share analysis (not raw logs) publicly
- Redact personal info before sharing
- Keep logs in private repo

---

For detailed documentation, see: [CONVERSATION_ANALYSIS.md](../CONVERSATION_ANALYSIS.md)
