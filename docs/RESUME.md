# Resume & Portfolio Tracker

Living document to capture accomplishments as the project progresses.

---

## Project Summary (for resume)

**AI Fitness Coach** | Personal Project | Dec 2024 - Present
- Building conversational fitness tracking app with agentic AI architecture
- Tech: Python, LangChain, LangGraph, Claude API, Streamlit

---

## Resume Bullets (Draft)

### Architecture & Design
- [ ] Designed multi-agent architecture using LangChain/LangGraph, implementing intent-based routing with specialized handlers for logging, queries, and recommendations
- [ ] Built pattern selection framework choosing between chains, ReAct agents, and state machines based on task complexity and requirements
- [ ] Architected human-in-the-loop workflows using LangGraph for data entry confirmation, reducing input errors

### Tool Design
- [ ] Created 10+ composable LLM tools for workout tracking, progression analysis, and training balance assessment
- [ ] Implemented weekly split tracking system with rotation-aware workout suggestions

### Data & Integration
- [ ] Designed JSON-based data layer with exercise normalization and fuzzy matching for flexible input parsing
- [ ] Built historical data import pipeline processing 70+ workout sessions from unstructured markdown logs

### Learning & Documentation
- [ ] Documented architecture decisions and learning journey as technical blog content
- [ ] Applied "build in public" methodology, producing [X] blog posts from development process

---

## Skills to Highlight

### Technical Skills (from this project)
- [x] LangChain / LangGraph
- [x] AI Agent Design
- [x] Prompt Engineering
- [x] Python
- [x] Pydantic
- [ ] Streamlit
- [x] Claude API
- [ ] State Machine Design

### Soft Skills (demonstrated)
- Architecture decision-making
- Pattern selection (knowing when NOT to use agents)
- Technical documentation
- Learning in public

---

## Interview Story Bank

### Story 1: Architecture Decision
**Situation**: Needed to add intelligent features to a simple fitness app
**Task**: Decide between raw API calls vs framework
**Action**: Evaluated options, chose LangChain for patterns + portfolio value
**Result**: Cleaner architecture, transferable skills, demonstrable project

### Story 2: When NOT to Use Agents
**Situation**: Building features for fitness coach app
**Task**: Implement chat, logging, queries, recommendations
**Action**: Analyzed each feature, chose simplest viable pattern for each
**Result**: Only 2 of 5 features needed agents; others used simpler chains

### Story 3: Human-in-the-Loop Design
**Situation**: Users entering workouts via natural language
**Task**: Parse and save data accurately
**Action**: Built LangGraph workflow with confirm step before saving
**Result**: User can review/edit parsed data, preventing errors

### Story 4: Tool Design Philosophy
**Situation**: Agents need tools to query workout data
**Task**: Design effective tools
**Action**: Created focused, single-purpose tools with clear inputs/outputs
**Result**: Agent reliably selects and uses tools; easy to debug

---

## Portfolio Pieces

### Code Samples to Highlight
1. Intent router with LangChain
2. LangGraph workflow with human-in-the-loop
3. ReAct agent with custom tools
4. Tool design examples

### Blog Posts (planned)
1. "When NOT to Use AI Agents"
2. "Building Human-in-the-Loop with LangGraph"
3. "Tool Design for LLM Agents"

### Demos
- [ ] Screen recording of the app in action
- [ ] Architecture diagram
- [ ] Before/after comparison (simple vs agentic)

---

## Quantifiable Metrics (fill in as measured)

- Workout sessions tracked: ___
- Historical data imported: 70+ sessions
- Tools built: 10+
- Agent patterns implemented: 3 (router, ReAct, LangGraph)
- Blog posts published: ___
- Lines of code: ___

---

## Update Log

| Date | Update |
|------|--------|
| 2024-12-21 | Initial architecture decisions, pattern selection framework |
| | |
| | |
