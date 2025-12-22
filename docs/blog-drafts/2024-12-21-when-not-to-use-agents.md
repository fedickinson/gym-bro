# When NOT to Use AI Agents (And What to Use Instead)

**Status**: Draft  
**Target**: Dev.to, Medium, or personal blog  
**Word count target**: 1,500-2,000  
**Hook**: Contrarian take on hot topic

---

## Opening Hook

Everyone's building AI agents. LangChain, CrewAI, AutoGPT—the ecosystem is exploding. But here's what I learned building an AI fitness coach: **most features don't need agents**.

I started with five features to build. Only two actually needed agents. The rest? Simple chains worked better—faster, cheaper, more predictable.

Here's the framework I developed for deciding when to use agents and when to reach for simpler patterns.

---

## The Problem With "Agent Everything"

Agents are powerful. An LLM that can:
1. Decide what to do
2. Use tools to do it
3. Observe results
4. Loop until done

That's impressive. It's also:
- **Slow**: Multiple LLM calls per request
- **Expensive**: More tokens = more cost
- **Unpredictable**: The LLM decides the path
- **Hard to debug**: Why did it call that tool three times?

The skill isn't building agents. It's knowing when they're the right tool.

---

## A Real Example: My Fitness Coach

I'm building an AI fitness coaching app. It needs to handle:

1. **Chat**: General conversation, motivation, questions
2. **Log Workouts**: Parse natural language into structured data
3. **Answer Queries**: "What did I bench last week?"
4. **Recommendations**: "What should I do today?"
5. **Admin**: Edit or delete existing logs

My first instinct: build an agent that handles everything!

My second thought: wait, do all of these need an agent?

---

## The Pattern Selection Framework

I developed a simple decision tree:

```
Does it need tools?
├── No → Simple Chain (prompt → LLM → response)
└── Yes → Does the number of steps vary?
    ├── No → Chain with tools (fixed sequence)
    └── Yes → Does it need to pause for human input?
        ├── No → ReAct Agent (LLM decides tool use)
        └── Yes → State Machine (LangGraph)
```

Let's apply this to each feature:

### 1. Chat → Simple Chain
- Needs tools? **No** (just conversation)
- Pattern: Prompt → LLM → Response

```python
chat_chain = prompt | llm | StrOutputParser()
response = chat_chain.invoke({"input": user_message})
```

Done. No agent needed.

### 2. Log Workouts → LangGraph State Machine
- Needs tools? **Yes** (parse natural language)
- Variable steps? **Yes** (depends on what needs confirmation)
- Human input? **Yes** (user should confirm before saving)

This is the complex one. The flow:
```
parse_notes → show_preview → [approve/edit/cancel] → save → respond
```

An agent would work, but a state machine is more predictable. I know exactly what states exist and what transitions are allowed.

### 3. Answer Queries → ReAct Agent
- Needs tools? **Yes** (search history, calculate stats)
- Variable steps? **Yes** ("What did I bench?" vs "Compare my bench to squat progress over 6 months")

This is where agents shine. The simple query needs one tool call. The complex one needs multiple. Let the agent figure it out.

```python
agent = create_react_agent(llm, query_tools, prompt)
```

### 4. Recommendations → ReAct Agent
- Needs tools? **Yes** (check weekly progress, get templates)
- Variable steps? **Yes** (simple suggestion vs detailed planning)

Same pattern as queries. Agent with recommendation-focused tools.

### 5. Admin → Simple Chain
- Needs tools? **Kind of** (but it's just CRUD)
- Variable steps? **No** (edit is edit, delete is delete)

The "tools" here are just database operations with known signatures. A structured chain with confirmation works better than an agent.

---

## The Scorecard

| Feature | Pattern | Why NOT Agent? |
|---------|---------|----------------|
| Chat | Simple Chain | No tools needed |
| Log | LangGraph | Need predictable state machine |
| Query | ReAct Agent | ✓ Variable tool use |
| Recommend | ReAct Agent | ✓ Variable tool use |
| Admin | Simple Chain | Fixed operations |

**Result**: 2 out of 5 features use agents. 60% of my app is simpler patterns.

---

## The Benefits of Simpler Patterns

### Faster Response Times
Simple chain: 1 LLM call
ReAct agent: 2-5+ LLM calls

For chat, I want sub-second responses. An agent would add unnecessary latency.

### Lower Costs
Each LLM call costs money. Agents multiply those calls. For high-traffic features, this adds up.

### Easier Debugging
When a chain fails, I know exactly where. When an agent fails, I'm tracing through a reasoning loop.

### More Predictable
Chains do what you program. Agents do what they "think" is right. For data operations, I want predictable.

---

## When TO Use Agents

Agents are the right choice when:

1. **The number of steps genuinely varies**
   - "What did I do yesterday?" (1 tool call)
   - "Analyze my progress and compare to last quarter" (5+ tool calls)

2. **The tools needed depend on the question**
   - Might need search, might need calculation, might need both

3. **The LLM's reasoning adds value**
   - Synthesizing information from multiple sources
   - Making judgment calls about relevance

4. **You can tolerate the latency and cost**
   - Not every request, but some requests

---

## Practical Takeaways

### 1. Start with the simplest pattern
Try a chain first. Add agent capabilities only when the chain can't handle the variability.

### 2. Use a router
Classify intent first, then dispatch to specialized handlers. Don't make one agent do everything.

```python
intent = router.classify(user_input)
handlers = {
    "chat": chat_chain,
    "log": log_workflow,
    "query": query_agent,
    "recommend": recommend_agent,
}
return handlers[intent].invoke(user_input)
```

### 3. Design focused tools
Bad: `handle_everything(query: str)`
Good: `get_exercise_history(exercise: str, days: int)`

Small, focused tools are easier for agents to use correctly.

### 4. Consider state machines for multi-step flows
If you need human-in-the-loop, branching logic, or rollback—LangGraph is often better than a free-form agent.

---

## Conclusion

The agent hype is real, and agents are genuinely powerful. But the real skill is knowing when simpler patterns work better.

My fitness coach uses agents for 2 of 5 features. The other 3 are faster, cheaper, and more reliable because I chose the right pattern for the job.

Before you build an agent, ask: "Could a chain do this?"

Often, the answer is yes.

---

## About the Project

[Link to GitHub]
[Link to demo]

I'm building in public and documenting my learnings. Follow along: [Twitter/LinkedIn]

---

## Notes for Editing

- [ ] Add code snippets for each pattern
- [ ] Include timing/cost comparison if I can measure it
- [ ] Add architecture diagram
- [ ] Get feedback on tone (too preachy?)
- [ ] Shorten intro?
