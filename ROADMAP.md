# Development Roadmap

## V1 Goal
A working fitness coach that demonstrates agentic AI architecture patterns. Should be functional for personal use AND serve as a portfolio piece.

---

## Phase 1: Foundation ✅
**Status**: Complete

- [x] Project structure and dependencies
- [x] Pydantic models (`src/models.py`)
- [x] Data layer with JSON CRUD (`src/data.py`)
- [x] Intent router (`src/agents/router.py`)
- [x] Query tools (`src/tools/query_tools.py`)
- [x] Recommend tools (`src/tools/recommend_tools.py`)

**Files created:**
```
src/
├── models.py          # WorkoutLog, Exercise, WeeklySplit, etc.
├── data.py            # JSON operations, weekly split tracking
├── agents/
│   └── router.py      # Intent classification
└── tools/
    ├── query_tools.py     # search_workouts, get_exercise_history, etc.
    └── recommend_tools.py # get_weekly_split_status, suggest_next_workout, etc.
```

---

## Phase 2: Agents & Chains 🔄
**Status**: In Progress

### 2.1 Simple Chains
- [ ] Chat chain (`src/chains/chat_chain.py`)
  - Basic conversation, no tools
  - System prompt with fitness coach persona
  
- [ ] Admin chain (`src/chains/admin_chain.py`)
  - Edit workout logs
  - Delete workout logs
  - Structured confirmation flow

### 2.2 ReAct Agents
- [ ] Query agent (`src/agents/query_agent.py`)
  - Uses query_tools
  - Handles: "What did I bench last week?", "Show my progress on squats"
  
- [ ] Recommend agent (`src/agents/recommend_agent.py`)
  - Uses recommend_tools
  - Handles: "What should I do today?", "Am I overtraining chest?"

### 2.3 Main Orchestrator
- [ ] Main handler (`src/agents/main.py`)
  - Routes intent to appropriate handler
  - Maintains conversation context

**Deliverable**: Can have a conversation that routes correctly to different handlers.

---

## Phase 3: LangGraph Workflow
**Status**: Not Started

- [ ] Log workflow graph (`src/agents/log_graph.py`)
  - State: `LogWorkoutState`
  - Nodes: parse_notes → confirm → save → respond
  - Conditional edges for approve/edit/cancel

- [ ] Integration with router
  - "log" intent triggers the graph
  - Graph pauses for human confirmation
  - Resumes based on user response

**Deliverable**: Natural language workout logging with confirmation step.

---

## Phase 4: Streamlit UI
**Status**: Not Started

### 4.1 Core Pages
- [ ] `app.py` - Main entry, session state setup
- [ ] `pages/1_Log_Workout.py` - Log interface with confirmation
- [ ] `pages/2_Chat.py` - General chat interface
- [ ] `pages/3_History.py` - View/filter past workouts
- [ ] `pages/4_Progress.py` - Charts and trends

### 4.2 UI Components
- [ ] Workout log preview (for confirmation step)
- [ ] Exercise history table
- [ ] Weekly split status display
- [ ] Progress charts (weight over time, volume trends)

**Deliverable**: Functional multi-page Streamlit app.

---

## Phase 5: Historical Data Import
**Status**: Not Started

- [ ] Parse phase markdown files (phase_01.md - phase_10.md)
- [ ] Convert to JSON format
- [ ] Import ~70 workout sessions
- [ ] Verify data integrity

**Deliverable**: App populated with real historical data.

---

## Phase 6: Polish & Documentation
**Status**: Not Started

- [ ] Error handling throughout
- [ ] Loading states in UI
- [ ] README.md with screenshots
- [ ] Demo video/GIF
- [ ] Blog post from devlog

**Deliverable**: Portfolio-ready project.

---

## File Checklist

### Must Have for V1
```
fitness-coach/
├── CLAUDE.md              ✅
├── ROADMAP.md             ✅
├── README.md              ⬜
├── requirements.txt       ✅
├── app.py                 ⬜
├── src/
│   ├── __init__.py        ⬜
│   ├── models.py          ✅
│   ├── data.py            ✅
│   ├── agents/
│   │   ├── __init__.py    ⬜
│   │   ├── router.py      ✅
│   │   ├── main.py        ⬜
│   │   ├── query_agent.py ⬜
│   │   ├── recommend_agent.py ⬜
│   │   └── log_graph.py   ⬜
│   ├── chains/
│   │   ├── __init__.py    ⬜
│   │   ├── chat_chain.py  ⬜
│   │   └── admin_chain.py ⬜
│   └── tools/
│       ├── __init__.py    ⬜
│       ├── query_tools.py ✅
│       └── recommend_tools.py ✅
├── data/
│   ├── workout_logs.json  ⬜
│   ├── templates.json     ⬜
│   ├── exercises.json     ⬜
│   └── weekly_split.json  ⬜
└── pages/
    ├── 1_Log_Workout.py   ⬜
    ├── 2_Chat.py          ⬜
    ├── 3_History.py       ⬜
    └── 4_Progress.py      ⬜
```

---

## Success Criteria

### Functional
- [ ] Can log a workout via natural language
- [ ] Can ask questions about workout history
- [ ] Can get intelligent workout recommendations
- [ ] Can view progress over time
- [ ] Weekly split tracking works correctly

### Portfolio
- [ ] Clean code with type hints
- [ ] Architecture is documented and explainable
- [ ] Can demo the different patterns (chain vs agent vs graph)
- [ ] Has real data demonstrating functionality

---

## Quick Start (for development)

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run
streamlit run app.py
```

---

## Notes

- Start with hardcoded test data before importing historical
- Test each component in isolation before integration
- The router is the critical path - get intent classification right first
- LangGraph is the most complex piece - save for after basic agents work
