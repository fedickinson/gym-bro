"""
Workout Logging Graph - Multi-step workflow with human-in-the-loop.

This is the MOST COMPLEX pattern we'll use - a LangGraph with:
- State management (shared memory)
- Multiple nodes (parse, confirm, save)
- Conditional edges (branch based on user choice)
- Human-in-the-loop (pause for confirmation)

Analogy: Like a GPS navigation system
- Shows you the route (parsed workout)
- Waits for you to confirm (human-in-the-loop)
- Adjusts based on your choice (conditional routing)
- Can recalculate if you make a wrong turn (edit loop)

Why not a Chain?
- Chains can't pause mid-process for user input
- Chains can't branch or loop back

Why not an Agent?
- Agents make autonomous decisions
- We need explicit human approval before saving data
- Too risky to let AI decide what to save!
"""

from typing import TypedDict, Literal
from datetime import date
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from src.models import WorkoutLog, Exercise, Set, Warmup
from src.data import add_log


# ============================================================================
# State Definition (The Shared Clipboard)
# ============================================================================

class LogWorkoutState(TypedDict):
    """
    The state that gets passed between nodes.

    Think of this as a clipboard that each department fills out:
    - User writes the raw notes
    - Parser fills out structured data
    - User reviews and approves/edits
    - Saver fills out the final result
    """
    # Input from user
    raw_notes: str  # "bench 135x8x3, overhead 95x8x3"

    # Parsed workout (structured)
    parsed_workout: dict | None  # {"date": "...", "exercises": [...]}

    # User feedback
    user_choice: Literal["approve", "edit", "cancel"] | None
    edit_instructions: str | None  # "Actually it was 145 lbs"

    # Results
    saved: bool
    workout_id: str | None
    response: str  # What to tell the user


# ============================================================================
# Pydantic Models for Parsing (Structured Output)
# ============================================================================

class ParsedSet(BaseModel):
    """A single set within an exercise."""
    reps: int | None = Field(None, description="Number of repetitions (null if not specified)")
    weight_lbs: float | None = Field(None, description="Weight in pounds (null if not specified)")


class ParsedExercise(BaseModel):
    """An exercise with its sets."""
    name: str = Field(description="Exercise name (e.g., 'Bench Press')")
    sets: list[ParsedSet] = Field(description="List of sets")


class ParsedWorkout(BaseModel):
    """The complete parsed workout."""
    date: str = Field(description="Workout date (YYYY-MM-DD), default to today")
    workout_type: str = Field(description="Type: Push, Pull, Legs, Upper, Lower, or Other")
    exercises: list[ParsedExercise] = Field(description="List of exercises")
    notes: str | None = Field(None, description="Any additional notes")


# ============================================================================
# Node 1: Parse Notes (LLM Extraction)
# ============================================================================

PARSE_PROMPT = """You are a workout data extractor. Parse the user's workout notes into structured data.

User's notes: {raw_notes}

Extract:
- Date (default to today if not mentioned): {today}
- Workout type (Push, Pull, Legs, Upper, Lower, or Other)
- Exercises with sets (reps and weight)
- Any additional notes

Common abbreviations:
- "x8" or "8 reps" = 8 repetitions
- "x3" or "3 sets" = 3 sets
- "135" or "135lbs" = 135 pounds
- "bench" = Bench Press
- "ohp" or "overhead" = Overhead Press

Example:
"bench 135x8x3" → Bench Press: 3 sets of 8 reps at 135 lbs

IMPORTANT: If exercise details are missing (like reps or weight not specified), use reasonable defaults:
- If only exercise name mentioned: assume 3 sets of 10 reps
- If no weight mentioned: set weight_lbs to null

{format_instructions}
"""


