# LangGraph Workflow Explained

## The Workout Logging Problem

**User Input**: "Did push today - bench 135x8x3, overhead 95x8x3"

**What needs to happen** (can't be done with chains or agents!):

```
                    START
                      ↓
            ┌─────────────────┐
            │  parse_notes    │  ← LLM extracts structured data
            │  (AI extracts)  │
            └────────┬─────────┘
                     ↓
            ┌─────────────────┐
            │  show_preview   │  ← Show to user for confirmation
            │  (Human sees)   │
            └────────┬─────────┘
                     ↓
            ┌─────────────────┐
            │  WAIT FOR USER  │  ← Graph PAUSES here!
            │  (Human input)  │
            └────────┬─────────┘
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    [approve]     [edit]      [cancel]
        ↓            ↓            ↓
    ┌──────┐    ┌────────┐    ┌──────┐
    │ save │    │ re-parse│   │ abort│
    └──┬───┘    └───┬────┘    └──┬───┘
       ↓            │            ↓
    ┌──────┐        │         ┌──────┐
    │respond│       │         │respond│
    └──┬───┘        │         └──┬───┘
       ↓            ↓            ↓
      END ←─────────┴───────────END
```

## Why Each Pattern Fails

### ❌ Chain (Too Simple)
```
Input → Parse → Save → Output
```
**Problem**: Can't wait for human confirmation! It just goes straight through.

**Analogy**: Like a factory assembly line - once it starts, it can't stop mid-way for your approval!

### ❌ Agent (Too Autonomous)
```
Think → "Should I save this?" → Decides → Saves
```
**Problem**: Agent makes the decision, not the human!

**Analogy**: Like a robot chef that decides the recipe is done - you don't get to taste and approve first!

### ✅ Graph (Perfect!)
```
Parse → Show → WAIT → Human decides → Branch accordingly
```
**Perfect**: Pauses for human input, branches based on choice!

**Analogy**: Like a GPS navigation - it shows you the route, waits for you to confirm, then guides you based on which turn you take!

---

## LangGraph State Machine

### The State (Shared Memory)

Think of State like a **clipboard** that gets passed between nodes:

```python
class LogWorkoutState(TypedDict):
    # Raw input from user
    raw_notes: str  # "bench 135x8x3, overhead 95x8x3"

    # Parsed structure
    parsed_workout: dict | None  # {exercises: [...], date: "...", ...}

    # User feedback
    user_choice: str | None  # "approve" | "edit" | "cancel"
    edits: str | None  # "Actually it was 145 lbs"

    # Results
    saved: bool  # Did we save it?
    response: str  # What to tell the user
```

**Analogy**: Like a form that gets filled out as it moves between departments:
- Reception fills out name
- Accounting fills out payment
- Manager fills out approval
- Each person adds their part to the same form!

### The Nodes (Processing Steps)

Each node is a **function** that reads the state, does work, updates the state:

```python
def parse_notes(state: LogWorkoutState) -> LogWorkoutState:
    """
    Node 1: Parse the user's notes into structured data.

    Input: state["raw_notes"] = "bench 135x8x3"
    Output: state["parsed_workout"] = {
        "exercises": [
            {"name": "Bench Press", "sets": [...]}
        ]
    }
    """
    # Use LLM to extract structure
    ...
    return updated_state


def confirm(state: LogWorkoutState) -> LogWorkoutState:
    """
    Node 2: Show preview and wait for user.

    This is where the graph PAUSES!
    """
    # Show preview
    # Graph pauses here
    # User input resumes the graph
    ...
    return updated_state


def save(state: LogWorkoutState) -> LogWorkoutState:
    """
    Node 3: Save to database.

    Only called if user approved!
    """
    # Save to workout_logs.json
    state["saved"] = True
    return state
```

### The Edges (Routing Logic)

Edges decide **which node to go to next**:

```python
def should_save(state: LogWorkoutState) -> str:
    """
    Conditional edge: Where to go after confirmation?

    Returns:
    - "save" if user approved
    - "parse_notes" if user wants to edit
    - "cancel" if user wants to abort
    """
    choice = state["user_choice"]

    if choice == "approve":
        return "save"
    elif choice == "edit":
        return "parse_notes"  # Loop back!
    else:
        return "cancel"
```

**Analogy**: Like traffic lights at an intersection:
- Green (approve) → Go to "save" road
- Yellow (edit) → Go back to "parse" road
- Red (cancel) → Go to "cancel" road

---

## The Human-in-the-Loop Pattern

### How Graph Pauses

```python
# Build the graph
graph = StateGraph(LogWorkoutState)

# Add nodes
graph.add_node("parse", parse_notes)
graph.add_node("confirm", confirm)
graph.add_node("save", save)

# Add edges
graph.add_edge("parse", "confirm")  # Always go here
graph.add_conditional_edge(
    "confirm",
    should_save,  # Decide where to go
    {
        "save": "save",
        "edit": "parse",
        "cancel": END
    }
)

# Make it wait for human input after confirm
graph.add_edge("confirm", "interrupt")  # PAUSE HERE!
```

**What happens**:

1. User: "bench 135x8"
2. Graph runs "parse" → Creates structured data
3. Graph runs "confirm" → Shows preview
4. **Graph PAUSES** 🛑 (interrupt point)
5. Human sees preview: "Bench Press: 135 lbs × 8 reps. Correct?"
6. Human responds: "yes" / "edit" / "cancel"
7. **Graph RESUMES** ▶️ with user's choice
8. Graph runs appropriate next node

**Analogy**: Like a video game checkpoint:
- Game saves progress
- Waits for you to press a button
- Continues based on what you pressed

---

## Comparison Chart

| Feature | Chain | Agent | Graph |
|---------|-------|-------|-------|
| **Pause mid-process** | ❌ No | ❌ No | ✅ Yes |
| **Branch based on input** | ❌ No | ⚠️ Limited | ✅ Yes |
| **Loop back to earlier step** | ❌ No | ✅ Yes | ✅ Yes |
| **Human confirmation** | ❌ No | ❌ No | ✅ Yes |
| **Complex workflows** | ❌ No | ⚠️ Maybe | ✅ Yes |
| **Speed** | ⚡ Fast | 🐌 Slow | 🐌 Slow |
| **Complexity** | 🟢 Simple | 🟡 Medium | 🔴 Complex |

---

## When to Use Each

### Use a CHAIN when:
- Linear flow (A → B → C)
- No decisions needed
- Fast execution important
- Example: Chat, Admin confirm

### Use an AGENT when:
- Need to use tools
- Variable complexity
- Autonomous decision making OK
- Example: Query data, Plan workouts

### Use a GRAPH when:
- Multi-step workflow
- Human input required mid-process
- Branching logic
- Can go back to earlier steps
- Example: **Workout logging!**

---

## The Power of LangGraph

**What makes it special**:

1. **State Management**: Persistent memory across steps
2. **Human-in-the-Loop**: Pause and wait for user
3. **Conditional Routing**: Go different directions based on data
4. **Cycles**: Loop back to earlier nodes
5. **Interrupts**: Breakpoints for user input

**Real-world use cases**:
- Customer support (escalate to human)
- Medical diagnosis (doctor confirms AI suggestion)
- Legal review (lawyer approves AI draft)
- **Workout logging** (user confirms parsed data)

---

## Next Steps

We'll build the actual LangGraph workflow for workout logging:

1. Define the State schema
2. Build parse_notes node (LLM extraction)
3. Build confirm node (show preview)
4. Build save node (database write)
5. Connect edges (routing logic)
6. Add interrupt point (human-in-the-loop)
7. Integrate with main orchestrator

Let's build it! 🚀
