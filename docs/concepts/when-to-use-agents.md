# When to Use Agents (And When Not To)

**Status**: Draft  
**Blog potential**: ⭐⭐⭐⭐⭐ (High - contrarian take on hot topic)

---

## The Concept

An **AI agent** is an LLM that can:
1. Decide what actions to take
2. Use tools to take those actions
3. Observe results and decide next steps
4. Loop until the task is complete

The key word is **decide**. If you know the exact steps in advance, you don't need an agent.

## Why It Matters

Agents are powerful but have costs:
- **Latency**: Multiple LLM calls in a loop
- **Cost**: More tokens = more money
- **Unpredictability**: The LLM decides the path
- **Debugging difficulty**: Hard to trace why it did X

The skill isn't building agents - it's knowing when they're the right tool.

## The Pattern Selection Framework

### Level 0: Direct LLM Call
```python
response = llm.invoke("What's the capital of France?")
```
**Use when**: Single question, no tools needed, no structure required.

### Level 1: Chain (Prompt → LLM → Parser)
```python
chain = prompt | llm | output_parser
result = chain.invoke({"input": user_message})
```
**Use when**: You need structured output, but the steps are fixed.

Example: Parse user's workout notes into JSON. The LLM extracts data, parser validates structure. No decisions needed.

### Level 2: Router + Chains
```python
# Classify intent, then route to appropriate chain
intent = router.classify(user_message)
if intent == "log":
    return log_chain.invoke(user_message)
elif intent == "chat":
    return chat_chain.invoke(user_message)
```
**Use when**: Different inputs need different handling, but each path is deterministic.

### Level 3: ReAct Agent (LLM + Tools + Loop)
```python
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
result = agent_executor.invoke({"input": user_message})
```
**Use when**: 
- Variable number of steps
- Need to choose between multiple tools
- Results of one step inform the next

Example: "Compare my bench progress to my squat progress" - agent needs to call `get_exercise_history` twice, then synthesize.

### Level 4: State Machine (LangGraph)
```python
workflow = StateGraph(State)
workflow.add_node("parse", parse_node)
workflow.add_node("confirm", confirm_node)
workflow.add_node("save", save_node)
workflow.add_conditional_edges("confirm", route_confirmation)
```
**Use when**:
- Multi-step workflows with branches
- Need to pause for human input
- Complex state that persists across steps
- Error handling and rollback needed

Example: Logging a workout - parse notes → show user for confirmation → handle approve/edit/cancel → save.

## My Decision Matrix

For my fitness coach, I mapped each feature:

| Feature | Needs Tools? | Variable Steps? | Human-in-Loop? | Pattern |
|---------|--------------|-----------------|----------------|---------|
| Chat | No | No | No | Simple Chain |
| Log Workout | Yes (parse) | Yes (confirm flow) | Yes | LangGraph |
| Query History | Yes | Yes (depends on question) | No | ReAct Agent |
| Recommendations | Yes | Yes (check split, history) | No | ReAct Agent |
| Edit/Delete | No | No | Yes (confirm) | Simple Chain |

## Common Mistakes

### Mistake 1: Agent for everything
"Let's make an agent that handles all user requests!"

Problem: The agent has to figure out intent AND execute. Two jobs = more failure modes.

**Better**: Router classifies intent, then dispatches to specialized handlers.

### Mistake 2: One mega-tool
```python
@tool
def handle_fitness_query(query: str) -> str:
    """Handles any fitness-related query."""
    # 500 lines of logic
```

Problem: LLM can't reason about when to use it. Too vague.

**Better**: Small, focused tools with clear purposes.

### Mistake 3: No human oversight for important actions
"The agent parses the workout and saves it directly."

Problem: LLM might misinterpret. User has no chance to correct.

**Better**: Parse → confirm → save. Worth the extra step.

### Mistake 4: Agents for deterministic flows
If you KNOW the steps: A → B → C → D, don't use an agent to "figure out" those steps. Just code them.

Agents are for when the path depends on intermediate results.

## Resources

- [LangChain Conceptual Guide](https://python.langchain.com/docs/concepts/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629) - The reasoning + acting pattern
- [Building Effective Agents (Anthropic)](https://www.anthropic.com/research/building-effective-agents)

---

## Pull Quote for Blog

> "The agent hype is real, but the skill isn't building agents—it's knowing when a simple chain would work better. Use the simplest pattern that solves the problem."
