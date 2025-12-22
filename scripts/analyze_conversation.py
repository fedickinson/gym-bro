"""
Automated Conversation Analysis using Claude.

This script analyzes failed conversation logs to identify root causes
and suggest fixes.

Usage:
    python scripts/analyze_conversation.py conversation_logs/failed/20251222_issue.json
"""

import sys
import os
import json
from pathlib import Path
from anthropic import Anthropic

ANALYSIS_PROMPT = """You are a debugging assistant for an AI fitness coaching system called "Gym Bro". Analyze this conversation log to identify what went wrong.

## Conversation Log
{conversation_json}

## System Context

**Architecture:**
- **Router**: Classifies user intent → routes to appropriate agent
- **Query Agent (ReAct)**: Answers questions about workout history using tools
- **Recommend Agent (ReAct)**: Suggests workouts based on weekly split using tools
- **Log Agent (LangGraph)**: Parses and saves workout logs with human confirmation
- **Chat Agent (Simple Chain)**: General conversation without tools

**Available Tools:**
- Query Tools: `search_workouts`, `get_exercise_history`, `calculate_progression`
- Recommend Tools: `get_weekly_split_status`, `suggest_next_workout`, `get_workout_template`
- Adaptive Tools: `analyze_workout_patterns`, `check_progression_status`

**Data Model:**
- Workouts stored as JSON with exercises, sets, reps, weights
- Weekly split tracking (Push/Pull/Legs/Upper/Lower)
- 128+ historical workouts available for pattern analysis

---

## Analysis Framework

### 1. User Intent
- What did the user want to accomplish?
- What was their actual goal?
- Is this a common use case?

### 2. System Response
- What did the system do?
- Which agent handled the request?
- What tools were called (if any)?
- Was the response helpful?

### 3. Failure Point
Identify WHERE it went wrong:
- Was the intent misclassified by the router?
- Did the agent choose the wrong tool?
- Did a tool return incorrect data?
- Did the agent misinterpret the tool results?
- Was the prompt insufficient to guide the agent?
- Did the LLM hallucinate instead of using tools?

### 4. Root Cause
Select ONE primary root cause:
- [ ] **Intent routing failure** - Router sent to wrong agent
- [ ] **Agent prompt issue** - Prompt missing context/examples/instructions
- [ ] **Tool selection error** - Agent chose wrong tool or no tool
- [ ] **Tool implementation bug** - Tool has a bug or edge case
- [ ] **Missing tool/capability** - No tool exists for this task
- [ ] **Data quality issue** - Incomplete/incorrect data
- [ ] **LLM reasoning failure** - Model failed to reason correctly
- [ ] **User input unclear** - User request was ambiguous

### 5. Proposed Fix
What specific change would fix this? Be concrete:
- **If code change**: Which file? What exact change?
- **If prompt improvement**: Which agent prompt? What to add/change?
- **If new tool needed**: What tool? What should it do?
- **If data fix**: What data needs correction?

### 6. Test Case
How can we verify the fix works?
```python
# Input
user_input = "..."

# Expected behavior
expected = "..."

# Current behavior (broken)
actual = "..."
```

---

## Output Format

Provide your analysis in the following sections:

```markdown
# Conversation Analysis

## Summary
[1-2 sentence summary of the issue]

## User Intent
[What the user wanted]

## System Response
[What the system did, which agent, which tools]

## Failure Point
[Where it went wrong]

## Root Cause
[Selected category and explanation]

## Proposed Fix

**File(s) to modify:**
- `path/to/file.py`

**Changes needed:**
```python
# Before
...

# After
...
```

**Why this fixes it:**
[Explanation]

## Test Case

```python
def test_fix_for_issue():
    \"\"\"Test that [specific issue] is fixed.\"\"\"
    # Test code
```

## Priority
[High/Medium/Low based on impact and frequency]

## Estimated Effort
[Hours/Days to implement fix]
```
"""


def load_conversation_log(log_file: str) -> dict:
    """Load and validate conversation log file."""
    if not os.path.exists(log_file):
        raise FileNotFoundError(f"Log file not found: {log_file}")

    with open(log_file, 'r') as f:
        log_data = json.load(f)

    # Validate structure
    if "conversation" not in log_data:
        raise ValueError("Invalid log format: missing 'conversation' field")

    return log_data


def analyze_with_claude(log_data: dict) -> str:
    """Analyze conversation using Claude."""
    # Format conversation as JSON
    conversation_json = json.dumps(log_data, indent=2)

    # Build prompt
    prompt = ANALYSIS_PROMPT.format(conversation_json=conversation_json)

    # Call Claude
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def save_analysis(analysis: str, input_file: str) -> str:
    """Save analysis to analyzed folder."""
    input_path = Path(input_file)
    filename = input_path.stem  # Filename without extension

    # Create output path
    output_dir = Path("conversation_logs/analyzed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{filename}_ANALYZED.md"

    with open(output_file, 'w') as f:
        f.write(analysis)

    return str(output_file)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_conversation.py <log_file>")
        print("\nExample:")
        print("  python scripts/analyze_conversation.py conversation_logs/failed/20251222_wrong_suggestion.json")
        sys.exit(1)

    log_file = sys.argv[1]

    print("=" * 80)
    print("CONVERSATION ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing: {log_file}")
    print("This may take 30-60 seconds...\n")

    try:
        # Load conversation
        log_data = load_conversation_log(log_file)
        print(f"✓ Loaded {log_data['total_messages']} messages")

        # Analyze with Claude
        print("✓ Analyzing with Claude...")
        analysis = analyze_with_claude(log_data)

        # Save analysis
        output_file = save_analysis(analysis, log_file)
        print(f"✓ Analysis saved to: {output_file}")

        print("\n" + "=" * 80)
        print("ANALYSIS RESULT")
        print("=" * 80)
        print(analysis)

        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("1. Review analysis above")
        print(f"2. Read full analysis: cat {output_file}")
        print("3. Create fix branch: git checkout -b fix/conversation-YYYYMMDD-description")
        print("4. Implement proposed fix")
        print("5. Write test case")
        print("6. Update failure_tracker.csv")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
