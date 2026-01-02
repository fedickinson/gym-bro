# LangGraph Workflow Pattern

**Reference**: `/Users/franklindickinson/Projects/gym-bro/src/agents/log_graph.py`

## Complete Example: LogGraph

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

class LogWorkoutState(TypedDict):
    """State for workout logging workflow."""
    raw_notes: str
    parsed_workout: dict | None
    user_feedback: Literal["approve", "edit", "cancel"] | None
    edits: dict | None
    saved: bool
    response: str | None

# Node 1: Parse Notes
def parse_notes(state: LogWorkoutState) -> LogWorkoutState:
    """Extract workout structure from raw notes using Claude."""
    # Use LLM to parse raw_notes into structured format
    parsed = _parse_with_llm(state["raw_notes"])
    state["parsed_workout"] = parsed
    return state

# Node 2: Confirm with User
def confirm_with_user(state: LogWorkoutState) -> LogWorkoutState:
    """Generate confirmation message for user review."""
    workout = state["parsed_workout"]
    msg = f"I parsed your workout as:\\n{format_workout(workout)}\\nApprove?"
    state["response"] = msg
    return state

# Node 3: Save Workout
def save_workout(state: LogWorkoutState) -> LogWorkoutState:
    """Save approved workout to database."""
    from src.data import add_log
    log_id = add_log(state["parsed_workout"])
    state["saved"] = True
    state["response"] = f"Saved workout {log_id}"
    return state

# Routing Logic
def route_after_confirm(state: LogWorkoutState) -> str:
    """Route based on user feedback."""
    feedback = state.get("user_feedback")
    if feedback == "approve":
        return "save"
    elif feedback == "edit":
        return "parse"  # Re-parse with edits
    else:
        return "end"  # Cancel

# Build Graph
def build_log_graph():
    """Construct the logging workflow graph."""
    workflow = StateGraph(LogWorkoutState)

    workflow.add_node("parse_notes", parse_notes)
    workflow.add_node("confirm_with_user", confirm_with_user)
    workflow.add_node("save_workout", save_workout)

    workflow.set_entry_point("parse_notes")
    workflow.add_edge("parse_notes", "confirm_with_user")
    workflow.add_conditional_edges("confirm_with_user", route_after_confirm, {
        "save": "save_workout",
        "parse": "parse_notes",
        "end": END
    })
    workflow.add_edge("save_workout", END)

    return workflow.compile()
```

## Key Components

1. **State Type**: TypedDict defines all state fields
2. **Node Functions**: Each node takes state, returns state
3. **Routing Functions**: Conditional logic for branching
4. **Graph Builder**: Assembles nodes and edges

## Human-in-the-Loop

Use `workflow.compile(interrupt_before=["confirm_with_user"])` to pause for user input.

## State Management Best Practices

- Keep state flat (avoid deep nesting)
- Use TypedDict for type safety
- Echo previous state in node returns
- Handle None/missing fields gracefully
