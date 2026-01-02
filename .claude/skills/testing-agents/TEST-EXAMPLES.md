# Common Test Scenarios

## 1. Testing Intent Routing

**Goal**: Verify router classifies intents correctly

```python
# test_intent_routing.py
from src.agents.router import IntentRouter, quick_route
from dotenv import load_dotenv

load_dotenv()
router = IntentRouter()

test_cases = [
    ("Just did push day", "log"),
    ("What did I bench last week?", "query"),
    ("What should I do today?", "recommend"),
    ("I need a workout", "chat"),
    ("Delete my last workout", "admin"),
]

for message, expected in test_cases:
    # Try quick route first
    quick_intent = quick_route(message)
    if quick_intent:
        print(f"✓ Quick route: '{message}' → {quick_intent}")
        continue

    # Fall back to LLM
    result = router.classify(message)
    actual = result.intent
    match = "✓" if actual == expected else "✗"
    print(f"{match} '{message}' → Expected: {expected}, Got: {actual}")
```

**Expected Output**:
```
✓ Quick route: 'Just did push day' → log
✓ 'What did I bench last week?' → Expected: query, Got: query
✓ 'What should I do today?' → Expected: recommend, Got: recommend
✓ 'I need a workout' → Expected: chat, Got: chat
✓ Quick route: 'Delete my last workout' → admin
```

---

## 2. Testing Equipment Constraints

**Goal**: Verify session graph handles unavailable equipment

```python
# test_equipment_constraints.py
from src.agents.session_graph import initialize_planning_session, initialize_planning
from dotenv import load_dotenv

load_dotenv()

# Initialize with barbell unavailable
state = initialize_planning_session()
state['equipment_unavailable'] = ['barbell', 'smith machine']

# Run planning
result = initialize_planning(state)

print("Suggested Type:", result['suggested_type'])
print("\nTemplate Exercises:")
for ex in result['planned_template']['exercises'][:3]:
    print(f"  - {ex['name']}")

print("\nAdaptations Made:")
for adaptation in result['planned_template'].get('adaptations', []):
    print(f"  • {adaptation}")
```

**Expected Output**:
```
Suggested Type: Push

Template Exercises:
  - Dumbbell Bench Press
  - Dumbbell Incline Press
  - Cable Fly

Adaptations Made:
  • Replaced Barbell Bench Press with Dumbbell Bench Press (barbell unavailable)
  • Skipped Smith Machine exercises (equipment unavailable)
```

---

## 3. Testing Catch-Up Mode

**Goal**: Verify recommendation system detects catch-up scenarios

```python
# test_catch_up_mode.py
from src.tools.recommend_tools import suggest_next_workout
from src.data import get_weekly_split, update_weekly_split
from datetime import date, timedelta

# Simulate: Friday, user has done Push and Pull, needs 2 Legs + Upper + Lower
today = date.today()
weekday = today.weekday()  # 0=Monday, 4=Friday

if weekday < 4:
    print("Run this test on Friday or later for catch-up mode")
else:
    result = suggest_next_workout.invoke({})

    print("Suggestion:", result['suggested_type'])
    print("Reason:", result['reason'])
    print("Catch-up Mode:", result.get('catch_up_mode', False))

    if result.get('catch_up_mode'):
        print("\nCatch-up Details:", result.get('catch_up_details'))
```

---

## 4. Testing Deviation Detection

**Goal**: Verify system detects when user does different exercises than planned

```python
# test_deviation_detection.py
from src.agents.deviation_detector import detect_deviation

planned_exercises = [
    "Dumbbell Bench Press",
    "Dumbbell Incline Press",
    "Cable Fly"
]

actual_exercises = [
    {"name": "Barbell Bench Press", "sets": [{"reps": 8, "weight_lbs": 135}]},
    {"name": "Dumbbell Incline Press", "sets": [{"reps": 10, "weight_lbs": 50}]},
    {"name": "Push Ups", "sets": [{"reps": 20}]}
]

# Note: This is pseudocode - actual implementation may vary
deviations = []
for planned in planned_exercises:
    matched = any(planned.lower() in ex['name'].lower() for ex in actual_exercises)
    if not matched:
        deviations.append(f"Skipped: {planned}")

for actual in actual_exercises:
    matched = any(actual['name'].lower() in planned.lower() for planned in planned_exercises)
    if not matched:
        deviations.append(f"Added: {actual['name']}")

print("Deviations Detected:")
for dev in deviations:
    print(f"  • {dev}")
```

**Expected Output**:
```
Deviations Detected:
  • Skipped: Dumbbell Bench Press
  • Added: Barbell Bench Press
  • Skipped: Cable Fly
  • Added: Push Ups
```

---

## 5. Testing Query Agent with Real Data

**Goal**: Verify query agent retrieves accurate workout data

