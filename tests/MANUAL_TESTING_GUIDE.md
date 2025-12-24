# Manual Testing Guide: Chat-Workout Integration

## ✅ Automated Tests Results
All programmatic tests passed successfully:
- ✅ Chat history queries (using Query tools)
- ✅ Chat recommendations (using Recommend tools)
- ✅ Session creation from chat
- ✅ Orchestrator integration
- ✅ No false session creation

## 🧪 Manual UI Tests

The Streamlit app should be running at: http://localhost:8502

### Test 1: Chat History Query Flow
**Objective**: Verify ChatAgent uses tools to answer questions about workout history

1. Navigate to **Chat** page
2. Clear chat history (sidebar button)
3. Type: `"What did I bench last week?"`
4. **Expected Result**:
   - Agent responds with actual bench press data
   - Response shows weights and reps from recent history
   - No "Continue to Workout" button appears
   - Sidebar shows tool was called (if dev mode enabled)

5. Try another query: `"Show me my squat progression"`
6. **Expected Result**:
   - Agent analyzes progression data
   - Mentions trends, PRs, or progress
   - No workout session created

**Status**: [ ] PASS / [ ] FAIL

---

### Test 2: Chat Recommendation Flow
**Objective**: Verify ChatAgent provides workout recommendations based on weekly split

1. Clear chat history
2. Type: `"What should I train today?"`
3. **Expected Result**:
   - Agent checks weekly split status
   - Recommends workout based on rotation and targets
   - Mentions what's done vs. what's remaining this week
   - No session created yet (just a suggestion)

4. Try: `"Am I behind on any muscle groups?"`
5. **Expected Result**:
   - Agent analyzes weekly split balance
   - Lists muscle groups that need attention
   - Provides context (e.g., "0/2 legs done this week")

**Status**: [ ] PASS / [ ] FAIL

---

### Test 3: Workout Session Creation
**Objective**: Verify session is created and navigation button appears

1. Clear chat history
2. Type: `"Let's do a push workout"`
3. **Expected Result**:
   - Agent responds: "I've created your Push workout..."
   - Lists exercises in the plan
   - Mentions clicking button to continue
   - **Green "Continue to Workout →" button appears** below chat
   - Button is large, prominent, primary type
   - Shows workout type and exercise count above button

4. Verify button text shows: `"🏋️ Continue to Workout →"`
5. **DO NOT CLICK YET** - proceed to Test 4

**Status**: [ ] PASS / [ ] FAIL

---

### Test 4: Navigation to Workout Logging
**Objective**: Verify navigation works and session data transfers

1. From Test 3 above (with button visible)
2. **Click**: `"Continue to Workout →"` button
3. **Expected Result**:
   - Navigates to **Log Workout** page
   - Page shows "Planning Your Workout" or session active state
   - Workout template is loaded with exercises
   - All exercises from chat are present
   - Can modify plan (add/remove exercises, change weights)

4. Verify you can interact with the workout:
   - Try modifying an exercise
   - Verify chat modifications persist

**Status**: [ ] PASS / [ ] FAIL

---

### Test 5: Session Trigger Phrases
**Objective**: Verify all trigger phrases create sessions

**Test these phrases** (clear history between each):

| Phrase | Should Create Session? | Expected Workout Type |
|--------|------------------------|----------------------|
| "let's start" | ✅ Yes | AI-suggested |
| "let's begin" | ✅ Yes | AI-suggested |
| "I want to do legs" | ✅ Yes | Legs |
| "start workout session" | ✅ Yes | AI-suggested |
| "I'm ready to workout" | ✅ Yes | AI-suggested |
| "turn this into a workout" | ✅ Yes | AI-suggested |

For each phrase:
1. Type the phrase
2. Verify agent calls `start_workout_session`
3. Verify button appears
4. Verify session is created

**Status**: [ ] PASS / [ ] FAIL

---

### Test 6: No False Session Creation
**Objective**: Verify casual conversation doesn't create sessions

**Test these phrases** (should NOT create sessions):

