---
name: exploring-codebase
description: Explores multi-agent architecture (LangChain/LangGraph), intent routing, and data flow. Use when understanding how agents work, finding tools, or tracing request flows through the Gym Bro system.
---

# Gym Bro Architecture Explorer

## Architecture Overview

```
User Input
   ↓
Intent Router (router.py:48-68)
   ├─ quick_route() - Pattern matching (fast)
   └─ classify() - LLM classification (fallback)
   ↓
GymBroOrchestrator (main.py:36)
   ├─ chat → ChatAgent (ReAct with tools)
   ├─ query → QueryAgent (ReAct with 5 query tools)
   ├─ recommend → RecommendAgent (ReAct with planning tools)
   ├─ admin → AdminChain (simple chain)
   └─ log → LangGraph workflow
```

## Quick Navigation

**Find specific information:**
- **All agents** → See [AGENTS.md](AGENTS.md)
- **All tools** → See [TOOLS.md](TOOLS.md)
- **Data models** → See [DATA.md](DATA.md)

## Intent Routing Logic

Located in `/Users/franklindickinson/Projects/gym-bro/src/agents/router.py`

**5 Intent Types:**

| Intent | When Used | Example Queries |
|--------|-----------|----------------|
| `log` | Recording PAST workouts | "Just did push day", "3x8 bench at 135" |
| `query` | Questions about history | "What did I bench?", "Show my progress" |
| `recommend` | Passive suggestions | "What should I do today?" (not planning) |
| `admin` | Edit/delete data | "Fix my last workout", "Delete Tuesday's log" |
| `chat` | **DEFAULT** - planning, starting, constraints | "I need a workout", "only have dumbbells" |

**Critical Rule**: Anything workout-related that isn't logging PAST workouts → CHAT

**Routing Flow:**
1. `quick_route()` checks pattern matching (fast path)
2. If no match, `classify()` uses LLM (router.py:48)
3. Orchestrator calls `_route_to_handler()` (main.py)

## Core Files

**Entry Point:**
- `/Users/franklindickinson/Projects/gym-bro/src/agents/main.py` - GymBroOrchestrator (205 LOC)

**Routing:**
- `/Users/franklindickinson/Projects/gym-bro/src/agents/router.py` - Intent classification (119 LOC)

**Agents (14 total):**
See [AGENTS.md](AGENTS.md) for complete list with patterns

**Tools (11 total):**
See [TOOLS.md](TOOLS.md) for signatures and usage

**Data Layer:**
See [DATA.md](DATA.md) for models and JSON structure

## Common Queries

### "Where are workout logs stored?"
```bash
# Data files in /Users/franklindickinson/Projects/gym-bro/data/
ls data/
# workout_logs.json - All logged workouts
# templates.json - Workout templates
# weekly_split.json - Split tracking
```

See [DATA.md](DATA.md) for schemas

### "What's the LangGraph workflow?"

**Session Graph** (session_graph.py:1233 LOC):
- Most complex workflow
- Multi-step planning with state
- Equipment constraints
- Real-time suggestions

**Log Graph** (log_graph.py):
- Simpler workflow
- Parse notes → Confirm → Save
- Human-in-the-loop

See [AGENTS.md](AGENTS.md) for detailed LangGraph patterns

### "How do I find a specific tool?"

```bash
# Search for tool by name
grep -r "@tool" src/tools/

# Or see TOOLS.md for organized list
```

See [TOOLS.md](TOOLS.md)

## File Organization

```
src/
├── agents/           # 14 agent files (orchestration layer)
│   ├── main.py      # Entry point - GymBroOrchestrator
│   ├── router.py    # Intent classification
│   ├── *_agent.py   # ReAct agents (query, recommend, chat)
│   ├── *_graph.py   # LangGraph workflows (session, log)
│   └── *_chain.py   # Simple chains
│
├── tools/           # 5 tool modules (agent capabilities)
│   ├── query_tools.py      # 5 query tools
│   ├── recommend_tools.py  # 6 recommend tools
│   ├── session_tools.py    # Session tools
│   ├── abs_tools.py        # Abs recommendations
│   └── adaptive_template_tools.py
│
├── ui/              # 14 UI components (Streamlit)
│   ├── styles.py            # Design system (611 LOC)
│   ├── session.py           # Session state
│   ├── navigation.py        # Bottom nav
│   └── *_components.py      # Reusable components
│
├── data.py          # Data layer - CRUD operations (635 LOC)
├── models.py        # Pydantic models (204 LOC)
│
data/                # JSON storage
├── workout_logs.json
├── templates.json
├── weekly_split.json
└── exercises.json

pages/               # 6 Streamlit pages
├── app.py                   # Home
├── 1_Log_Workout.py         # Workout logging
├── 2_Chat.py                # Conversational interface
├── 3_History.py             # Browse workouts
├── 4_Progress.py            # Charts & analytics
└── 5_Trash.py               # Soft-deleted workouts
```

## Pattern Identification

**ReAct Pattern** (Reasoning + Actions):
- Uses tools to answer variable complexity questions
- Examples: QueryAgent, RecommendAgent, ChatAgent
- See `/Users/franklindickinson/Projects/gym-bro/src/agents/query_agent.py`

**LangGraph Pattern** (Stateful Workflow):
- Multi-step process with human-in-the-loop
- Examples: SessionGraph, LogGraph
- See `/Users/franklindickinson/Projects/gym-bro/src/agents/session_graph.py`

**Simple Chain Pattern** (Direct Prompting):
- Straightforward tasks without tools
- Examples: AdminChain, ChatChain
- See `/Users/franklindickinson/Projects/gym-bro/src/chains/chat_chain.py`

## Tracing Request Flows

**Example: User asks "What did I bench last week?"**

1. **Router** (router.py) → classifies as `query` intent
2. **Orchestrator** (main.py) → routes to QueryAgent
3. **QueryAgent** (query_agent.py) → uses `search_workouts` tool
4. **search_workouts** (query_tools.py) → queries workout_logs.json
5. **Data Layer** (data.py) → returns matching logs
6. **QueryAgent** → formats response
7. **Orchestrator** → returns to user

Trace file access: Start at `main.py:_route_to_handler()`

## Quick Search Commands

```bash
# Find agent definitions
grep -n "class.*Agent" src/agents/*.py

# Find tool definitions
grep -n "@tool" src/tools/*.py

# Find LangGraph workflows
grep -n "StateGraph" src/agents/*.py

# Find data models
grep -n "class.*BaseModel" src/models.py
```

---

For detailed information, see:
- [AGENTS.md](AGENTS.md) - All 14 agents with patterns
- [TOOLS.md](TOOLS.md) - All 11 tools with signatures
- [DATA.md](DATA.md) - Data models and JSON schemas
