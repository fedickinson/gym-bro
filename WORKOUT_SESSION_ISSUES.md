# Workout Session Issues & Fixes

## User Report

After creating workout from chat and completing it:

1. **Exercise Completion Unclear**:
   - Planned workout had X exercises
   - After completing them, system kept suggesting more
   - Unclear when the original plan was finished
   - "kept asking me to keep adding more"

2. **Weekly Split Not Updating**:
   - Before workout: "You have 2 Legs remaining this week"
   - After completing Legs workout: Still showed "2 Legs remaining"
   - Expected: Should show "1 Legs remaining"

---

## Root Cause Analysis

### Issue #1: Adaptive Suggestions Continue Indefinitely

**Location**: `src/agents/suggestion_engine.py:44-66`

**The Problem:**
```python
def suggest_next_exercise(session_state: dict, source: Literal["auto", "plan", "adaptive"] = "auto"):
    current_index = session_state.get('current_exercise_index', 0)
    plan_exercises = planned_template.get('exercises', [])

    # Auto-detect source
    if source == "auto":
        if current_index < len(plan_exercises):
            source = "plan"  # ✅ Suggest from plan
        else:
            source = "adaptive"  # ❌ Suggest ADDITIONAL exercises!

    if source == "adaptive":
        return _suggest_adaptive(...)  # Suggests exercises not in original plan
```

**What Happens:**
1. User creates session with 5 planned exercises
2. Completes exercises 1-5 (current_index goes from 0→1→2→3→4→5)
3. After exercise 5: `current_index = 5`, `len(plan_exercises) = 5`
4. Condition `current_index < len(plan_exercises)` → False
5. System switches to "adaptive" mode
6. **Starts suggesting exercises 6, 7, 8, ... indefinitely**

**Why It's Confusing:**
- No "✅ Plan Complete!" message
- Progress indicator shows "X exercises logged" without context
- User doesn't know if they're still on-plan or adding extras
- System treats "plan exhausted" as "keep suggesting more"

---

### Issue #2: Weekly Split Status

**Location**: `src/data.py:197-226` and `src/tools/recommend_tools.py:21-81`

**How It Works:**
1. `add_log()` saves workout (line 76)
2. Calls `_update_weekly_split_after_log()` (line 79)
3. Weekly split calculates status from actual saved workouts (line 51)

**Potential Causes:**

**Cause A: Timing/Caching**
- After save, user sees "What's Next?" suggestion
- That suggestion might use cached/old weekly split data
- User goes back to chat and checks - might still see old data

**Cause B: Wrong Workout Type**
- Session created as "Legs"
- User deviates during workout (does Push exercises)
- System correctly detects deviation and changes `actual_workout_type` to "Push"
- Workout saves as "Push" instead of "Legs"
- Weekly split correctly shows: Legs still at 0/2, Push at 1/1

**Cause C: Date Mismatch**
- Workout saved with wrong date
- Weekly split only counts workouts >= week_start (Monday)
- If date is wrong, workout not counted

---

## Proposed Fixes

### Fix #1A: Clear "Plan Complete" State

**File**: `src/agents/suggestion_engine.py`

**Change**: Return special "plan_complete" signal instead of auto-switching to adaptive

```python
def suggest_next_exercise(...):
    # ...

    if source == "auto":
        plan_exercises = planned_template.get('exercises', [])
        if current_index < len(plan_exercises):
            source = "plan"
        else:
            # ✅ Plan exhausted - return completion signal
            return {
                "source": "plan_complete",
                "exercise_name": None,
                "plan_complete": True,
                "total_planned": len(plan_exercises),
                "total_completed": len(accumulated),
                "reasoning": f"🎉 You've completed all {len(plan_exercises)} planned exercises!"
            }
```

**Impact**: System can now detect plan completion and show appropriate UI.

---

### Fix #1B: UI Improvements for Completion

**File**: `pages/1_Log_Workout.py:244-287`

**Current UI**:
```
Legs Session: 8 exercises logged
Next: Lateral Raise (4×12)  ← From adaptive mode, not in plan
```

**Improved UI**:
```
Legs Session: 5 of 5 planned exercises completed ✅
+ 3 bonus exercises

🎉 Original Plan Complete!

Options:
[ Finish Workout ]  (primary button)
[ Add More Exercises ]  (secondary)
```

**Changes Needed**:
1. **Progress indicator** (src/ui/session_components.py:165-176):
   ```python
   def render_session_progress(session: dict):
       num_accumulated = len(session.get('accumulated_exercises', []))
       planned_count = len(session.get('planned_template', {}).get('exercises', []))

       if num_accumulated < planned_count:
           st.caption(f"**Progress:** {num_accumulated}/{planned_count} planned exercises")
       elif num_accumulated == planned_count:
           st.success(f"✅ **Plan Complete!** {planned_count} exercises done")
       else:
           bonus = num_accumulated - planned_count
           st.success(f"✅ **Plan Complete!** {planned_count} exercises + {bonus} bonus")
   ```