| Phrase | Should Create Session? |
|--------|------------------------|
| "Hey, how are you?" | ❌ No |
| "Thanks for the help!" | ❌ No |
| "What is progressive overload?" | ❌ No |
| "I'm feeling tired today" | ❌ No |
| "Tell me about rest days" | ❌ No |

For each phrase:
1. Type the phrase
2. Verify agent responds conversationally
3. Verify **NO** "Continue to Workout" button appears
4. Verify chat_initiated_workout flag stays False

**Status**: [ ] PASS / [ ] FAIL

---

### Test 7: Session Conflict Detection
**Objective**: Verify system prevents creating multiple sessions simultaneously

**Part A: Session from Chat**
1. Start fresh (reload page)
2. Go to **Chat** page
3. Type: `"Let's do push"`
4. Verify session created, button appears
5. Type: `"Actually, let's do legs instead"`
6. **Expected Result**:
   - System should either:
     - Replace existing session with new one, OR
     - Ask user to cancel current session first
   - Should NOT crash or create duplicate sessions

**Part B: Session from Log Workout Page**
1. Navigate to **Log Workout** page
2. Start a workout session there (click "Start New Workout")
3. Navigate back to **Chat** page
4. Type: `"Let's start a workout"`
5. **Expected Result**:
   - System should detect existing active session
   - Should NOT overwrite without warning
   - Should provide option to continue or cancel existing

**Status**: [ ] PASS / [ ] FAIL

---

### Test 8: Equipment Constraints
**Objective**: Verify equipment unavailable parameter works

1. Clear chat history
2. Type: `"I want to workout but no barbell today"`
3. **Expected Result**:
   - Agent creates session avoiding barbell exercises
   - Response mentions adapting to equipment constraint
   - Template uses dumbbells, cables, machines instead
   - Button appears for navigation

4. Click through to Log Workout
5. Verify no barbell exercises in template

**Status**: [ ] PASS / [ ] FAIL

---

### Test 9: Cancel Workout Button
**Objective**: Verify user can cancel session before navigating

1. Create session from chat: `"Let's do push"`
2. Verify button appears
3. Look for `"❌ Cancel Workout"` button (should be below main button)
4. **Click**: Cancel Workout
5. **Expected Result**:
   - Button disappears
   - Session cleared
   - Can create new session
   - No navigation occurred

**Status**: [ ] PASS / [ ] FAIL

---

### Test 10: Chat History Preservation
**Objective**: Verify chat history persists after session creation

1. Have a conversation:
   - `"How are you?"`
   - `"What did I do last week?"`
   - `"What should I train today?"`
   - `"Let's start a push workout"`

2. **Expected Result**:
   - All messages visible in chat history
   - Session button appears at bottom
   - Can scroll up to see previous conversation
   - History preserved even after navigation

**Status**: [ ] PASS / [ ] FAIL

---

## 🐛 Issues Found

Document any issues discovered during testing:

### Issue Template
```
**Issue #**:
**Test**:
**Expected**:
**Actual**:
**Severity**: Critical / High / Medium / Low
**Steps to Reproduce**:
1.
2.
3.

**Error Messages** (if any):

**Screenshots** (if applicable):
```

---

## 📊 Test Summary

**Date**: ________________
**Tester**: ________________
**Build/Commit**: ________________

| Test | Status | Notes |
|------|--------|-------|
| 1. Chat History Query | [ ] | |
| 2. Chat Recommendations | [ ] | |
| 3. Session Creation | [ ] | |
| 4. Navigation Flow | [ ] | |
| 5. Trigger Phrases | [ ] | |
| 6. No False Sessions | [ ] | |
| 7. Session Conflicts | [ ] | |
| 8. Equipment Constraints | [ ] | |
| 9. Cancel Button | [ ] | |
| 10. Chat History | [ ] | |

**Overall Result**: [ ] All Pass / [ ] Some Failures

**Ready for Production?**: [ ] Yes / [ ] No / [ ] With Caveats

---

## 🚀 Next Steps

If all tests pass:
- [ ] Commit remaining changes
- [ ] Update documentation
- [ ] Create demo video
- [ ] Get user feedback

If issues found:
- [ ] Document all issues
- [ ] Prioritize by severity
- [ ] Create fix plan
- [ ] Retest after fixes
