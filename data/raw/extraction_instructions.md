# Trainerize PDF Extraction Instructions

## Context

I'm building a fitness tracking system. I have 25 phases of workout data exported as PDFs from Trainerize. Each phase contains workout templates and (sometimes) logged session data with actual weights/reps performed.

**Your job:** Extract all structured data from each PDF I upload and output it as clean markdown that I can save.

---

## What to Extract

For each phase, extract:

### 1. Phase Metadata
- Phase number
- Date range
- Duration (weeks)
- Total number of workout templates in phase

### 2. Workout Templates
- Workout name (e.g., "3.1 Push")
- Exercises in order
- Sets × reps (target)
- Rest periods
- Equipment needed
- Any supersets (note which exercises are grouped, rounds, and rest after)
- Estimated duration

### 3. Logged Sessions (if present in "Previous Stats")
- Date performed
- Which workout template was used
- Exercise name
- Actual sets/reps/weight for each set
- Jog data: distance, time, speed, incline, calories

---

## Output Format

Generate a single markdown file per phase using this structure:

```markdown
# Phase [X]
**Date Range:** [start] - [end]  
**Duration:** [X] weeks  
**Total Workouts:** [X]

---

## Workout Templates

### [Workout Name]
**Equipment:** [list]  
**Est. Duration:** [X] minutes

| Exercise | Sets × Reps | Rest |
|----------|-------------|------|
| ... | ... | ... |

**Supersets:**
- [Exercise A] + [Exercise B] (3 rounds, 90s rest after pair)

---

## Logged Sessions

### [Date]
**Workout:** [Name]

| Exercise | Set 1 | Set 2 | Set 3 | Set 4 |
|----------|-------|-------|-------|-------|
| [Name] | 8 × 45lbs | 8 × 45lbs | 8 × 45lbs | — |

---
```

---

## Data Entry Error Corrections

**Important:** The Trainerize export contains data entry errors. Fix obvious mistakes based on context and patterns. Common errors to watch for and correct:

| Error Type | Example | Fix | How to Identify |
|------------|---------|-----|-----------------|
| Extra digit in reps | 104 × 40lbs | 10 × 40lbs | Reps way higher than other sets |
| Missing decimal in distance | 55 miles | 0.55 miles | All jogs are ~0.5 miles |
| Extra digit in time | 52:20 | 5:20 | All jogs are ~5 minutes |
| Missing zero in weight | 6lbs, 7lbs | 60lbs, 70lbs | Weight impossibly light for exercise |
| Single rep typo | 1 × 35lbs | 10 × 35lbs | Other sets have 10+ reps |
| Reversed format | 3 × 12lbs | 12 × 30lbs | Format shows sets × weight instead of reps × weight |

### Correction Guidelines

1. **Compare to other sets in same exercise** - If 3 sets are "10 × 40lbs" and one is "104 × 40lbs", it's a typo
2. **Compare to same exercise on other days** - Establish typical weight/rep ranges
3. **Use exercise-appropriate weights** - Lat pulldowns aren't done at 6lbs, lateral raises aren't done at 100lbs
4. **Jog patterns** - Distance ~0.45-0.55 miles, time ~5:00-6:00, speed 5.5-6, incline 1-4
5. **When uncertain** - Use the most conservative reasonable correction, or note it with [?]

---

## Process

1. I'll upload one phase PDF at a time
2. You extract and output the markdown with corrections applied
3. I'll save it as `phase_XX.md`
4. Repeat for all 25 phases

---

## Additional Notes

- If a phase has no logged sessions, note: `*No logged sessions found*`
- Preserve exercise names exactly as written (we'll normalize later)
- Capture partial sessions too (even if incomplete)
- Use "—" for empty set columns
- For supersets, list all exercises in the group and note rest period
- Sort logged sessions by date (most recent first, or chronologically - be consistent)
