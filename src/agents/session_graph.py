"""
Session-Based Workout Logging Graph.

LangGraph workflow for incremental workout logging where users add exercises
one at a time during their workout.
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from datetime import datetime, date
import uuid

from src.data import add_log
from src.tools.recommend_tools import suggest_next_workout, get_workout_template


# ============================================================================
# State Definition
# ============================================================================

class SessionWorkoutState(TypedDict):
    """State for session-based workout logging workflow."""
    # Session management
    session_id: str
    intended_type: str  # "Push", "Pull", "Legs", etc.
    accumulated_exercises: list[dict]  # All exercises logged so far

    # Current exercise being added
    current_exercise_input: str | None
    current_parsed_exercise: dict | None

    # User actions
    user_action: Literal["add_another", "finish", "cancel"] | None

    # Final workout
    saved: bool
    workout_id: str | None
    response: str | None


class SessionWithPlanState(TypedDict):
    """Enhanced session state with AI planning and adaptation."""
    # Session metadata
    session_id: str
    started_at: str  # ISO datetime
    last_activity_at: str

    # AI Planning (Pre-workout)
    suggested_type: str  # Push/Pull/Legs from recommend agent
    suggestion_reason: str  # Why this type was suggested
    planned_template: dict  # Original adaptive template
    plan_adjustments: list[dict]  # Chat-based modifications
    # [{timestamp, user_message, ai_response, template_change}]

    # Equipment constraints
    equipment_available: list[str] | None  # ["dumbbells", "cables", "barbell"]
    equipment_unavailable: list[str] | None  # ["smith machine"]

    # During workout
    actual_workout_type: str  # May differ from suggested_type if user deviates
    accumulated_exercises: list[dict]  # What user actually logged
    current_exercise_index: int  # Position in plan (0-based)

    # Current exercise being added
    current_exercise_input: str | None
    current_parsed_exercise: dict | None

    # User actions
    user_action: Literal["add_another", "finish", "cancel", "adapt_plan", "continue_plan"] | None

    # Final workout
    saved: bool
    workout_id: str | None
    response: str | None


# ============================================================================
# Node Functions
# ============================================================================

def parse_exercise(state: SessionWorkoutState) -> SessionWorkoutState:
    """
    Parse a single exercise from raw input.

    Reuses the existing parse_notes logic from log_graph.py but for single exercises.
    """
    from src.agents.log_graph import parse_notes

    raw_input = state.get("current_exercise_input", "")

    if not raw_input:
        return {
            **state,
            "current_parsed_exercise": None,
            "response": "No input provided"
        }

    try:
        # Use existing parse_notes logic
        # Create a temporary state for parsing
        parse_state = {
            "raw_notes": raw_input,
            "parsed_workout": None
        }

        # Parse the input
        result = parse_notes(parse_state)

        # Extract the parsed workout
        parsed_workout = result.get("parsed_workout")

        if not parsed_workout:
            return {
                **state,
                "current_parsed_exercise": None,
                "response": "Could not parse exercise"
            }

        # Extract first exercise (should be single exercise input)
        exercises = parsed_workout.get("exercises", [])

        if not exercises:
            return {
                **state,
                "current_parsed_exercise": None,
                "response": "No exercise found in input"
            }

        # Take the first exercise
        exercise = exercises[0]

        # Check if exercise name is meaningful
        exercise_name = exercise.get('name', 'Unknown')
        if exercise_name in ['Unknown', 'Unknown Exercise', '']:
            return {
                **state,
                "current_parsed_exercise": None,
                "response": "Could not identify the exercise name. Please include the exercise name (e.g., 'Bench press, 3 sets of 10 reps at 135 lbs')"
            }

        return {
            **state,
            "current_parsed_exercise": exercise,
            "response": f"Parsed: {exercise_name}"
        }

    except Exception as e:
        return {
            **state,
            "current_parsed_exercise": None,
            "response": f"Error parsing: {str(e)}"
        }


def accumulate_exercise(state: SessionWorkoutState) -> SessionWorkoutState:
    """
    Add the current parsed exercise to the accumulated list.
    """
    current_exercise = state.get("current_parsed_exercise")

    if not current_exercise:
        return state

    # Add to accumulated exercises
    accumulated = state.get("accumulated_exercises", []).copy()
    accumulated.append(current_exercise)

    # Update last activity time
    # Note: We'll persist to disk here in the actual implementation

    return {
        **state,
        "accumulated_exercises": accumulated,
        "current_exercise_input": None,  # Clear for next exercise
        "current_parsed_exercise": None,
        "response": f"Added exercise: {current_exercise.get('name')}"
    }


def save_session_workout(state: SessionWorkoutState) -> SessionWorkoutState:
    """
    Save the complete workout session to workout_logs.json.
    """
    session_id = state.get("session_id")
    intended_type = state.get("intended_type")
    exercises = state.get("accumulated_exercises", [])

    if not exercises:
        return {
            **state,
            "saved": False,
            "response": "No exercises to save"
        }

    try:
        # Create workout log
        workout_log = {
            "date": date.today().isoformat(),
            "type": intended_type,  # For Phase 1, use intended type as-is
            "exercises": exercises,
            "notes": f"Session logged incrementally (Session ID: {session_id})",
            "completed": True
        }

        # Save to data store
        log_id = add_log(workout_log)

        return {
            **state,
            "saved": True,
            "workout_id": log_id,
            "response": f"Workout saved! {len(exercises)} exercises logged."
        }

    except Exception as e:
        return {
            **state,
            "saved": False,
            "response": f"Error saving workout: {str(e)}"
        }


def cancel_session(state: SessionWorkoutState) -> SessionWorkoutState:
    """
    Cancel the session without saving.
    """
    return {
        **state,
        "saved": False,
        "response": "Session cancelled"
    }


# ============================================================================
# Planning Node Functions (Phase 1)
# ============================================================================

def initialize_planning(state: SessionWithPlanState) -> SessionWithPlanState:
    """
    Initialize pre-workout planning session.

    - Calls suggest_next_workout() to get AI recommendation
    - Generates adaptive template for suggested type
    - Sets up initial planning state
    """
    try:
        # Get AI suggestion for workout type
        suggestion = suggest_next_workout.invoke({})
        suggested_type = suggestion.get('suggested_type', 'Push')
        reason = suggestion.get('reason', 'Based on your weekly split')

        # Generate adaptive template for this type
        template_result = get_workout_template.invoke({
            "workout_type": suggested_type,
            "adaptive": True
        })

        template = template_result if template_result.get('found') else {
            "id": f"basic_{suggested_type.lower()}",
            "name": f"{suggested_type} Workout",
            "type": suggested_type,
            "exercises": [],
            "mode": "static"
        }

        # Initialize planning state
        now = datetime.now().isoformat()

        return {
            **state,
            "started_at": now,
            "last_activity_at": now,
            "suggested_type": suggested_type,
            "suggestion_reason": reason,
            "planned_template": template,
            "actual_workout_type": suggested_type,  # Default to suggested
            "plan_adjustments": [],
            "equipment_available": None,
            "equipment_unavailable": None,
            "current_exercise_index": 0,
            "response": f"AI suggests {suggested_type} workout today"
        }

    except Exception as e:
        # Fallback if recommendation fails
        return {
            **state,
            "started_at": datetime.now().isoformat(),
            "last_activity_at": datetime.now().isoformat(),
            "suggested_type": "Push",
            "suggestion_reason": "Default suggestion",
            "planned_template": {"exercises": [], "mode": "static"},
            "actual_workout_type": "Push",
            "plan_adjustments": [],
            "equipment_available": None,
            "equipment_unavailable": None,
            "current_exercise_index": 0,
            "response": f"Error getting suggestion: {str(e)}"
        }


def process_planning_chat(state: SessionWithPlanState, user_message: str) -> SessionWithPlanState:
    """
    Process user's planning chat message and modify template.

    Args:
        state: Current planning state
        user_message: User's modification request

    Returns:
        Updated state with modified template
    """
    from src.agents.planning_chain import get_planning_chain

    try:
        # Get current template and equipment constraints
        current_template = state.get('planned_template', {})
        equipment_unavailable = state.get('equipment_unavailable', [])
        equipment_available = state.get('equipment_available', [])

        # Call planning chain to modify template
        chain = get_planning_chain()
        result = chain.modify_template(
            user_message=user_message,
            current_template=current_template,
            equipment_available=equipment_available,
            equipment_unavailable=equipment_unavailable
        )

        # Create adjustment record
        adjustment = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "ai_response": result.get('explanation', 'Template updated'),
            "template_change": True
        }

        # Update plan adjustments history
        adjustments = state.get('plan_adjustments', []).copy()
        adjustments.append(adjustment)

        # Update state with modified template
        return {
            **state,
            "planned_template": result.get('modified_template', current_template),
            "plan_adjustments": adjustments,
            "equipment_unavailable": result.get('equipment_unavailable', equipment_unavailable),
            "equipment_available": result.get('equipment_required', equipment_available),
            "last_activity_at": datetime.now().isoformat(),
            "response": result.get('explanation', 'Template updated')
        }

    except Exception as e:
        # On error, return state unchanged with error message
        return {
            **state,
            "response": f"Could not modify template: {str(e)}"
        }


# ============================================================================
# Routing Functions
# ============================================================================

def route_user_action(state: SessionWorkoutState) -> str:
    """
    Route based on user's chosen action.

    Returns:
        "add_another" | "finish" | "cancel" | "preview"
    """
    action = state.get("user_action")

    if action == "finish":
        return "finish"
    elif action == "cancel":
        return "cancel"
    elif action == "add_another":
        return "add_another"
    else:
        # No action yet - stop here for user preview
        return "preview"


# ============================================================================
# Graph Construction
# ============================================================================

def build_session_graph():
    """
    Build the session workout logging graph.

    Flow:
        START
          ↓
        parse_exercise (parse single exercise)
          ↓
        [HUMAN INPUT: user chooses action]
          ↓
        route_user_action
          ├→ add_another: accumulate → END
          ├→ finish: save_session_workout → END
          └→ cancel: cancel_session → END
    """
    # Create graph
    workflow = StateGraph(SessionWorkoutState)

    # Add nodes
    workflow.add_node("parse_exercise", parse_exercise)
    workflow.add_node("accumulate_exercise", accumulate_exercise)
    workflow.add_node("save_session_workout", save_session_workout)
    workflow.add_node("cancel_session", cancel_session)

    # Set entry point
    workflow.set_entry_point("parse_exercise")

    # Add conditional routing after parse
    # Note: For Phase 1, we handle routing in the UI layer
    # The graph just provides the parsing and saving logic
    workflow.add_conditional_edges(
        "parse_exercise",
        route_user_action,
        {
            "preview": END,  # Stop here for user to preview
            "add_another": "accumulate_exercise",
            "finish": "save_session_workout",
            "cancel": "cancel_session"
        }
    )

    # All paths end
    workflow.add_edge("accumulate_exercise", END)
    workflow.add_edge("save_session_workout", END)
    workflow.add_edge("cancel_session", END)

    return workflow.compile()


# ============================================================================
# Convenience Functions for UI
# ============================================================================

def start_session(intended_type: str) -> dict:
    """
    Start a new workout session.

    Args:
        intended_type: Workout type (Push, Pull, Legs, etc.)

    Returns:
        Initial session state dict
    """
    return {
        "session_id": str(uuid.uuid4()),
        "intended_type": intended_type,
        "accumulated_exercises": [],
        "current_exercise_input": None,
        "current_parsed_exercise": None,
        "user_action": None,
        "saved": False,
        "workout_id": None,
        "response": None
    }


def add_exercise_to_session(session_state: dict, exercise_input: str) -> dict:
    """
    Parse and add an exercise to the session.

    Args:
        session_state: Current session state
        exercise_input: Raw exercise input (from voice or text)

    Returns:
        Updated session state with parsed exercise
    """
    # Update state with new input
    session_state["current_exercise_input"] = exercise_input

    # Build graph and invoke
    graph = build_session_graph()

    # Run parsing
    result = graph.invoke(session_state)

    return result


def finish_session(session_state: dict) -> dict:
    """
    Finish the session and save the workout.

    Args:
        session_state: Current session state

    Returns:
        Final session state with saved workout
    """
    # Set user action to finish
    session_state["user_action"] = "finish"

    # Build graph and invoke
    graph = build_session_graph()

    result = graph.invoke(session_state)

    return result


# ============================================================================
# Phase 1: Planning Convenience Functions
# ============================================================================

def initialize_planning_session() -> dict:
    """
    Initialize a new planning session with AI recommendation.

    Returns:
        Initial planning state dict with suggested workout and template
    """
    # Create initial state with required fields
    initial_state = {
        "session_id": str(uuid.uuid4()),
        "started_at": "",  # Will be set by initialize_planning
        "last_activity_at": "",
        "suggested_type": "",
        "suggestion_reason": "",
        "planned_template": {},
        "plan_adjustments": [],
        "equipment_available": None,
        "equipment_unavailable": None,
        "actual_workout_type": "",
        "accumulated_exercises": [],
        "current_exercise_index": 0,
        "current_exercise_input": None,
        "current_parsed_exercise": None,
        "user_action": None,
        "saved": False,
        "workout_id": None,
        "response": None
    }

    # Call initialize_planning to populate with AI recommendation
    result = initialize_planning(initial_state)

    return result


def modify_plan_via_chat(session_state: dict, user_message: str) -> dict:
    """
    Modify the workout plan via chat during planning phase.

    Args:
        session_state: Current planning session state
        user_message: User's modification request

    Returns:
        Updated session state with modified template
    """
    result = process_planning_chat(session_state, user_message)
    return result
