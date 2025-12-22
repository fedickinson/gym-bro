# Development Log & Learning Journal

This directory contains my learning journey building an agentic AI application.

## Purpose

1. **Learn by documenting** - Writing clarifies thinking
2. **Build portfolio content** - Each entry can become a blog post
3. **Interview prep** - Real examples with context and decisions
4. **Help others** - Share what I learn

## Structure

```
docs/
├── README.md           # This file
├── devlog/             # Daily/session logs
│   ├── 001-project-setup.md
│   ├── 002-first-agent.md
│   └── ...
├── concepts/           # Deep dives on concepts I learned
│   ├── when-to-use-agents.md
│   ├── langgraph-state-machines.md
│   └── ...
├── decisions/          # Architecture Decision Records (ADRs)
│   ├── 001-why-langchain.md
│   ├── 002-json-vs-database.md
│   └── ...
└── blog-drafts/        # Polished posts ready to publish
    └── ...
```

## Devlog Template

Each devlog entry follows this structure:
- **Date & Session**: When and how long
- **Goal**: What I tried to accomplish
- **What I Did**: Steps taken
- **What I Learned**: Key insights
- **Stuck Points**: Where I struggled (and how I solved it)
- **Next Steps**: What's next
- **Blog Potential**: Could this become a post? What angle?

## Concept Deep Dive Template

For concepts worth explaining:
- **The Concept**: What is it?
- **Why It Matters**: When would you use this?
- **How It Works**: Technical explanation
- **My Example**: How I used it in this project
- **Common Mistakes**: What to avoid
- **Resources**: Where to learn more

## Decision Record Template

For architecture decisions:
- **Decision**: What we decided
- **Context**: Why this decision was needed
- **Options Considered**: What alternatives existed
- **Decision**: What we chose and why
- **Consequences**: Trade-offs, what this enables/prevents

---

## Blog Post Ideas (Generated as I go)

### Beginner-Friendly
- [ ] "I Built an AI Fitness Coach - Here's What I Learned"
- [ ] "When NOT to Use AI Agents (And What to Use Instead)"
- [ ] "My First LangGraph App: A Step-by-Step Walkthrough"

### Technical Deep Dives
- [ ] "Router → Agent → Chain: Designing Practical AI Architectures"
- [ ] "Human-in-the-Loop with LangGraph: Beyond Simple Chatbots"
- [ ] "Tool Design for LLM Agents: Lessons from Building 10 Tools"

### Career/Portfolio
- [ ] "How I Used a Side Project to Learn Agentic AI"
- [ ] "From Tutorials to Production: Building Real AI Apps"

---

## Resume Bullets (Draft as I go)

**AI Application Developer** - Personal Project
- Designed multi-agent architecture using LangChain/LangGraph, implementing router-based intent classification with specialized ReAct agents for queries and recommendations
- Built human-in-the-loop workflow using LangGraph state machines for workout logging with parse-confirm-save flow
- Created 10+ composable tools for workout tracking, progression analysis, and weekly split management
- Reduced "agent sprawl" by applying appropriate patterns: simple chains for chat, ReAct for complex queries, LangGraph for stateful workflows

---

## LinkedIn Post Templates

### "I learned something" post:
```
🧠 TIL: [Concept]

I'm building an AI fitness coach and just figured out [insight].

The key realization: [one sentence]

Here's what that looks like in practice:
[brief example]

#AI #LangChain #BuildInPublic
```

### "I built something" post:
```
🚀 Just shipped: [Feature]

[Screenshot or diagram]

The interesting part: [technical insight]

What I'd do differently: [reflection]

#AI #Python #BuildInPublic
```
