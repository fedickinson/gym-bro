# Interpreting Agent Execution Traces

## ReAct Agent Trace Format

### Standard Trace Structure

```
> Entering new AgentExecutor chain...

Thought: [Agent's reasoning]
Action: [Tool name]
Action Input: [JSON parameters]
Observation: [Tool output]

Thought: [Next reasoning step]
Action: [Next tool]
Action Input: [Parameters]
Observation: [Output]

Thought: [Final reasoning]
Final Answer: [Response to user]

> Finished chain.
```

---

### Example: QueryAgent Trace

**User Query**: "What did I bench last week?"

```
> Entering new AgentExecutor chain...

Thought: I need to search for bench press workouts from the last 7 days
Action: search_workouts
Action Input: {"query": "bench press", "days": 7}
Observation: [{"date": "2024-12-15", "type": "Push", "exercises": [{"name": "Dumbbell Bench Press", "sets": [{"reps": 8, "weight_lbs": 135}, {"reps": 8, "weight_lbs": 135}, {"reps": 7, "weight_lbs": 135}]}]}]

Thought: I found a bench press workout from December 15th. I should provide the user with the weight and reps.
Final Answer: Based on your workout history, you benched 135 lbs for 3 sets on December 15th (8, 8, and 7 reps).

> Finished chain.
```

---

## Trace Analysis Checklist

### 1. Thought Quality
- ✓ Reasoning is logical and follows from previous observation
- ✓ Agent correctly identifies which tool to use
- ✗ Agent repeats same action without progress (stuck loop)
- ✗ Agent uses wrong tool for the task

### 2. Tool Selection
- ✓ Chosen tool matches the user's intent
- ✓ Tool parameters are well-formed JSON
- ✗ Missing required parameters
- ✗ Parameters have wrong types

### 3. Observation Handling
- ✓ Agent correctly interprets tool output
- ✓ Agent uses observation to inform next step
- ✗ Agent ignores observation
- ✗ Agent misunderstands observation

### 4. Final Answer
- ✓ Directly answers user's question
- ✓ Includes relevant details from observations
- ✓ Natural, conversational tone
- ✗ Incomplete or vague answer
- ✗ Contradicts observations

---

## Common Trace Patterns

### Pattern 1: Single Tool Call (Simple)

**Scenario**: User asks straightforward question

```
Thought: Need to search workouts
Action: search_workouts
Action Input: {"query": "push", "days": 7}
Observation: [3 workouts found]
Thought: Found the data, can answer
Final Answer: You did 3 push workouts last week...
```

**Analysis**: ✓ Efficient, direct path to answer

---

### Pattern 2: Multi-Tool Chain (Complex)

**Scenario**: User asks comparison question

```
Thought: Need bench press history
Action: get_exercise_history
Action Input: {"exercise": "bench press", "days": 90}
Observation: [12 sessions with weights]

Thought: Now need squat history to compare
Action: get_exercise_history
Action Input: {"exercise": "squat", "days": 90}
Observation: [10 sessions with weights]

Thought: Now can compare progression
Action: compare_exercises
Action Input: {"exercise1": "bench press", "exercise2": "squat"}
Observation: {"bench_trend": "increasing", "squat_trend": "stable", ...}

Thought: Have all data needed
Final Answer: Your bench press is increasing faster than squat...
```

**Analysis**: ✓ Logical sequence, each tool builds on previous

---

### Pattern 3: Stuck Loop (Error)

**Scenario**: Agent repeatedly uses same tool

```
Thought: Need to find bench press
Action: search_workouts
Action Input: {"query": "bench press", "days": 30}
Observation: []

Thought: Didn't find anything, try again
Action: search_workouts
Action Input: {"query": "bench press", "days": 30}
Observation: []

Thought: Still nothing, try one more time
Action: search_workouts
Action Input: {"query": "bench press", "days": 30}
Observation: []

[MAX_ITERATIONS reached]
```

**Analysis**: ✗ Agent stuck, needs better fallback logic

**Fix**: Agent should try different query or conclude no data exists

---

### Pattern 4: Wrong Tool Selection (Error)

**Scenario**: Agent uses inappropriate tool

```
User: "What should I do today?"

Thought: Need to find what exercises user did recently
Action: search_workouts  # ✗ WRONG - should use get_weekly_split_status
Action Input: {"query": "", "days": 7}
Observation: [All recent workouts]

Thought: Too much data, let me search again
Action: search_workouts  # ✗ Still wrong
...
```