def parse_notes(state: LogWorkoutState) -> LogWorkoutState:
    """
    Node 1: Parse raw notes into structured workout data.

    Input: state["raw_notes"] = "bench 135x8x3, overhead 95x8"
    Output: state["parsed_workout"] = {exercises: [...], date: "...", ...}

    This is like the receptionist filling out a form based on what you said.
    """
    print("\n🔍 Parsing workout notes...")

    # Set up LLM and parser
    # Note: Tested Haiku (47% accuracy) - too many JSON formatting issues
    # Keeping Sonnet for reliable parsing
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    parser = PydanticOutputParser(pydantic_object=ParsedWorkout)

    prompt = ChatPromptTemplate.from_template(PARSE_PROMPT)
    chain = prompt | llm | parser

    # Parse the notes
    try:
        parsed = chain.invoke({
            "raw_notes": state["raw_notes"],
            "today": date.today().isoformat(),
            "format_instructions": parser.get_format_instructions()
        })

        # Convert to dict for state
        state["parsed_workout"] = {
            "date": parsed.date,
            "type": parsed.workout_type,
            "exercises": [
                {
                    "name": ex.name,
                    "sets": [{"reps": s.reps, "weight_lbs": s.weight_lbs} for s in ex.sets]
                }
                for ex in parsed.exercises
            ],
            "notes": parsed.notes
        }

        print(f"✅ Parsed: {len(parsed.exercises)} exercises")

    except Exception as e:
        print(f"❌ Parse error: {e}")
        state["response"] = f"Sorry, I couldn't parse that workout. Error: {str(e)}"
        state["user_choice"] = "cancel"

    return state


# ============================================================================
# Node 2: Confirm with User (Show Preview)
# ============================================================================

def confirm_with_user(state: LogWorkoutState) -> LogWorkoutState:
    """
    Node 2: Show parsed workout and prepare for user confirmation.

    This node generates a preview message.
    The actual waiting happens in the graph's interrupt point!

    This is like showing you the form before you sign it.
    """
    print("\n📋 Generating preview for user confirmation...")

    parsed = state["parsed_workout"]

    if not parsed:
        state["response"] = "No workout data to confirm."
        return state

    # Build a nice preview message
    preview_lines = [
        f"**Date**: {parsed['date']}",
        f"**Type**: {parsed['type']}",
        "",
        "**Exercises**:"
    ]

    for ex in parsed["exercises"]:
        sets_summary = []
        for s in ex["sets"]:
            if s.get("weight_lbs"):
                sets_summary.append(f"{s['reps']} @ {s['weight_lbs']} lbs")
            else:
                sets_summary.append(f"{s['reps']} reps")

        preview_lines.append(f"  • {ex['name']}: {', '.join(sets_summary)}")

    if parsed.get("notes"):
        preview_lines.append(f"\n**Notes**: {parsed['notes']}")

    preview_lines.append("\n**Is this correct?**")
    preview_lines.append("(Reply: 'approve' to save, 'edit: <changes>' to modify, 'cancel' to abort)")

    state["response"] = "\n".join(preview_lines)

    print("✅ Preview generated")

    return state


# ============================================================================
# Node 3: Save to Database
# ============================================================================

def save_workout(state: LogWorkoutState) -> LogWorkoutState:
    """
    Node 3: Save the approved workout to the database.

    Only called if user approved!

    This is like filing the signed form in the filing cabinet.
    """
    print("\n💾 Saving workout to database...")

    parsed = state["parsed_workout"]

    if not parsed:
        state["response"] = "No workout data to save."
        return state

    try:
        # Save to database
        workout_id = add_log(parsed)

        state["saved"] = True
        state["workout_id"] = workout_id
        state["response"] = f"✅ Workout saved! (ID: {workout_id})\n\n{state['response']}"

        print(f"✅ Saved workout: {workout_id}")

    except Exception as e:
        state["saved"] = False
        state["response"] = f"❌ Error saving workout: {str(e)}"
        print(f"❌ Save error: {e}")

    return state


# ============================================================================
# Node 4: Handle Cancellation
# ============================================================================

def cancel_workout(state: LogWorkoutState) -> LogWorkoutState:
    """
    Node 4: Handle user cancellation.

    This is like throwing away the form if the user changes their mind.
    """
    print("\n🚫 Workout logging cancelled")

    state["saved"] = False
    state["response"] = "Workout logging cancelled. No data was saved."

    return state


# ============================================================================
# Conditional Edge: Where to Go After Confirmation?
# ============================================================================

def route_after_confirmation(state: LogWorkoutState) -> str:
    """
    Decide where to go based on user's choice.

    This is like a traffic light:
    - Green (approve) → Go to "save"
    - Yellow (edit) → Go back to "parse"
    - Red (cancel) → Go to "cancel"

    Returns:
        The name of the next node to visit
    """
    choice = state.get("user_choice")

    if choice == "approve":
        return "save"
    elif choice == "edit":
        # If user wants to edit, we need to re-parse with new instructions
        if state.get("edit_instructions"):
            # Append edit instructions to raw notes
            state["raw_notes"] += f"\n\nCorrection: {state['edit_instructions']}"
        return "parse"
    else:  # cancel
        return "cancel"


