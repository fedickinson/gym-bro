# ADR 001: LangChain/LangGraph Over Raw API Calls

**Date**: December 21, 2024  
**Status**: Accepted  
**Deciders**: Franklin  

---

## Context

Building a fitness coaching AI application. Started with direct Anthropic API calls in a simple Streamlit app. Now need to add more sophisticated features:
- Intent classification and routing
- Multi-step workflows with human confirmation
- Tool-using agents for queries and recommendations

Need to decide: continue with raw API calls or adopt a framework?

## Options Considered

### Option 1: Raw Anthropic API
Continue using `anthropic.Anthropic()` directly.

**Pros**:
- Full control
- No framework to learn
- Minimal dependencies

**Cons**:
- Must implement tool calling, parsing, loops manually
- No built-in patterns for agents, chains, graphs
- More boilerplate code
- Harder to switch models later

### Option 2: LangChain + LangGraph
Use LangChain for chains/agents, LangGraph for stateful workflows.

**Pros**:
- Industry standard (good for portfolio)
- Built-in patterns: ReAct agents, tool handling, output parsing
- LangGraph handles state machines elegantly
- Easy model switching (Claude, GPT, local models)
- Large community, good docs

**Cons**:
- Learning curve
- Abstraction can hide what's happening
- Framework lock-in (somewhat)
- Extra dependencies

### Option 3: Other Frameworks (Haystack, LlamaIndex, CrewAI)
Use alternative agent frameworks.

**Pros**:
- Some are simpler (CrewAI)
- Some specialize in retrieval (LlamaIndex)

**Cons**:
- Smaller communities
- Less transferable knowledge
- CrewAI is multi-agent focused (overkill for this)
- LlamaIndex is retrieval-focused (not our main need)

## Decision

**Adopt LangChain + LangGraph**

Primary reasons:
1. **Portfolio value**: LangChain is what employers search for
2. **Right patterns built-in**: ReAct agents, output parsers, tool decorators
3. **LangGraph for workflows**: The log confirmation flow needs state machine semantics
4. **Future flexibility**: Can swap Claude for other models easily

## Consequences

### Positive
- Professional architecture to demonstrate
- Learn patterns that transfer to other projects
- Faster implementation of complex features
- Better debugging with LangSmith (optional)

### Negative
- Need to learn LangChain idioms
- Some simple things become more verbose
- Framework updates may require code changes

### Mitigations
- Keep business logic separate from LangChain code
- Write clear documentation of patterns used
- Pin dependency versions

---

## Notes

This decision was partly driven by the portfolio/resume goal. If this were a production app at a company with existing patterns, we'd evaluate differently.

The key learning: **framework choice should consider team skills, existing patterns, AND career goals** when it's a personal project.
