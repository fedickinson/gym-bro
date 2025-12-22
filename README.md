# 🏋️ AI Fitness Coach

A conversational fitness tracking app built with **LangChain**, **LangGraph**, and **Claude**. Demonstrates practical agentic AI architecture—using agents where they add value, simpler patterns where they don't.

> **Note**: This is a learning project built in public. See [ROADMAP.md](ROADMAP.md) for development status.

---

## Features

### Core Features
- **Natural Language Logging**: "Did push today - bench 135x8, incline 40x10, tricep pushdowns"
- **Audio Recording**: Record workouts via voice at the gym
- **Intelligent Queries**: "What's my bench press PR?" / "Compare my squat to deadlift progress"
- **Smart Recommendations**: "What should I do today?" (considers weekly split, recent workouts, muscle balance)
- **Progress Tracking**: Visualize trends, PRs, and training balance
- **Weekly Split Awareness**: Tracks Push/Pull/Legs rotation and suggests based on what's missing

### 🎯 Adaptive Coaching (NEW!)
- **Pattern Learning**: Learns which exercises you actually do vs skip
- **Personalized Weights**: Suggests weights based on YOUR progression history
- **Volume Adjustment**: Matches your typical training volume
- **Coaching Insights**: Explains WHY each weight is suggested
- **Progression Tracking**: Detects when to increase, maintain, or deload

### 🛠️ Dev Mode
- **Chat Log Export**: Export conversations as JSON or Markdown for debugging
- **Metadata Capture**: Timestamps, agents used, errors for full context
- See [DEV_MODE.md](DEV_MODE.md) for details

---

## Architecture

This project intentionally uses **different patterns for different tasks**:

| Feature | Pattern | Why |
|---------|---------|-----|
| Log Workout | **LangGraph** | Multi-step with human confirmation |
| Query History | **ReAct Agent** | Variable complexity, needs tools |
| Recommendations | **ReAct Agent** | Needs reasoning over multiple data sources |
| General Chat | **Simple Chain** | Just conversation, no tools needed |

```
User Input
    │
    ▼
┌─────────────────┐
│  Intent Router  │  ← Classifies: log | query | recommend | chat
└─────────────────┘
    │
    ├─→ Log Graph (LangGraph)     → parse → confirm → save
    ├─→ Query Agent (ReAct)       → tools: search, history, progression
    ├─→ Recommend Agent (ReAct)   → tools: weekly split, balance check
    └─→ Chat Chain (Simple)       → direct LLM response
```

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.

---

## Tech Stack

- **LangChain** - Agent orchestration and chains
- **LangGraph** - Stateful workflow for logging
- **Claude API** - LLM (Anthropic)
- **Streamlit** - Web UI
- **Pydantic** - Data validation

---

## Quick Start

```bash
# Clone
git clone https://github.com/fedickinson/gym-bro.git
cd gym-bro

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "OPENAI_API_KEY=sk-proj-..." >> .env  # For audio transcription
echo "DEV_MODE=true" >> .env  # Optional: Enable dev tools

# Run
streamlit run app.py
```

**Live Demo**: [https://gym-bro-o.streamlit.app/](https://gym-bro-o.streamlit.app/)

---

## Project Structure

```
fitness-coach/
├── app.py                 # Streamlit entry
├── src/
│   ├── agents/            # Router, ReAct agents, LangGraph
│   ├── chains/            # Simple LLM chains
│   ├── tools/             # Agent tools (search, recommend, etc.)
│   ├── data.py            # JSON data layer
│   └── models.py          # Pydantic models
├── data/                  # JSON storage
└── pages/                 # Streamlit pages
```

---

## Key Learnings

### 1. Not Everything Needs an Agent
Agents are powerful but add latency, cost, and unpredictability. A simple chain often works better.

### 2. Router First
Classify intent, then dispatch to specialized handlers. Don't make one agent do everything.

### 3. Tools Should Be Focused
Small, single-purpose tools are easier for agents to use correctly than large multi-purpose ones.

### 4. Human-in-the-Loop for Data Entry
LangGraph makes it easy to pause for confirmation before saving parsed data.

---

## Development Status

See [ROADMAP.md](ROADMAP.md) for detailed progress.

- [x] Phase 1: Foundation (models, data layer, tools)
- [ ] Phase 2: Agents & Chains
- [ ] Phase 3: LangGraph Workflow
- [ ] Phase 4: Streamlit UI
- [ ] Phase 5: Historical Data Import
- [ ] Phase 6: Polish

---

## Documentation

- [CLAUDE.md](CLAUDE.md) - Technical architecture and design decisions
- [ROADMAP.md](ROADMAP.md) - Development plan and status
- [docs/](docs/) - Learning journal and blog drafts

---

## License

MIT

---

## Author

Built by Franklin as a learning project to explore agentic AI patterns.

*Building in public: [Twitter/LinkedIn handle]*
