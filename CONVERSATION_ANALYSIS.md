# Conversation Analysis & Improvement System

A systematic approach to analyze failed conversations, identify root causes, and implement improvements.

---

## Overview

This system creates a feedback loop:
1. **Capture** failed conversations
2. **Analyze** what went wrong
3. **Categorize** failure types
4. **Fix** the root cause
5. **Test** that it's fixed
6. **Track** improvements over time

---

## Step 1: Capture Failed Conversations

### When to Capture
- User reports unexpected behavior
- AI gives wrong recommendations
- Agent fails to use correct tools
- Response is off-topic or unhelpful
- System errors occur

### How to Capture
1. Enable dev mode: `DEV_MODE=true`
2. Reproduce the issue in Chat
3. Export conversation as JSON
4. Save to `conversation_logs/failed/YYYYMMDD_description.json`

### Naming Convention
```
conversation_logs/
  failed/
    20251222_wrong_workout_suggestion.json
    20251222_exercise_not_found.json
    20251223_progression_calculation_error.json
  analyzed/
    20251222_wrong_workout_suggestion_ANALYZED.md
  fixed/
    20251222_wrong_workout_suggestion_FIXED.json
```

---

## Step 2: Analyze with LLM

Use Claude or another LLM to systematically analyze the conversation.

### Analysis Prompt Template

```markdown
You are a debugging assistant for an AI fitness coaching system. Analyze this conversation log to identify what went wrong.

## Conversation Log
[paste JSON export]

## System Context
- Router: Classifies intent → routes to appropriate agent
- Query Agent: Answers questions about workout history
- Recommend Agent: Suggests workouts based on weekly split
- Log Agent: Parses and saves workout logs
- Chat Agent: General conversation

## Analysis Framework

### 1. User Intent
- What did the user want?
- What was their actual goal?

### 2. System Response
- What did the system do?
- Which agent handled it?
- What tools were called?

### 3. Failure Point
- Where did it go wrong?
- Was the intent misclassified?
- Did the agent choose the wrong tool?
- Was the tool implementation buggy?
- Did the prompt fail to guide the agent?

### 4. Root Cause
Select ONE primary cause:
- [ ] Intent routing failure
- [ ] Agent prompt issue
- [ ] Tool selection error
- [ ] Tool implementation bug
- [ ] Missing tool/capability
- [ ] Data quality issue
- [ ] LLM reasoning failure

### 5. Proposed Fix
What specific change would fix this?
- Code change? (which file, what change)
- Prompt improvement? (which prompt, how)
- New tool needed? (what tool, why)
- Data fix? (what data needs correction)

### 6. Test Case
How can we verify the fix works?
- Input: [user message]
- Expected: [correct behavior]
- Currently: [actual behavior]

## Output Format
Provide your analysis in the sections above.
```

### Save Analysis
Save LLM response to: `conversation_logs/analyzed/[filename]_ANALYZED.md`

---

## Step 3: Categorize Failure Types

Track failures in `conversation_logs/failure_tracker.csv`:

```csv
Date,Conversation_ID,Category,Subcategory,Root_Cause,Status,PR_Link
2025-12-22,wrong_workout_suggestion,Agent,Recommend,Prompt missing context,Fixed,#123
2025-12-22,exercise_not_found,Tool,Query,Fuzzy matching needed,In Progress,#124
2025-12-23,progression_error,Tool,Calculate,Math bug in progression.py,Fixed,#125
```

### Categories
1. **Intent Routing**
   - Misclassified as wrong agent
   - Should be multi-agent (sequential)
   - Needs new routing rule

2. **Agent Prompts**
   - Insufficient context
   - Missing examples
   - Unclear instructions
   - Conflicting directives

3. **Tool Selection**
   - Agent chose wrong tool
   - Agent didn't use any tools
   - Agent hallucinated instead of using tool

4. **Tool Implementation**
   - Bug in tool logic
   - Edge case not handled
   - Wrong data returned

5. **Missing Capabilities**
   - No tool exists for this task
   - Need new agent type
   - Need new data source

6. **Data Quality**
   - Incomplete workout logs
   - Invalid exercise names
   - Missing metadata

---

## Step 4: Implement Fixes

### Fix Type → Action Mapping

| Root Cause | File(s) to Edit | Validation |
|------------|----------------|------------|
| Intent routing | `src/agents/router.py` | Test with sample inputs |
| Agent prompt | `src/agents/[agent]_agent.py` | Run agent directly |
| Tool selection | Add examples to agent prompt | Test with failed conversation |
| Tool bug | `src/tools/[tool]_tools.py` | Unit test |
| Missing tool | Create new tool in `src/tools/` | Integration test |
| Data quality | Fix data or add validation | Check all logs |

### Implementation Checklist
- [ ] Create branch: `fix/conversation-YYYYMMDD-description`
- [ ] Implement fix
- [ ] Write test that reproduces original failure
- [ ] Verify test now passes
- [ ] Test with original failed conversation (re-run if possible)
- [ ] Update failure tracker: status = "Fixed"
- [ ] Create PR with link to analysis
- [ ] Merge and deploy

---

## Step 5: Test That It's Fixed

### Regression Test
Create `tests/conversation_tests/test_YYYYMMDD_description.py`:

```python
"""
Test for conversation failure: Wrong workout suggestion

Original issue: User asked "What should I do today?" on Friday after doing
Push/Pull/Legs this week. System suggested Push again instead of Upper.

Root cause: Recommend agent not checking full weekly split.

Fix: Updated recommend agent prompt to always check weekly_split_status tool first.
"""

def test_workout_suggestion_after_ppl():
    """Test that correct workout is suggested after Push/Pull/Legs."""
    from src.agents.main import GymBroOrchestrator

    # Setup: Mock weekly split status
    # (Simulate user has done Push, Pull, Legs this week)

    orchestrator = GymBroOrchestrator()
    response = orchestrator.chat("What should I do today?")

    # Should suggest Upper (next in rotation after Legs)
    assert "Upper" in response or "upper" in response
    assert "Push" not in response  # Should NOT suggest Push again
```

