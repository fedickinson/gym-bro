# Learning-in-Public Workflow

A practical system for turning project work into portfolio content.

---

## The Core Loop

```
Build → Document → Reflect → Share
  ↑                           ↓
  ←←←←←←← Feedback ←←←←←←←←←←
```

### 1. Build (30-90 min sessions)
- Work on one focused thing
- Keep a scratch pad open for notes
- When stuck, write down the problem

### 2. Document (10-15 min after each session)
- Fill in devlog template while it's fresh
- Capture the "aha" moments
- Note what confused you (others will have the same confusion)

### 3. Reflect (weekly, 30 min)
- Review devlogs from the week
- Identify patterns and themes
- Extract concepts worth deep-diving
- Update the blog ideas list

### 4. Share (when ready)
- Polish one devlog into a blog post
- Post a LinkedIn update
- Update resume bullets

---

## Capturing the Right Things

### What to write down DURING coding:
- Commands that didn't work (and what fixed them)
- Error messages you googled
- "I wish I knew this earlier" moments
- Decisions and why you made them

### What to write AFTER coding:
- What you were trying to do
- What you actually did
- What surprised you
- What you'd do differently

### What makes good content:
- Specific problems with specific solutions
- Contrarian takes backed by experience
- Mistakes you made and learned from
- Mental models that clicked

---

## From Devlog to Blog Post

### Step 1: Find a devlog with potential
Look for entries with:
- A clear problem → solution arc
- A non-obvious insight
- Something you struggled with that others will too

### Step 2: Identify the angle
Ask: "What would make someone click on this?"
- "I was wrong about X"
- "Everyone says Y, but actually Z"
- "How to do X (the non-obvious way)"
- "I built X, here's what I learned"

### Step 3: Outline for humans
```
1. Hook (the problem or question)
2. Context (why this matters)
3. The journey (what you tried)
4. The insight (what worked)
5. The takeaway (so what?)
```

### Step 4: Add value others can use
- Code snippets they can copy
- Diagrams they can reference
- Checklist or framework they can apply

---

## Resume Integration

### Keep a running "wins" list
After each session, ask:
- Did I solve a technical challenge?
- Did I make an architecture decision?
- Did I learn a new tool/pattern?
- Did I build something demonstrable?

### Translate wins to bullets
**Weak**: "Used LangChain"
**Strong**: "Designed multi-agent architecture using LangChain, implementing intent router with specialized handlers reducing response latency by 40%"

Formula: `[Action verb] + [What you built] + [How you built it] + [Impact/Result]`

---

## LinkedIn Posting Cadence

### Weekly options (pick one):
1. **Learning post**: One insight from the week
2. **Progress post**: What you shipped
3. **Question post**: Something you're figuring out

### Monthly:
1. **Milestone post**: Summary of progress
2. **Blog share**: Link to published article

### Template: The "I learned" post
```
🧠 Building in public: Week [N] of my AI fitness coach

This week I learned: [one insight]

The problem: [what I was trying to do]
The solution: [what worked]

Key takeaway: [generalizable lesson]

Next up: [what's coming]

#AI #LangChain #BuildInPublic #Python
```

---

## File Naming Conventions

### Devlogs
`NNN-short-description.md`
- `001-project-setup.md`
- `002-first-agent.md`
- `003-langgraph-workflow.md`

### Concepts
`topic-name.md`
- `when-to-use-agents.md`
- `tool-design-patterns.md`
- `human-in-the-loop.md`

### Decisions
`NNN-decision-name.md`
- `001-langchain-over-raw-api.md`
- `002-json-over-database.md`

### Blog drafts
`YYYY-MM-DD-title.md`
- `2024-12-21-when-not-to-use-agents.md`

---

## Quick Reference: What to Capture

| Moment | Where to Put It |
|--------|-----------------|
| Something I did | Devlog → "What I Did" |
| Something I learned | Devlog → "What I Learned" |
| Something that confused me | Devlog → "Stuck Points" |
| A decision I made | decisions/ folder |
| A concept I now understand | concepts/ folder |
| Something worth sharing | Blog ideas list |
| A quantifiable win | Resume bullets |

---

## Remember

> "The best time to document is right after you figure something out, when the confusion is fresh and the solution is clear."

> "Your struggles are content. The thing that took you 2 hours to debug? That's a blog post."

> "Write for yourself 6 months ago. That person is your audience."
