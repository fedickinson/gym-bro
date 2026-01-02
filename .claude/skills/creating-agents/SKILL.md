---
name: creating-agents
description: Scaffolds new agents following ReAct, LangGraph, or Simple Chain patterns. Use when adding new agent types, building workflows, or extending the orchestrator with new capabilities.
---

# Agent Builder

## Pattern Decision Tree

```
What type of task?
├─ Need tools + reasoning? → ReAct Agent
├─ Multi-step with state? → LangGraph Workflow
└─ Simple prompting? → Simple Chain
```

## Quick Agent Creation Workflow

Copy this checklist:

```
Agent Creation:
- [ ] Step 1: Choose pattern (ReAct/LangGraph/Chain)
- [ ] Step 2: Define requirements (name, intent, tools)
- [ ] Step 3: Generate agent structure
- [ ] Step 4: Update orchestrator (main.py)
- [ ] Step 5: Update router (router.py)
- [ ] Step 6: Test agent
```

---

## Pattern 1: ReAct Agent

**Use when**: Variable complexity tasks requiring tools and reasoning

**Example**: QueryAgent, RecommendAgent

### Template

```python
# src/agents/my_agent.py

from langchain_anthropic import ChatAnthropic
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from src.tools.my_tools import MY_TOOLS

AGENT_PROMPT = """You are a [role description].

Your job: [what this agent does]

Your tools:
- tool1: [description]
- tool2: [description]

Important notes:
- [Key constraint 1]
- [Key constraint 2]

User input: {input}

{agent_scratchpad}
"""

class MyAgent:
    """[Brief description]."""

    def __init__(self):
        self.llm = ChatAnthropic(model="claude-sonnet-4-5-20250514", temperature=0)
        self.prompt = ChatPromptTemplate.from_template(AGENT_PROMPT)
        self.agent = create_react_agent(self.llm, MY_TOOLS, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=MY_TOOLS,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15
        )

    def execute(self, user_input: str, chat_history: list = None) -> str:
        """Execute agent with user input."""
        result = self.executor.invoke({"input": user_input})
        return result["output"]
```

**Reference**: See [REACT-PATTERN.md](REACT-PATTERN.md) for complete example

---

## Pattern 2: LangGraph Workflow

**Use when**: Multi-step process with human-in-the-loop or complex state

**Example**: SessionGraph, LogGraph

### Template

```python
# src/agents/my_workflow.py

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# State Definition
class MyWorkflowState(TypedDict):
    """State for my workflow."""
    input_data: str
    processed_data: dict | None
    user_action: Literal["approve", "edit", "cancel"] | None
    saved: bool
    response: str | None

# Node Functions
def process_input(state: MyWorkflowState) -> MyWorkflowState:
    """Process the input data."""
    # TODO: Implement processing
    state["processed_data"] = {"result": "processed"}
    return state

def confirm_with_user(state: MyWorkflowState) -> MyWorkflowState:
    """Generate confirmation message for user."""
    state["response"] = f"Processed: {state['processed_data']}"
    return state

def save_result(state: MyWorkflowState) -> MyWorkflowState:
    """Save the result."""
    # TODO: Implement saving
    state["saved"] = True
    return state

# Routing Logic
def route_after_confirm(state: MyWorkflowState) -> str:
    """Route based on user action."""
    action = state.get("user_action")
    if action == "approve":
        return "save"
    elif action == "edit":
        return "process"
    else:
        return "end"

# Graph Construction
def build_my_workflow():
    """Build the workflow graph."""
    workflow = StateGraph(MyWorkflowState)

    # Add nodes
    workflow.add_node("process", process_input)
    workflow.add_node("confirm", confirm_with_user)
    workflow.add_node("save", save_result)

    # Add edges
    workflow.set_entry_point("process")
    workflow.add_edge("process", "confirm")
    workflow.add_conditional_edges("confirm", route_after_confirm, {
        "save": "save",
        "process": "process",
        "end": END
    })
    workflow.add_edge("save", END)

    return workflow.compile()
```

**Reference**: See [LANGGRAPH-PATTERN.md](LANGGRAPH-PATTERN.md) for complete example

---

## Pattern 3: Simple Chain

**Use when**: Straightforward prompting without tools or state

**Example**: ChatChain

### Template

