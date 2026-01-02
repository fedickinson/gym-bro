# Gym Bro Agents Reference

## Contents
- Orchestrator
- ReAct Agents (3)
- LangGraph Workflows (2)
- Specialized Agents (6)
- Simple Chains (3)

---

## Orchestrator

### GymBroOrchestrator
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/main.py`
**Lines**: 205
**Pattern**: Orchestration Layer

**Purpose**: Entry point for entire agentic system. Routes user input to specialized handlers.

**Components**:
- Intent Router - Classifies user input → intent
- Handler Routing - Maps intent → appropriate agent/chain
- Response Coordination - Returns formatted responses

**Key Method**: `_route_to_handler(intent, user_input, chat_history)`

---

## ReAct Agents

ReAct Pattern = Reasoning + Actions (using tools)

### 1. QueryAgent
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/query_agent.py`
**Lines**: 189
**Intent**: `query`

**Purpose**: Answers questions about workout history and past data.

**Tools Available**:
- `search_workouts` - Find workouts by keyword/exercise
- `get_exercise_history` - Weight/rep history for exercise
- `calculate_progression` - Stats: trend, PR, avg increase
- `compare_exercises` - Side-by-side comparison
- `get_workout_count` - Count workouts in time period

**Example Queries**:
- "What did I bench last week?"
- "Show my progress on squats"
- "How many leg days in December?"

---

### 2. RecommendAgent
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/recommend_agent.py`
**Lines**: 216
**Intent**: `recommend`

**Purpose**: Provides workout recommendations based on weekly split rotation.

**Tools Available**:
- `get_weekly_split_status` - Week's completion status
- `suggest_next_workout` - Smart suggestion with catch-up mode
- `get_last_workout_by_type` - Most recent of specific type
- `check_muscle_balance` - Push/pull/legs ratio analysis
- `get_workout_template` - Template retrieval
- `get_abs_status` - Ab workout tracking

**Example Queries**:
- "What should I do today?" (passive)
- "Any recommendations?"

**Note**: Rarely used - CHAT handles active planning

---

### 3. ChatAgent
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/chat_agent.py`
**Lines**: 351
**Intent**: `chat`

**Purpose**: Conversational interface with data access AND workout planning. **DEFAULT handler** for most workout-related requests.

**Tools Available**:
- All query tools (history access)
- All recommend tools (planning)
- `start_workout_session` - Initiates planning session

**Example Queries**:
- "I need a workout"
- "Quick 30-min push workout"
- "I only have dumbbells"
- "Let's start"
- "How does progressive overload work?"

**Critical**: Handles future planning, constraints, conversational flow

---

## LangGraph Workflows

Stateful, multi-step processes with human-in-the-loop

### 1. SessionGraph
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/session_graph.py`
**Lines**: 1233
**Intent**: Internal (called by ChatAgent via `start_workout_session` tool)

**Purpose**: Complete workout session management - planning, real-time suggestions, tracking.

**State**: `SessionWithPlanState` (18+ fields)

**Workflow**:
```
Initialize Planning
   ↓
Generate Next Suggestion
   ↓
User Records Sets
   ↓
Detect Deviations
   ↓
Accumulate Exercises
   ↓
Save Workout
```

**Features**:
- Equipment constraint handling
- Adaptive template generation
- Deviation detection (swapped exercises)
- Supplementary work (abs) scheduling
- Weekly split awareness

**Nodes**:
- `initialize_planning` - Get next workout suggestion
- `generate_next_suggestion` - Recommend exercise
- `save_workout` - Persist to database

---

### 2. LogGraph
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/log_graph.py`
**Lines**: 497
**Intent**: `log`

**Purpose**: Log completed workouts with human confirmation.

**State**: `LogWorkoutState`

**Workflow**:
```
Parse Notes (Claude extracts structure)
   ↓
Confirm with User (INTERRUPT)
   ↓
   ├─ Approve → Save Workout
   ├─ Edit → Back to Parse
   └─ Cancel → End
```

**Nodes**:
- `parse_notes` - Extract workout from natural language
- `confirm_with_user` - Show preview, wait for approval
- `save_workout` - Persist to database
- `cancel_workout` - Handle cancellation

---

## Specialized Agents

### 1. SuggestionEngine
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/suggestion_engine.py`
**Lines**: 570

**Purpose**: Generates intelligent real-time exercise suggestions during workouts.

**Features**:
- Progressive overload tracking
- Weight increase suggestions
- Equipment substitutions

---

### 2. TemplateGenerator
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/template_generator.py`
**Lines**: 330

**Purpose**: Creates adaptive workout templates based on training history.

**Fallback**: Static templates if insufficient data

---

### 3. PlanAdapter
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/plan_adapter.py`
**Lines**: 118

**Purpose**: Modifies workout plans during session based on feedback/constraints.

**Use Cases**:
- Equipment unavailable
- Time constraints
- Energy level adjustments

---

### 4. DeviationDetector
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/deviation_detector.py`
**Lines**: 236

**Purpose**: Compares actual workout to planned workout, identifies swaps/modifications.

**Output**: Recording mode (exact | modified | different)

---

### 5. AbsRecommender
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/abs_recommender.py`
**Lines**: 138

**Purpose**: Specialized agent for ab workout scheduling and spacing.

**Rules**:
- Target: 2 ab workouts per week
- Spacing: No consecutive day ab work
- Tracks via supplementary_work field

---

### 6. PlanningChain
**File**: `/Users/franklindickinson/Projects/gym-bro/src/agents/planning_chain.py`
**Lines**: 180

**Purpose**: Pre-workout planning logic and decision-making.

---

## Simple Chains

Straightforward prompting without tools

### 1. ChatChain
**File**: `/Users/franklindickinson/Projects/gym-bro/src/chains/chat_chain.py`
**Intent**: `chat` (fallback when ChatAgent not needed)

**Purpose**: Simple conversation without data access.

---

### 2. AdminChain
**File**: `/Users/franklindickinson/Projects/gym-bro/src/chains/admin_chain.py`
**Intent**: `admin`

**Purpose**: Handles edit/delete operations on existing logs.

**Operations**:
- Edit workout data
- Delete logs (soft delete)
- Fix incorrect entries

---

## Agent Selection Decision Tree

```
Is it about PAST workout data?
├─ Yes → QueryAgent (intent: query)
└─ No
   ↓
   Is user asking passively for suggestions?
   ├─ Yes → RecommendAgent (intent: recommend)
   └─ No
      ↓
      Is it edit/delete operation?
      ├─ Yes → AdminChain (intent: admin)
      └─ No
         ↓
         Is user recording PAST workout?
         ├─ Yes → LogGraph (intent: log)
         └─ No → ChatAgent (intent: chat) [DEFAULT]
```

---

## Integration Pattern

**Adding a New Agent:**

1. Create agent file in `src/agents/`
2. Choose pattern (ReAct | LangGraph | Chain)
3. Update `main.py`:
   - Import new agent
   - Add to `__init__`
   - Add case in `_route_to_handler()`
4. Update `router.py`:
   - Add intent to ROUTER_PROMPT
   - Add patterns to QUICK_PATTERNS (if applicable)
5. Test with orchestrator

See `creating-agents` skill for scaffolding.
