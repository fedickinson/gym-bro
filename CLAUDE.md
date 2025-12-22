# Fitness Coach System

## Overview
A personal fitness coaching app demonstrating practical agentic AI architecture. Uses LangChain for orchestration, LangGraph for stateful workflows, and Claude for intelligence. Agents are used purposefully—only where they add value.

## Philosophy
- All movement counts (gym, classes, climbing, walks)
- Celebrates consistency over perfection
- No guilt for missed days
- Adapts to energy, travel, equipment availability
- Long-term records enable pattern recognition
- **Weekly split balance** - tracks rotation across Push/Pull/Legs/Upper/Lower

## Tech Stack
- **Frontend:** Streamlit
- **Orchestration:** LangChain + LangGraph
- **AI:** Claude API (Anthropic)
- **Data:** JSON files (simple, portable, version controlled)

---

## Agentic Architecture

### Design Principle
Use the simplest pattern that works. Agents only where reasoning + tools are needed.

```
┌─────────────────────────────────────────────────────────────────┐
│  USER INPUT                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  INTENT ROUTER (LangChain)                                      │
│  Classifies: log | query | recommend | chat | admin             │
└─────────────────────────────────────────────────────────────────┘
         │           │            │            │           │
         ▼           ▼            ▼            ▼           ▼
    ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────┐  ┌────────┐
    │  LOG   │  │ QUERY  │  │RECOMMEND │  │  CHAT  │  │ ADMIN  │
    │ Graph  │  │ Agent  │  │  Agent   │  │ Chain  │  │ Chain  │
    │        │  │        │  │          │  │        │  │        │
    │LangGraph│ │ ReAct  │  │  ReAct   │  │ Simple │  │ Simple │
    └────────┘  └────────┘  └──────────┘  └────────┘  └────────┘
```

### Pattern Selection Rationale

| Component | Pattern | Why This Pattern |
|-----------|---------|------------------|
| Log Workout | **LangGraph** | Multi-step with state: parse → confirm → save. Human-in-the-loop. |
| Query History | **ReAct Agent** | Needs tools to search, filter, calculate. Variable complexity. |
| Recommendations | **ReAct Agent** | Needs tools for weekly split, history, muscle balance. |
| General Chat | **Simple Chain** | Just conversation, no tools needed. |
| Admin/Edit | **Simple Chain** | Structured, predictable flow. |

---

## Tools

### Query Agent Tools
```python
@tool
def search_workouts(query: str, days: int = 30) -> list[dict]:
    """Search workout logs by keyword, exercise, or date range."""

@tool
def get_exercise_history(exercise: str, days: int = 90) -> list[dict]:
    """Get weight/rep history for a specific exercise."""

@tool
def calculate_progression(exercise: str) -> dict:
    """Calculate progression stats: trend, PR, avg increase."""

@tool
def compare_exercises(exercise1: str, exercise2: str) -> dict:
    """Compare progression between two exercises."""
```

### Recommend Agent Tools
```python
@tool
def get_weekly_split_status() -> dict:
    """Get current week's workout completion by type."""

@tool
def get_last_workout_by_type(workout_type: str) -> dict:
    """Get most recent workout of a specific type."""

@tool
def check_muscle_balance() -> dict:
    """Analyze if any muscle groups are under/over trained."""

@tool
def suggest_next_workout() -> dict:
    """Based on split rotation and recent history, suggest next workout."""

@tool
def get_template(workout_type: str) -> dict:
    """Get the workout template for a given type."""
```

---

## LangGraph: Workout Logging Flow

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   parse     │  Claude extracts structure from notes
                    │   notes     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   confirm   │  Display to user, ask approval
                    │   with_user │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │ approve │  │  edit   │  │ cancel  │
        └────┬────┘  └────┬────┘  └────┬────┘
             │            │            │
             │      ┌─────┘            │
             ▼      ▼                  ▼
        ┌─────────────┐           ┌─────────┐
        │    save     │           │   END   │
        └──────┬──────┘           └─────────┘
               │
               ▼
        ┌─────────────┐
        │  respond    │  Confirm save, note any patterns
        └──────┬──────┘
               │
               ▼
           ┌───────┐
           │  END  │
           └───────┘
```

### Graph State
```python
class LogWorkoutState(TypedDict):
    raw_notes: str
    parsed_workout: dict | None
    user_feedback: str | None  # "approve" | "edit" | "cancel"
    edits: dict | None
    saved: bool
    response: str