**Analysis**: ✗ Agent doesn't understand question is about recommendations, not history

**Fix**: Router should classify as `recommend` intent, not `query`

---

## LangGraph Trace Format

### State-Based Tracing

LangGraph shows state transitions between nodes:

```
[Node: parse_notes]
Input State: {
  "raw_notes": "Did push: bench 3x8 at 135",
  "parsed_workout": null
}
Output State: {
  "raw_notes": "Did push: bench 3x8 at 135",
  "parsed_workout": {
    "type": "Push",
    "exercises": [...]
  }
}

[Node: confirm_with_user]
Input State: {
  "parsed_workout": {...}
}
Output State: {
  "parsed_workout": {...},
  "response": "I've parsed your workout as..."
}

[INTERRUPT - Waiting for user feedback]

[Node: save_workout]
Input State: {
  "user_feedback": "approve",
  "parsed_workout": {...}
}
Output State: {
  "saved": true,
  "parsed_workout": {"id": "2024-12-20-001", ...}
}
```

---

## Performance Metrics in Traces

### Timing Breakdown

```
Total execution time: 3.2s
├─ Thought generation: 1.5s (47%)
├─ Tool execution: 0.4s (12%)
│  ├─ search_workouts: 0.15s
│  └─ calculate_progression: 0.25s
└─ Final answer generation: 1.3s (41%)
```

**Red Flags**:
- Tool execution > 1s → Slow data access
- Thought generation > 3s → Complex reasoning or retries
- Final answer > 2s → Overly long response

---

## Debugging Trace Issues

### Issue 1: "Tool not found"

**Trace**:
```
Action: calculate_1rm  # ✗ Tool doesn't exist
Action Input: {"weight": 135, "reps": 8}
Error: Tool 'calculate_1rm' not found
```

**Fix**:
1. Check tool is in agent's tool list
2. Verify tool is properly exported
3. Check for typos in tool name

---

### Issue 2: "Invalid JSON in Action Input"

**Trace**:
```
Action: search_workouts
Action Input: query=bench, days=7  # ✗ Not JSON
Error: Invalid JSON format
```

**Fix**:
- Agent's prompt should specify JSON format
- Add examples to agent system prompt

---

### Issue 3: "Maximum iterations reached"

**Trace**:
```
[15 thought-action-observation cycles]
...
Error: Maximum iterations (15) reached without final answer
```

**Causes**:
- Stuck loop (agent not learning from observations)
- Impossible task (no data exists)
- Tool returning confusing output

**Fix**:
- Add max_iterations parameter to agent
- Improve tool output format
- Add fallback logic for "no data" cases

---

## Trace Comparison: Good vs Bad

### Good Trace Example

```
Thought: Clear reasoning
Action: Appropriate tool
Action Input: Well-formed JSON
Observation: Useful data
Thought: Builds on observation
Final Answer: Complete, accurate
```

**Characteristics**:
- 2-4 tool calls total
- Each step has clear purpose
- Observations are used effectively
- Answer directly addresses question

---

### Bad Trace Example

```
Thought: Vague reasoning
Action: Random tool selection
Action Input: Missing parameters
Observation: Error or irrelevant data
Thought: Ignores observation
Action: Repeats same tool
...
[Loop continues]
Final Answer: Incomplete or wrong
```

**Characteristics**:
- 10+ tool calls
- Stuck in loops
- Errors not handled
- Answer doesn't match observations

---

## Advanced: Custom Trace Handlers

### Logging Traces to File

```python
import logging
from langchain.callbacks import FileCallbackHandler

# Setup logging
logfile = 'agent_traces.log'
handler = FileCallbackHandler(logfile)

# Use with agent
agent = QueryAgent(callbacks=[handler])
response = agent.query("What did I bench?")

# Traces written to agent_traces.log
```

---

### Real-time Trace Monitoring

```python
from langchain.callbacks import StdOutCallbackHandler

# Verbose mode with stdout
agent = QueryAgent(verbose=True, callbacks=[StdOutCallbackHandler()])
response = agent.query("What did I bench?")
# Prints trace to console in real-time
```

---

For practical testing examples, see [TEST-EXAMPLES.md](TEST-EXAMPLES.md)
