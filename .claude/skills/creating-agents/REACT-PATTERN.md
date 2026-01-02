# ReAct Agent Pattern

**Reference**: `/Users/franklindickinson/Projects/gym-bro/src/agents/query_agent.py`

## Complete Example: QueryAgent

```python
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from src.tools.query_tools import QUERY_TOOLS

QUERY_AGENT_PROMPT = """You are a fitness data analyst helping users explore their workout history.

Your job: Answer questions about the user's workout data using the tools available to you.

Your tools:
- search_workouts: Find workouts by keyword, exercise, or type
- get_exercise_history: Get weight/rep history for a specific exercise
- calculate_progression: Calculate stats like trend, PR, and avg increase
- compare_exercises: Compare progression between two exercises
- get_workout_count: Count workouts in a time period

Guidelines:
- Use tools to find accurate data
- Provide specific numbers (weights, reps, dates)
- If no data found, say so clearly
- Compare against user's goals when relevant

User input: {input}

{agent_scratchpad}
"""

class QueryAgent:
    """Answers questions about workout history using data tools."""

    def __init__(self):
        self.llm = ChatAnthropic(model="claude-sonnet-4-5-20250514", temperature=0)
        self.prompt = ChatPromptTemplate.from_template(QUERY_AGENT_PROMPT)
        self.agent = create_react_agent(self.llm, QUERY_TOOLS, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=QUERY_TOOLS,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15
        )

    def query(self, user_input: str, chat_history: list = None) -> str:
        """Query workout history data."""
        result = self.executor.invoke({"input": user_input})
        return result["output"]
```

## Key Components

1. **Agent Prompt**: Defines role, tools, guidelines
2. **LLM**: `claude-sonnet-4-5-20250514` with `temperature=0` for consistency
3. **Tools List**: Import from tools module
4. **AgentExecutor**: Handles tool calling loop with error handling

## Parameters to Adjust

- `temperature`: 0 for factual, higher for creative
- `max_iterations`: Prevents infinite loops (10-15 typical)
- `handle_parsing_errors`: True for robustness
- `verbose`: True for debugging, False for production
