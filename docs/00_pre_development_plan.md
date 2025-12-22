# Pre-Development Setup Plan

## Current State Assessment
✅ Phase 1 marked complete with these files:
- `src/models.py` - Pydantic models
- `src/data.py` - JSON CRUD operations
- `src/agents/router.py` - Intent classification
- `src/tools/query_tools.py` - Query tools
- `src/tools/recommend_tools.py` - Recommendation tools

❓ **Need to verify**: Are these files complete and tested?

---

## Step 1: Environment & Dependencies

### 1.1 Verify Python Environment
```bash
python --version  # Should be 3.10+
which python      # Confirm we're in venv
```

### 1.2 Check Dependencies
```bash
pip list | grep -E "langchain|anthropic|streamlit|pydantic"
```

### 1.3 Verify API Key
```bash
echo $ANTHROPIC_API_KEY  # Should show sk-ant-...
```

---

## Step 2: MCP (Model Context Protocol) Setup

MCPs extend Claude's capabilities with specialized tools. For this fitness app, we should install:

### 2.1 Essential MCPs

#### **Filesystem MCP** (CRITICAL)
- **Why**: App stores all data in JSON files (workout_logs.json, templates.json, etc.)
- **Use cases**:
  - Reading/writing workout logs
  - Managing templates
  - Accessing exercise database
  - Weekly split tracking
- **Install**:
  ```bash
  # Add to Claude desktop config
  npx -y @modelcontextprotocol/server-filesystem /Users/franklindickinson/Projects/gym-bro/data
  ```

#### **Time/Date MCP** (RECOMMENDED)
- **Why**: Weekly split rotation, date ranges, workout history queries
- **Use cases**:
  - Calculate "last 30 days" for queries
  - Weekly split reset logic (start of week)
  - Progression over time calculations
- **Check availability**: May need custom implementation

### 2.2 MCP Configuration

Claude Code MCP servers are configured in Claude desktop config. We need to:

1. **Check current MCP config**:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Add filesystem MCP** for the data directory:
   ```json
   {
     "mcpServers": {
       "filesystem": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-filesystem",
           "/Users/franklindickinson/Projects/gym-bro/data"
         ]
       }
     }
   }
   ```

3. **Restart Claude desktop** to load MCPs

4. **Verify MCP tools are available**:
   - Use MCPSearch tool to find filesystem tools
   - Test reading/writing to data directory

### 2.3 Testing MCP Setup

Create a test script to verify:
```python
# test_mcp_setup.py
import json
from pathlib import Path

def test_data_directory():
    """Test that we can read/write JSON in data directory"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    test_file = data_dir / "test.json"
    test_data = {"test": "success", "timestamp": "2024-12-22"}

    # Write
    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # Read
    with open(test_file, "r") as f:
        loaded = json.load(f)

    assert loaded == test_data
    test_file.unlink()  # Clean up
    print("✅ Data directory read/write successful")

if __name__ == "__main__":
    test_data_directory()
```

---

## Step 3: Code Review & Validation

Before building new components, validate Phase 1 work:

### 3.1 Review Core Files
- [ ] `src/models.py` - All Pydantic models defined?
  - WorkoutLog
  - Exercise
  - ExerciseSet
  - Template
  - WeeklySplit

- [ ] `src/data.py` - All CRUD operations?
  - Load/save workout logs
  - Load/save templates
  - Weekly split management
  - Exercise database operations

- [ ] `src/agents/router.py` - Intent classification working?
  - Test: "log" vs "query" vs "recommend" vs "chat"

- [ ] `src/tools/*.py` - Tools properly decorated with @tool?
  - Query tools: search_workouts, get_exercise_history, etc.
  - Recommend tools: get_weekly_split_status, suggest_next_workout, etc.

### 3.2 Create Test Data

Initialize JSON files with sample data:

#### `data/workout_logs.json`
```json
{
  "logs": [
    {
      "id": "2024-12-20-001",
      "date": "2024-12-20",
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
      "notes": "Good session",
      "completed": true,
      "created_at": "2024-12-20T18:30:00Z"
    }
  ]
}
```