```

---

## Weekly Split System

### Data Model
```json
{
  "split_config": {
    "types": ["Push", "Pull", "Legs", "Upper", "Lower"],
    "rotation": ["Push", "Pull", "Legs", "Upper", "Lower", "Legs"],
    "weekly_targets": {
      "Push": 1,
      "Pull": 1, 
      "Legs": 2,
      "Upper": 1,
      "Lower": 1
    }
  },
  "current_week": {
    "start_date": "2024-12-16",
    "workouts": [
      {"date": "2024-12-16", "type": "Push", "log_id": "2024-12-16-001"},
      {"date": "2024-12-17", "type": "Pull", "log_id": "2024-12-17-001"}
    ],
    "next_in_rotation": "Legs"
  }
}
```

### Balance Checking
The recommend agent uses this to:
1. See what's done this week
2. What's missing from targets
3. What's next in rotation
4. Suggest accordingly

Example:
```
User: "What should I do today?"

Agent thinks:
- Check weekly split status → Push ✓, Pull ✓, Legs (0/2)
- Next in rotation → Legs
- Last legs workout → 3 days ago
- Response: "Legs is up next. You've done Push and Pull this week, 
  and you're at 0/2 for legs. Want me to pull up your leg template?"
```

---

## Directory Structure

```
fitness-coach/
├── CLAUDE.md              # This file
├── PRD.md                 # Product requirements
├── app.py                 # Streamlit entry
├── requirements.txt
├── .env
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── router.py      # Intent classification
│   │   ├── log_graph.py   # LangGraph for logging
│   │   ├── query_agent.py # ReAct for queries
│   │   └── recommend_agent.py  # ReAct for recommendations
│   ├── chains/
│   │   ├── __init__.py
│   │   ├── chat_chain.py  # Simple conversation
│   │   └── admin_chain.py # Edit/delete operations
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── query_tools.py
│   │   └── recommend_tools.py
│   ├── data.py            # JSON read/write
│   └── models.py          # Pydantic models
├── data/
│   ├── raw/               # Original phase files
│   ├── workout_logs.json
│   ├── templates.json
│   ├── exercises.json
│   └── weekly_split.json
└── pages/
    ├── 1_Log_Workout.py
    ├── 2_Chat.py
    ├── 3_History.py
    └── 4_Progress.py
```

---

## Data Models

### workout_logs.json
```json
{
  "logs": [
    {
      "id": "2024-01-15-001",
      "date": "2024-01-15",
      "type": "Push",
      "template_id": "push_a",
      "exercises": [
        {
          "name": "Dumbbell Bench Press",
          "sets": [
            {"reps": 8, "weight_lbs": 45},
            {"reps": 8, "weight_lbs": 45},
            {"reps": 7, "weight_lbs": 45}
          ]
        }
      ],
      "warmup": {"type": "jog", "duration_min": 10, "distance_miles": 1.0},
      "notes": "Shoulder felt tight",
      "completed": true,
      "created_at": "2024-01-15T18:30:00Z"
    }
  ]
}
```

### templates.json
```json
{
  "templates": [
    {
      "id": "push_a",
      "name": "Push Day A",
      "type": "Push",
      "exercises": [
        {
          "name": "Dumbbell Incline Bench Press",
          "target_sets": 4,
          "target_reps": 8,
          "rest_seconds": 90
        }
      ],
      "supersets": [
        {
          "exercises": ["Cable Fly", "Push Ups"],
          "rounds": 3,
          "rest_seconds": 60
        }
      ]
    }
  ]
}
```

---

## Build Order (for Cursor)

### Phase 1: Foundation
1. Set up directory structure
2. Create Pydantic models
3. Build data.py (JSON CRUD)
4. Parse historical data → JSON

### Phase 2: Simple Chains
1. Router chain (intent classification)
2. Chat chain (basic conversation)
3. Basic Streamlit integration

### Phase 3: Agents
1. Query tools
2. Query agent (ReAct)
3. Recommend tools (including weekly split)
4. Recommend agent (ReAct)

### Phase 4: LangGraph
1. Log workflow graph
2. State management
3. Human-in-the-loop confirmation

### Phase 5: Polish
1. Progress charts
2. History page with filters
3. Weekly split visualization

---

## Environment Variables

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Running the App

```bash
pip install -r requirements.txt
streamlit run app.py
```