# ============================================================================
# Build the Graph
# ============================================================================

def build_log_graph():
    """
    Build the workout logging graph.

    Flow:
        START
          ↓
        parse_notes (extract structure)
          ↓
        confirm_with_user (show preview)
          ↓
        [INTERRUPT - Wait for user]
          ↓
        route_after_confirmation (decide where to go)
          ↓
        ┌────────┬──────────┬────────┐
        ↓        ↓          ↓        ↓
      save    parse     cancel     END
                 ↑
                 └─ (loop back if editing)
    """
    # Create the graph
    workflow = StateGraph(LogWorkoutState)

    # Add nodes
    workflow.add_node("parse", parse_notes)
    workflow.add_node("confirm", confirm_with_user)
    workflow.add_node("save", save_workout)
    workflow.add_node("cancel", cancel_workout)

    # Add edges
    workflow.add_edge("parse", "confirm")  # Always go to confirm after parsing

    # Conditional edge after confirmation
    workflow.add_conditional_edges(
        "confirm",
        route_after_confirmation,
        {
            "save": "save",
            "parse": "parse",  # Loop back for edits
            "cancel": "cancel"
        }
    )

    # End edges
    workflow.add_edge("save", END)
    workflow.add_edge("cancel", END)

    # Set entry point
    workflow.set_entry_point("parse")

    # Compile the graph
    graph = workflow.compile()

    return graph


# ============================================================================
# Convenience Functions
# ============================================================================

def start_workout_log(raw_notes: str) -> dict:
    """
    Start the workout logging process.

    Args:
        raw_notes: User's workout description

    Returns:
        State dict with preview message

    Example:
        result = start_workout_log("bench 135x8x3, overhead 95x8")
        print(result["response"])  # Shows preview
        # User then calls continue_workout_log with their choice
    """
    graph = build_log_graph()

    initial_state = {
        "raw_notes": raw_notes,
        "parsed_workout": None,
        "user_choice": None,
        "edit_instructions": None,
        "saved": False,
        "workout_id": None,
        "response": ""
    }

    # Run until first interrupt (after confirm node)
    result = graph.invoke(initial_state)

    return result


def continue_workout_log(state: dict, user_choice: str, edit_instructions: str | None = None) -> dict:
    """
    Continue the workout logging after user feedback.

    Args:
        state: The state from start_workout_log
        user_choice: "approve", "edit", or "cancel"
        edit_instructions: If editing, what to change

    Returns:
        Final state with save result

    Example:
        # Start
        state = start_workout_log("bench 135x8")
        print(state["response"])  # Preview

        # User approves
        final = continue_workout_log(state, "approve")
        print(final["response"])  # "✅ Workout saved!"
    """
    state["user_choice"] = user_choice
    if edit_instructions:
        state["edit_instructions"] = edit_instructions

    graph = build_log_graph()

    # Continue from where we left off
    result = graph.invoke(state)

    return result


# ============================================================================
# Quick Test
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of the log graph.
    Run: python -m src.agents.log_graph
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("=" * 70)
    print("🏋️  GYM BRO - WORKOUT LOGGING GRAPH TEST")
    print("=" * 70)

    # Test 1: Parse and preview
    print("\n📝 Test 1: Parsing workout notes")
    print("-" * 70)

    raw_notes = "Did push today - bench 135x8x3, overhead 95x8x3, tricep pushdowns"

    print(f"Input: {raw_notes}\n")

    state = start_workout_log(raw_notes)

    print("\n" + "=" * 70)
    print("PREVIEW:")
    print("=" * 70)
    print(state["response"])

    # Simulate approval (in real app, user would click button)
    print("\n" + "=" * 70)
    print("🧪 Simulating user approval...")
    print("=" * 70)

    final_state = continue_workout_log(state, "approve")

    print("\n" + "=" * 70)
    print("FINAL RESULT:")
    print("=" * 70)
    print(final_state["response"])
    print(f"\nSaved: {final_state['saved']}")
    if final_state.get("workout_id"):
        print(f"Workout ID: {final_state['workout_id']}")