#### `data/templates.json`
```json
{
  "templates": [
    {
      "id": "push_a",
      "name": "Push Day A",
      "type": "Push",
      "exercises": [
        {
          "name": "Dumbbell Bench Press",
          "target_sets": 4,
          "target_reps": 8,
          "rest_seconds": 90
        },
        {
          "name": "Overhead Press",
          "target_sets": 4,
          "target_reps": 8,
          "rest_seconds": 90
        }
      ]
    }
  ]
}
```

#### `data/weekly_split.json`
```json
{
  "config": {
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
    "workouts": [],
    "next_in_rotation": "Push"
  }
}
```

#### `data/exercises.json`
```json
{
  "exercises": [
    {
      "name": "Dumbbell Bench Press",
      "category": "Push",
      "muscle_groups": ["Chest", "Triceps", "Shoulders"],
      "equipment": "Dumbbells"
    },
    {
      "name": "Squat",
      "category": "Legs",
      "muscle_groups": ["Quads", "Glutes", "Core"],
      "equipment": "Barbell"
    }
  ]
}
```

---

## Step 4: Create Missing __init__.py Files

Ensure Python can import modules:

```bash
touch src/__init__.py
touch src/agents/__init__.py
touch src/chains/__init__.py
touch src/tools/__init__.py
```

---

## Step 5: Integration Test Plan

Before moving to Phase 2, test Phase 1 components:

### 5.1 Unit Tests
```python
# test_phase1.py

def test_models():
    """Test Pydantic models validate correctly"""
    from src.models import WorkoutLog, Exercise
    # Test valid data
    # Test validation errors

def test_data_layer():
    """Test JSON CRUD operations"""
    from src.data import load_workout_logs, save_workout_log
    # Test load/save
    # Test error handling

def test_router():
    """Test intent classification"""
    from src.agents.router import classify_intent
    # Test: "Did push today" → "log"
    # Test: "What's my bench PR?" → "query"
    # Test: "What should I do today?" → "recommend"
    # Test: "How are you?" → "chat"

def test_query_tools():
    """Test query tools with sample data"""
    from src.tools.query_tools import search_workouts, get_exercise_history
    # Test with sample data

def test_recommend_tools():
    """Test recommendation tools"""
    from src.tools.recommend_tools import get_weekly_split_status
    # Test weekly split logic
```

### 5.2 Manual Testing Checklist
- [ ] Load sample workout logs
- [ ] Router classifies intents correctly
- [ ] Query tools return expected results
- [ ] Recommend tools calculate weekly split correctly
- [ ] Data persists across reads/writes

---

## Step 6: Pre-Phase 2 Checklist

Before starting Phase 2 (Agents & Chains):

- [ ] Python environment confirmed
- [ ] All dependencies installed
- [ ] ANTHROPIC_API_KEY set
- [ ] MCPs configured and tested
- [ ] Phase 1 files reviewed
- [ ] Sample data created
- [ ] __init__.py files created
- [ ] Unit tests written and passing
- [ ] Manual testing completed

---

## Next Steps (Phase 2 Preview)

Once pre-development is complete, Phase 2 will build:

1. **Simple Chains**:
   - Chat chain (no tools, just conversation)
   - Admin chain (edit/delete operations)

2. **ReAct Agents**:
   - Query agent (uses query_tools)
   - Recommend agent (uses recommend_tools)

3. **Main Orchestrator**:
   - Routes to appropriate handler based on intent
   - Maintains conversation context

---

## Questions to Resolve

1. **Phase 1 completeness**: Are the existing files fully implemented or just stubs?
2. **Testing strategy**: Should we write pytest tests or manual test scripts?
3. **Data validation**: Do we need migration scripts for the historical phase data?
4. **MCP scope**: Are there other MCPs we should consider (e.g., sequential thinking)?

---

## Estimated Timeline

- Step 1-2: Environment & MCP setup - 30 min
- Step 3: Code review - 1 hour
- Step 4-5: Test data & init files - 30 min
- Step 6: Integration testing - 1 hour

**Total**: ~3 hours to validate foundation before Phase 2