### Manual Verification
1. Load the original failed conversation JSON
2. Re-create the scenario (if possible)
3. Verify new response is correct
4. Export new conversation as `conversation_logs/fixed/[filename]_FIXED.json`

---

## Step 6: Track Improvements Over Time

### Metrics to Track

**Failure Rate**:
- Failed conversations / Total conversations
- Track weekly to see improvement

**Fix Rate**:
- Fixed issues / Total reported issues
- Target: 90%+ fix rate

**Category Distribution**:
- Which categories are most common?
- Helps prioritize where to invest effort

**Time to Fix**:
- Days from report to deployment
- Target: < 7 days for critical issues

### Monthly Review
Create `conversation_logs/reviews/YYYY-MM.md`:

```markdown
# Conversation Analysis Review - December 2025

## Summary
- Total conversations: 450
- Failed conversations: 18 (4% failure rate)
- Issues fixed: 15 (83% fix rate)
- Average time to fix: 4.2 days

## Top Issues
1. Exercise name matching (6 occurrences) → Fixed with fuzzy matching
2. Wrong workout suggestions (4 occurrences) → Fixed prompt
3. Progression calculation errors (3 occurrences) → Fixed math bug

## Improvements Made
- Added fuzzy exercise name matching (#124)
- Updated recommend agent prompt with examples (#123)
- Fixed progression velocity calculation (#125)

## Patterns Observed
- Most failures happen with edge cases (unusual workout types)
- New users struggle with natural language logging format
- Need better onboarding for workout logging

## Action Items
- [ ] Add more logging examples to UI
- [ ] Improve error messages for unclear input
- [ ] Create FAQ based on common questions
```

---

## Automated Analysis Script

Create `scripts/analyze_conversation.py`:

```python
"""
Automated conversation analysis using Claude.

Usage:
    python scripts/analyze_conversation.py conversation_logs/failed/20251222_issue.json
"""

import sys
import json
from anthropic import Anthropic

ANALYSIS_PROMPT = """[Analysis prompt from above]"""

def analyze_conversation(log_file: str):
    # Load conversation log
    with open(log_file, 'r') as f:
        log_data = json.load(f)

    # Format for analysis
    log_json = json.dumps(log_data, indent=2)
    prompt = ANALYSIS_PROMPT.replace("[paste JSON export]", log_json)

    # Call Claude for analysis
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    analysis = response.content[0].text

    # Save analysis
    output_file = log_file.replace("failed/", "analyzed/").replace(".json", "_ANALYZED.md")
    with open(output_file, 'w') as f:
        f.write(analysis)

    print(f"Analysis saved to: {output_file}")
    print(f"\n{analysis}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_conversation.py <log_file>")
        sys.exit(1)

    analyze_conversation(sys.argv[1])
```

---

## Quick Reference Workflow

```bash
# 1. Capture failed conversation
# (In app: Chat → Dev Tools → Export JSON)

# 2. Save to failed folder
mv ~/Downloads/gym_bro_chat_log_*.json conversation_logs/failed/20251222_issue_name.json

# 3. Analyze with Claude
python scripts/analyze_conversation.py conversation_logs/failed/20251222_issue_name.json

# 4. Review analysis
cat conversation_logs/analyzed/20251222_issue_name_ANALYZED.md

# 5. Create fix branch
git checkout -b fix/conversation-20251222-issue-name

# 6. Implement fix
# (Edit relevant files based on analysis)

# 7. Create test
# (Add to tests/conversation_tests/)

# 8. Verify fix
pytest tests/conversation_tests/test_20251222_issue_name.py

# 9. Update tracker
echo "2025-12-22,issue_name,Agent,Recommend,Prompt issue,Fixed,#123" >> conversation_logs/failure_tracker.csv

# 10. Commit and PR
git add .
git commit -m "Fix: Issue description from conversation analysis"
git push origin fix/conversation-20251222-issue-name
# Create PR with link to analysis
```

---

## Best Practices

### Do's
✅ Analyze every reported failure systematically
✅ Write regression tests for fixed issues
✅ Update failure tracker immediately
✅ Link PRs to original conversation logs
✅ Review metrics monthly
✅ Share learnings with team

### Don'ts
❌ Don't skip analysis - even for "obvious" fixes
❌ Don't fix without reproducing first
❌ Don't deploy without testing
❌ Don't ignore patterns in failure types
❌ Don't forget to update documentation

---

## Templates

### Issue Template (for GitHub)
```markdown
## Failed Conversation Report

**Date**: 2025-12-22
**Conversation Log**: [link to JSON file]

### User Intent
What the user was trying to do

### Actual Behavior
What the system did instead

### Expected Behavior
What should have happened

### Analysis
[Link to analyzed markdown file or paste key findings]

### Proposed Fix
What needs to change

### Test Case
How to verify it's fixed
```

---

## Tools & Resources

- **Analysis**: Claude Sonnet 4.5 (for conversation analysis)
- **Tracking**: `conversation_logs/failure_tracker.csv`
- **Testing**: pytest for regression tests
- **Metrics**: Generate monthly reviews
- **Automation**: `scripts/analyze_conversation.py`

---

## Example: Full Workflow

See `conversation_logs/examples/` for a complete worked example of the analysis → fix → test cycle.

---

**Remember**: The goal is not zero failures, but continuous improvement. Each failure is a learning opportunity to make the system better.