```python
# src/chains/my_chain.py

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

CHAIN_PROMPT = """You are a [role].

[Instructions...]

User: {input}
"""

class MyChain:
    """[Brief description]."""

    def __init__(self):
        self.llm = ChatAnthropic(model="claude-sonnet-4-5-20250514")
        self.prompt = ChatPromptTemplate.from_template(CHAIN_PROMPT)
        self.chain = self.prompt | self.llm

    def execute(self, user_input: str) -> str:
        """Execute chain with user input."""
        result = self.chain.invoke({"input": user_input})
        return result.content
```

---

## Integration Steps

### Step 1: Update Orchestrator

```python
# src/agents/main.py

from src.agents.my_agent import MyAgent  # NEW IMPORT

class GymBroOrchestrator:
    def __init__(self):
        # ... existing agents ...
        self.my_agent = MyAgent()  # NEW AGENT

    def _route_to_handler(self, intent: str, user_input: str, chat_history=None):
        # ... existing routes ...

        elif intent == "my_intent":  # NEW ROUTE
            response = self.my_agent.execute(user_input, chat_history)
            return ("my_agent", response, None)
```

### Step 2: Update Router

```python
# src/agents/router.py

ROUTER_PROMPT = """...

- **my_intent**: [When to use this intent]
  Examples: [example queries]

...
"""

# Add to quick patterns
QUICK_PATTERNS = {
    "my_intent": ["keyword1", "keyword2", "phrase"],
    # ... existing patterns ...
}
```

### Step 3: Test Agent

```python
# test_my_agent.py
from src.agents.my_agent import MyAgent
from dotenv import load_dotenv

load_dotenv()

agent = MyAgent()
response = agent.execute("test query")
print(response)
```

---

## Pattern Selection Guide

| Task | Pattern | Complexity | Example |
|------|---------|------------|---------|
| Answer history questions | ReAct | Medium | QueryAgent |
| Plan workouts | ReAct | Medium | RecommendAgent |
| Conversation with tools | ReAct | High | ChatAgent |
| Multi-step logging | LangGraph | High | LogGraph |
| Session management | LangGraph | Very High | SessionGraph |
| Simple responses | Chain | Low | ChatChain |

---

## Example: Create Nutrition Query Agent

### Requirements
- **Name**: NutritionAgent
- **Pattern**: ReAct (needs tools)
- **Intent**: `nutrition_query`
- **Tools**: `get_meal_logs`, `calculate_macros`, `get_nutrition_stats`
- **Purpose**: Answer questions about nutrition data

### Step 1: Create Tools

```python
# src/tools/nutrition_tools.py

from langchain_core.tools import tool

@tool
def get_meal_logs(days: int = 7) -> list[dict]:
    """Get meal logs from last N days."""
    # TODO: Implement
    return []

@tool
def calculate_macros(meal_id: str) -> dict:
    """Calculate macros for a meal."""
    # TODO: Implement
    return {"protein": 0, "carbs": 0, "fats": 0}

NUTRITION_TOOLS = [get_meal_logs, calculate_macros]
```

### Step 2: Create Agent

```python
# src/agents/nutrition_agent.py

from langchain_anthropic import ChatAnthropic
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from src.tools.nutrition_tools import NUTRITION_TOOLS

NUTRITION_AGENT_PROMPT = """You are a nutrition data analyst.

Your job: Answer questions about meal logs and nutritional data.

Your tools:
- get_meal_logs: Get meal history
- calculate_macros: Calculate protein/carbs/fats

User input: {input}

{agent_scratchpad}
"""

class NutritionAgent:
    """Answers questions about nutrition data."""

    def __init__(self):
        self.llm = ChatAnthropic(model="claude-sonnet-4-5-20250514", temperature=0)
        self.prompt = ChatPromptTemplate.from_template(NUTRITION_AGENT_PROMPT)
        self.agent = create_react_agent(self.llm, NUTRITION_TOOLS, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=NUTRITION_TOOLS,
            verbose=True,
            max_iterations=10
        )

    def query(self, user_input: str) -> str:
        """Query nutrition data."""
        result = self.executor.invoke({"input": user_input})
        return result["output"]
```

### Step 3: Integrate

See [INTEGRATION.md](INTEGRATION.md) for complete integration checklist.

---

## Reference Files

- [REACT-PATTERN.md](REACT-PATTERN.md) - Complete ReAct example
- [LANGGRAPH-PATTERN.md](LANGGRAPH-PATTERN.md) - Complete LangGraph example
- [INTEGRATION.md](INTEGRATION.md) - Integration checklist

For testing agents, use the `testing-agents` skill.