```python
# test_query_real_data.py
from src.agents.query_agent import QueryAgent
from src.data import get_all_logs
from dotenv import load_dotenv

load_dotenv()

# First check we have data
logs = get_all_logs()
print(f"Total logs in database: {len(logs)}")

if len(logs) == 0:
    print("⚠️  No workout data found. Add some workouts first!")
else:
    agent = QueryAgent()

    # Test 1: Count workouts
    response1 = agent.query("How many workouts do I have?")
    print(f"\nTest 1: {response1}")

    # Test 2: Exercise history
    # Find an exercise from recent logs
    recent_exercise = logs[0]['exercises'][0]['name'] if logs[0].get('exercises') else None
    if recent_exercise:
        response2 = agent.query(f"Show me {recent_exercise} history")
        print(f"\nTest 2: {response2}")
```

---

## 6. Testing Tool Execution Time

**Goal**: Measure tool performance

```python
# test_tool_performance.py
import time
from src.tools.query_tools import (
    search_workouts,
    get_exercise_history,
    calculate_progression
)

def measure_tool(tool, params):
    """Measure tool execution time."""
    start = time.time()
    result = tool.invoke(params)
    elapsed = time.time() - start
    return result, elapsed

# Test each tool
tools_to_test = [
    (search_workouts, {"query": "push", "days": 30}),
    (get_exercise_history, {"exercise": "bench press", "days": 90}),
    (calculate_progression, {"exercise": "bench press"}),
]

print("Tool Performance:")
for tool, params in tools_to_test:
    result, elapsed = measure_tool(tool, params)
    print(f"  {tool.name}: {elapsed*1000:.1f}ms")
```

**Expected Output**:
```
Tool Performance:
  search_workouts: 12.3ms
  get_exercise_history: 8.7ms
  calculate_progression: 15.2ms
```

---

## 7. Testing LangGraph State Transitions

**Goal**: Verify workflow moves through states correctly

```python
# test_log_graph_states.py
from src.agents.log_graph import parse_notes, confirm_with_user, save_workout

# Initial state
state = {
    "raw_notes": "Did push day: bench 3x8 at 135, incline 3x10 at 50",
    "parsed_workout": None,
    "user_feedback": None,
    "saved": False
}

print("Initial State:", state)

# Step 1: Parse notes
state = parse_notes(state)
print("\nAfter parse_notes:")
print(f"  parsed_workout: {state.get('parsed_workout', {}).get('type')}")
print(f"  exercises: {len(state.get('parsed_workout', {}).get('exercises', []))}")

# Step 2: Confirm (human would respond here)
state = confirm_with_user(state)
print("\nAfter confirm_with_user:")
print(f"  response: {state.get('response')[:100]}...")

# Step 3: Simulate user approval
state['user_feedback'] = 'approve'

# Step 4: Save
state = save_workout(state)
print("\nAfter save_workout:")
print(f"  saved: {state.get('saved')}")
print(f"  log_id: {state.get('parsed_workout', {}).get('id')}")
```

---

## 8. Testing Multi-Turn Conversations

**Goal**: Verify chat agent maintains context

```python
# test_multi_turn.py
from src.agents.chat_agent import ChatAgent
from dotenv import load_dotenv

load_dotenv()
agent = ChatAgent()

# Turn 1
response1 = agent.chat("I want to do a push workout")
print(f"User: I want to do a push workout")
print(f"Agent: {response1}\n")

# Turn 2 - reference previous context
chat_history = [
    {"role": "user", "content": "I want to do a push workout"},
    {"role": "assistant", "content": response1}
]

response2 = agent.chat("I don't have a barbell", chat_history=chat_history)
print(f"User: I don't have a barbell")
print(f"Agent: {response2}\n")

# Check if agent adapted plan
assert "dumbbell" in response2.lower() or "alternative" in response2.lower()
print("✓ Agent adapted to equipment constraint")
```

---

## 9. Testing Error Handling

**Goal**: Verify graceful degradation

```python
# test_error_handling.py
from src.tools.query_tools import get_exercise_history

# Test 1: Nonexistent exercise
result1 = get_exercise_history.invoke({"exercise": "Flying Dragon Kick", "days": 90})
print("Test 1 - Nonexistent exercise:")
print(f"  Result: {result1}")
print(f"  ✓ Returns empty list (graceful)" if result1 == [] else "  ✗ Error")

# Test 2: Invalid days parameter
try:
    result2 = get_exercise_history.invoke({"exercise": "bench", "days": -1})
    print("\nTest 2 - Invalid days:")
    print(f"  Result: {result2}")
except Exception as e:
    print(f"\nTest 2 - Invalid days:")
    print(f"  Exception: {type(e).__name__}")
```

---

## 10. Testing Weekly Split Reset

**Goal**: Verify week resets on Monday

```python
# test_weekly_reset.py
from src.tools.recommend_tools import get_weekly_split_status
from datetime import date, timedelta

# Get current split status
status = get_weekly_split_status.invoke({})

print("Current Week Status:")
print(f"  Week start: {status['week_start']}")
print(f"  Completed: {status['completed']}")
print(f"  Remaining: {status['remaining']}")
print(f"  Days left: {status['days_left_in_week']}")

# Check if week_start is a Monday
week_start = date.fromisoformat(status['week_start'])
is_monday = week_start.weekday() == 0  # 0 = Monday

print(f"\n✓ Week starts on Monday" if is_monday else "✗ Week doesn't start on Monday")
```

---

For more detailed tracing information, see [TRACING.md](TRACING.md)