2. **Completion decision point** (pages/1_Log_Workout.py):
   ```python
   if next_suggestion and next_suggestion.get('plan_complete'):
       # Show completion message
       st.success("🎉 You've completed your planned workout!")
       st.caption(f"{next_suggestion.get('total_planned')} exercises as planned")

       col1, col2 = st.columns(2)
       with col1:
           if st.button("✅ Finish Workout", type="primary", use_container_width=True):
               st.session_state.log_state = 'session_workout_review'
               st.rerun()

       with col2:
           if st.button("💪 Add More Exercises", use_container_width=True):
               # Force adaptive mode
               st.session_state.force_adaptive = True
               st.session_state.recording_mode = 'different'
               st.rerun()
   ```

---

### Fix #2: Debug Weekly Split Update

**File**: Create `tests/test_weekly_split_update.py`

```python
"""
Test to diagnose weekly split update issue.
"""

from src.data import add_log, get_weekly_split, get_weekly_split_status
from src.tools.recommend_tools import get_weekly_split_status as get_status_tool
from datetime import date

def test_weekly_split_updates_after_save():
    """
    Test that weekly split correctly updates after saving workout.
    """
    # Check initial state
    initial_status = get_status_tool.invoke({})
    initial_legs = initial_status.get('completed', {}).get('Legs', 0)

    print(f"Before save: Legs completed = {initial_legs}")

    # Create and save a Legs workout
    legs_workout = {
        "date": date.today().isoformat(),
        "type": "Legs",
        "exercises": [
            {"name": "Squat", "sets": [{"reps": 10, "weight_lbs": 135}]}
        ],
        "completed": True
    }

    log_id = add_log(legs_workout)
    print(f"Saved workout with ID: {log_id}")

    # Check updated state
    updated_status = get_status_tool.invoke({})
    updated_legs = updated_status.get('completed', {}).get('Legs', 0)

    print(f"After save: Legs completed = {updated_legs}")
    print(f"Full status: {updated_status}")

    # Assert
    assert updated_legs == initial_legs + 1, \
        f"Expected {initial_legs + 1}, got {updated_legs}"

    print("✅ TEST PASSED: Weekly split updated correctly!")

if __name__ == "__main__":
    test_weekly_split_updates_after_save()
```

**Run this to confirm split updates work.**

---

### Fix #2B: Force Split Refresh After Save

**File**: `pages/1_Log_Workout.py:625-641`

**Current** ("What's Next?" after save):
```python
try:
    suggestion = suggest_next_workout.invoke({})  # Might use cached data
    st.info(f"**Suggested:** {suggestion.get('suggested_type')}")
except:
    st.caption("Keep up the great work!")
```

**Improved** (explicit refresh):
```python
try:
    # Force fresh calculation (no caching)
    from src.tools.recommend_tools import get_weekly_split_status
    split_status = get_weekly_split_status.invoke({})

    st.subheader("This Week's Progress")
    completed = split_status.get('completed', {})
    targets = split_status.get('targets', {})

    for workout_type, target in targets.items():
        done = completed.get(workout_type, 0)
        st.write(f"{workout_type}: {done}/{target} {'✅' if done >= target else ''}")

    # Show suggestion
    suggestion = suggest_next_workout.invoke({})
    st.divider()
    st.info(f"**Next Suggested:** {suggestion.get('suggested_type')}")
    st.caption(suggestion.get('reason', ''))
except Exception as e:
    st.caption(f"Keep up the great work! (Error: {e})")
```

---

## Recommended Fix Order

1. **Fix #1B (UI Improvements)** - Quick win, improves UX immediately
2. **Fix #2B (Force Refresh)** - Quick, shows updated split after save
3. **Run diagnostic test** - Confirm split updates work
4. **Fix #1A (Plan Complete Signal)** - Requires more testing

---

## Testing Checklist

After implementing fixes:

- [ ] Create workout from chat with 5 exercises
- [ ] Complete all 5 exercises
- [ ] Verify "Plan Complete!" message shows
- [ ] Verify clear choice: "Finish" vs "Add More"
- [ ] Save workout
- [ ] Check weekly split shows updated count
- [ ] Return to chat
- [ ] Ask "what did I just do?" - should reflect saved workout
- [ ] Ask "what should I do?" - should show reduced remaining count

---

**Priority**: HIGH
**Complexity**: Medium (UI changes + logic fix)
**Impact**: High (core workout logging UX)
