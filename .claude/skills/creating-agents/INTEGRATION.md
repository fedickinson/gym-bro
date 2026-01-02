# Agent Integration Checklist

## Step-by-Step Integration

### 1. Create Agent File
- [ ] Create `src/agents/my_agent.py` or `src/chains/my_chain.py`
- [ ] Follow pattern (ReAct/LangGraph/Chain)
- [ ] Test agent independently

### 2. Update Main Orchestrator
```python
# src/agents/main.py

from src.agents.my_agent import MyAgent  # ADD IMPORT

class GymBroOrchestrator:
    def __init__(self):
        # ... existing ...
        self.my_agent = MyAgent()  # ADD INITIALIZATION

    def _route_to_handler(self, intent: str, user_input: str, chat_history=None):
        # ... existing routes ...

        elif intent == "my_intent":  # ADD ROUTE
            response = self.my_agent.execute(user_input)
            return ("my_agent", response, None)

        # ... rest ...
```

### 3. Update Intent Router
```python
# src/agents/router.py

ROUTER_PROMPT = """...

Classify into one of these intents:

- **log**: ... [existing]
- **query**: ... [existing]
- **recommend**: ... [existing]
- **admin**: ... [existing]
- **chat**: ... [existing]
- **my_intent**: [NEW - describe when to use]
  Examples: [provide 2-3 example queries]

...
"""

# Optional: Add quick route patterns
QUICK_PATTERNS = {
    "log": ["just did", ...],
    "query": ["what did i", ...],
    "my_intent": ["keyword1", "keyword2"],  # NEW
    ...
}
```

### 4. Test Integration
```python
# test_integration.py
from src.agents.main import GymBroOrchestrator
from dotenv import load_dotenv

load_dotenv()

orchestrator = GymBroOrchestrator()

# Test routing
response, metadata = orchestrator.process_message("query that should trigger my_intent")

print(f"Intent: {metadata['intent']}")  # Should be "my_intent"
print(f"Handler: {metadata['handler']}")  # Should be "my_agent"
print(f"Response: {response}")
```

### 5. Update Documentation
- [ ] Add agent to `exploring-codebase/AGENTS.md`
- [ ] Document tools in `exploring-codebase/TOOLS.md` (if new tools)
- [ ] Update `CLAUDE.md` architecture diagram

### 6. Verify Complete Integration
- [ ] Agent works standalone
- [ ] Router classifies intent correctly
- [ ] Orchestrator routes to agent
- [ ] Agent returns proper response
- [ ] Error handling works
- [ ] Logging/tracing works

## Common Issues

**Issue**: "Agent not found"
- Check import statement in main.py
- Verify agent class name matches

**Issue**: "Intent never triggers"
- Check ROUTER_PROMPT includes new intent
- Test quick_route patterns
- Verify intent name matches in _route_to_handler

**Issue**: "Agent returns None"
- Check agent's execute/query method returns string
- Verify return statement in agent

## Testing Checklist

- [ ] Test intent classification
- [ ] Test agent with valid inputs
- [ ] Test agent with edge cases
- [ ] Test error handling
- [ ] Test with chat history (if applicable)
- [ ] Test performance (response time)
