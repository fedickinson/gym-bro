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
# Helper Functions
# ============================================================================

def _infer_workout_type_from_exercises(exercises: list[dict]) -> str | None:
    """
    Infer workout type from exercise names as a last resort.

    This is used when session state is missing workout type information.
    Uses simple keyword matching to classify exercises.

    Args:
        exercises: List of exercise dicts with 'name' field

    Returns:
        "Push", "Pull", "Legs", or None if cannot infer
    """
    if not exercises:
        return None

    # Exercise classification keywords
    push_keywords = {"bench", "press", "chest", "tricep", "shoulder", "dip", "fly", "pushup"}
    pull_keywords = {"pull", "row", "lat", "back", "bicep", "curl", "chin", "shrug"}
    leg_keywords = {"squat", "leg", "lunge", "calf", "quad", "hamstring", "glute", "deadlift"}

    # Count votes
    push_score = 0
    pull_score = 0
    leg_score = 0

    for ex in exercises:
        name_lower = ex.get("name", "").lower()

        # Check for leg exercises first (most specific)
        if any(keyword in name_lower for keyword in leg_keywords):
            leg_score += 1
        elif any(keyword in name_lower for keyword in push_keywords):
            push_score += 1
        elif any(keyword in name_lower for keyword in pull_keywords):
            pull_score += 1

    # Return majority vote
    max_score = max(push_score, pull_score, leg_score)

    if max_score == 0:
        return None  # Cannot infer
    elif push_score == max_score:
        return "Push"
    elif pull_score == max_score:
        return "Pull"
    else:
        return "Legs"


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

    # Current exercise being added (DEPRECATED - use set-by-set fields below)
    current_exercise_input: str | None
    current_parsed_exercise: dict | None

    # AI Suggestions (Phase 2)
    next_suggestion: dict | None
    # {
    #   source: "plan" | "adaptive",
    #   exercise_name, target_sets, target_reps,
    #   suggested_weight_lbs, reasoning, plan_index
    # }

    # Set-by-set tracking (NEW)
    in_progress_exercise: dict | None  # Exercise being built set-by-set
    # {
    #   "name": "Bench Press",
    #   "sets": [{"reps": 10, "weight_lbs": 135}],  # Sets completed so far
    #   "target_sets": 4,
    #   "target_reps": 10
    # }
    current_exercise_name: str | None  # Name of exercise in progress
    current_exercise_sets_completed: list[dict]  # Sets recorded so far
    current_set_number: int  # Which set we're on (1, 2, 3, etc.)
    target_sets: int  # Total planned sets for this exercise
    current_set_suggestion: dict | None  # Suggestion for THIS specific set
    # {
    #   "set_number": 1,
    #   "target_reps": 10,
    #   "suggested_weight_lbs": 135,
    #   "rest_seconds": 90
    # }

    # Deviation Detection (Phase 3)
    current_deviation: dict | None
    # {
    #   is_deviation: bool, severity: "none"|"minor_variation"|"major_deviation",
    #   similarity_score: float, planned_name: str, actual_name: str,
    #   impact_description: str, changes_workout_type: bool, new_workout_type: str
    # }

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

    # Increment exercise index (for SessionWithPlanState)
    new_index = state.get("current_exercise_index", 0) + 1

    # Update last activity time
    # Note: We'll persist to disk here in the actual implementation

    return {
        **state,
        "accumulated_exercises": accumulated,
        "current_exercise_index": new_index,
        "current_exercise_input": None,  # Clear for next exercise
        "current_parsed_exercise": None,
        "response": f"Added exercise: {current_exercise.get('name')}"
    }


def save_session_workout(state: SessionWorkoutState) -> SessionWorkoutState:
    """
    Save the complete workout session to workout_logs.json.

    Handles both SessionWorkoutState and SessionWithPlanState.
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
        # Determine workout type (CRITICAL for weekly split tracking)
        workout_type = state.get("actual_workout_type") or intended_type

        # VALIDATION: Ensure type is not null/empty
        # This prevents weekly split tracking bugs
        if not workout_type or workout_type == "":
            # Fallback: Try to infer from suggested_type
            workout_type = state.get("suggested_type")

            if not workout_type or workout_type == "":
                # Last resort: Classify by exercises
                workout_type = _infer_workout_type_from_exercises(exercises)

                if not workout_type:
                    # Cannot save without a type - this is a critical error
                    return {
                        **state,
                        "saved": False,
                        "response": (
                            "❌ Cannot save workout: Unable to determine workout type. "
                            "This is a system error - please report it."
                        )
                    }

        # Create workout log
        workout_log = {
            "date": date.today().isoformat(),
            "type": workout_type,  # Validated - never null
            "exercises": exercises,
            "notes": f"Session logged incrementally (Session ID: {session_id})",
            "completed": True
        }

        # Phase 6: Add session metadata if SessionWithPlanState
        if "suggested_type" in state:  # SessionWithPlanState
            workout_log["session_id"] = session_id
            workout_log["suggested_type"] = state.get("suggested_type")

            # Save planned template info
            planned_template = state.get("planned_template", {})
            if planned_template.get("id"):
                workout_log["planned_template_id"] = planned_template.get("id")

            # Save plan adjustments (chat modifications)
            if state.get("plan_adjustments"):
                workout_log["plan_adjustments"] = state.get("plan_adjustments")

            # Collect deviations detected during session
            # Note: We'd need to track these throughout the session
            # For now, just note if there were any major deviations

            # Save equipment constraints
            if state.get("equipment_unavailable"):
                workout_log["equipment_unavailable"] = state.get("equipment_unavailable")

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

        # DEBUG: Log template resolution
        print(f"DEBUG: Template for {suggested_type}: found={template_result.get('found')}, mode={template_result.get('mode')}, exercises={len(template_result.get('exercises', []))}")

        template = template_result if template_result.get('found') else {
            "id": f"basic_{suggested_type.lower()}",
            "name": f"{suggested_type} Workout",
            "type": suggested_type,
            "exercises": [],
            "mode": "static"
        }

        # WARN if fallback triggered
        if not template_result.get('found'):
            print(f"⚠️ WARNING: No template found for {suggested_type}, using empty fallback")

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
# Suggestion Node Functions (Phase 2)
# ============================================================================

def generate_next_suggestion(state: SessionWithPlanState) -> SessionWithPlanState:
    """
    Generate AI-powered suggestion for the next exercise.

    Called after accumulating an exercise to provide guidance for what's next.

    Args:
        state: Current SessionWithPlanState

    Returns:
        Updated state with next_suggestion populated
    """
    from src.agents.suggestion_engine import suggest_next_exercise

    try:
        # Generate suggestion based on plan and progress
        suggestion = suggest_next_exercise(state, source="auto")

        return {
            **state,
            "next_suggestion": suggestion,
            "last_activity_at": datetime.now().isoformat()
        }

    except Exception as e:
        # On error, return state with no suggestion
        return {
            **state,
            "next_suggestion": None,
            "response": f"Could not generate suggestion: {str(e)}"
        }


def generate_next_set_suggestion(state: SessionWithPlanState) -> dict | None:
    """
    Generate suggestion for the next SET (not exercise).

    This is used for set-by-set recording flow where each set is recorded individually.

    Logic:
    - If in_progress_exercise is None: First set of a new exercise
      → Pull from next_suggestion or planned_template
    - If in_progress_exercise exists: Next set of same exercise
      → Increment set number, use same exercise details

    Args:
        state: Current SessionWithPlanState

    Returns:
        Set suggestion dict or None if no suggestion available:
        {
            "set_number": 1,
            "target_reps": 10,
            "suggested_weight_lbs": 135.0,
            "rest_seconds": 90,
            "exercise_name": "Bench Press"
        }
    """
    try:
        in_progress = state.get('in_progress_exercise')

        if in_progress is not None:
            # Next set of current exercise
            current_set_num = state.get('current_set_number', 0)
            target_sets = state.get('target_sets', 0)

            # Check if we've completed all planned sets
            if current_set_num >= target_sets:
                return None  # Exercise complete

            # Get details from in_progress_exercise
            exercise_name = in_progress.get('name', 'Unknown')
            target_reps = in_progress.get('target_reps', 10)

            # Get rest seconds from in_progress or default
            rest_seconds = in_progress.get('rest_seconds', 90)

            # Calculate suggested weight based on last set's performance
            sets_completed = in_progress.get('sets', [])
            if sets_completed:
                # Use last set's weight as suggestion
                last_set = sets_completed[-1]
                suggested_weight = last_set.get('weight_lbs')
            else:
                # Use initial suggestion if available
                suggested_weight = in_progress.get('suggested_weight_lbs')

            return {
                "set_number": current_set_num + 1,
                "target_reps": target_reps,
                "suggested_weight_lbs": suggested_weight,
                "rest_seconds": rest_seconds,
                "exercise_name": exercise_name
            }

        else:
            # First set of a new exercise
            # Try to get from next_suggestion first (AI-generated)
            next_suggestion = state.get('next_suggestion')

            if next_suggestion and next_suggestion.get('exercise_name'):
                # Use AI suggestion
                return {
                    "set_number": 1,
                    "target_reps": next_suggestion.get('target_reps', 10),
                    "suggested_weight_lbs": next_suggestion.get('suggested_weight_lbs'),
                    "rest_seconds": next_suggestion.get('rest_seconds', 90),
                    "exercise_name": next_suggestion.get('exercise_name')
                }

            # Fallback: Get from planned template
            planned_template = state.get('planned_template', {})
            plan_exercises = planned_template.get('exercises', [])
            current_index = state.get('current_exercise_index', 0)

            if current_index < len(plan_exercises):
                planned_ex = plan_exercises[current_index]

                return {
                    "set_number": 1,
                    "target_reps": planned_ex.get('target_reps', 10),
                    "suggested_weight_lbs": planned_ex.get('suggested_weight_lbs'),
                    "rest_seconds": planned_ex.get('rest_seconds', 90),
                    "exercise_name": planned_ex.get('name', 'Unknown')
                }

            # No suggestion available
            return None

    except Exception as e:
        print(f"Error generating set suggestion: {str(e)}")
        return None


# ============================================================================
# Deviation Detection Node Functions (Phase 3)
# ============================================================================

def check_for_deviation(state: SessionWithPlanState) -> SessionWithPlanState:
    """
    Check if current exercise deviates from the plan.

    Compares current_parsed_exercise against planned_template[current_exercise_index].

    Args:
        state: Current SessionWithPlanState

    Returns:
        Updated state with current_deviation populated
    """
    from src.agents.deviation_detector import detect_deviation

    try:
        current_exercise = state.get('current_parsed_exercise')

        if not current_exercise:
            # No exercise to check
            return {
                **state,
                "current_deviation": None
            }

        # Get planned exercise at current index
        planned_template = state.get('planned_template', {})
        current_index = state.get('current_exercise_index', 0)
        plan_exercises = planned_template.get('exercises', [])

        # Get planned exercise (if in bounds)
        planned_exercise = None
        if current_index < len(plan_exercises):
            planned_exercise = plan_exercises[current_index]

        # Detect deviation
        current_type = state.get('actual_workout_type', state.get('suggested_type', 'Unknown'))
        deviation = detect_deviation(current_exercise, planned_exercise, current_type)

        return {
            **state,
            "current_deviation": deviation,
            "last_activity_at": datetime.now().isoformat()
        }

    except Exception as e:
        # On error, return state with no deviation data
        return {
            **state,
            "current_deviation": None,
            "response": f"Could not check deviation: {str(e)}"
        }


# ============================================================================
# Plan Adaptation Node Functions (Phase 4)
# ============================================================================

def regenerate_plan_after_deviation(state: SessionWithPlanState) -> SessionWithPlanState:
    """
    Regenerate workout plan after user deviates and chooses to adapt.

    Updates planned_template with exercises complementary to what user actually did.

    Args:
        state: Current SessionWithPlanState

    Returns:
        Updated state with adapted template
    """
    from src.agents.plan_adapter import adapt_plan_for_deviation

    try:
        deviation = state.get('current_deviation')

        if not deviation or not deviation.get('changes_workout_type'):
            # No need to adapt if no deviation or type didn't change
            return state

        # Get adaptation
        accumulated = state.get('accumulated_exercises', [])
        new_type = deviation.get('new_workout_type', state.get('suggested_type'))
        equipment_unavailable = state.get('equipment_unavailable')

        adaptation = adapt_plan_for_deviation(
            accumulated,
            new_type,
            equipment_unavailable
        )

        # Update state with adapted plan
        return {
            **state,
            "planned_template": adaptation.get('adapted_template'),
            "actual_workout_type": new_type,
            "plan_adjustments": state.get('plan_adjustments', []) + [{
                "timestamp": adaptation.get('timestamp'),
                "user_message": "User deviated - adapted plan",
                "ai_response": adaptation.get('adaptation_reason'),
                "template_change": True,
                "adaptation": True
            }],
            "last_activity_at": datetime.now().isoformat(),
            "response": adaptation.get('adaptation_reason')
        }

    except Exception as e:
        return {
            **state,
            "response": f"Could not adapt plan: {str(e)}"
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


def add_exercise_to_session(session_state: dict, exercise_input: str, context: dict = None) -> dict:
    """
    Parse and add an exercise to the session.

    Args:
        session_state: Current session state (SessionWithPlanState)
        exercise_input: Raw exercise input (from voice or text)
        context: Optional parsing context with keys:
            - suggested_exercise: Exercise name to use if not in input

    Returns:
        Updated session state with parsed exercise
    """
    # Pre-process input if exercise name is suggested
    if context and context.get('suggested_exercise'):
        suggested_exercise = context['suggested_exercise']
        # Check if input already mentions the exercise
        if suggested_exercise.lower() not in exercise_input.lower():
            # Prepend exercise name to input
            exercise_input = f"{suggested_exercise}, {exercise_input}"

    # Update state with processed input
    session_state["current_exercise_input"] = exercise_input

    # Build graph and invoke
    # Note: Graph uses SessionWorkoutState, so preserve SessionWithPlanState fields
    graph = build_session_graph()

    # Run parsing
    result = graph.invoke(session_state)

    # CRITICAL: Preserve SessionWithPlanState fields that graph doesn't know about
    # The graph only returns SessionWorkoutState fields
    result = {
        **session_state,  # Preserve all original fields
        **result  # Override with parsed results
    }

    # Phase 3: Check for deviation after parsing
    if result.get('current_parsed_exercise'):
        result = check_for_deviation(result)

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

def generate_workout_summary(session_state: dict) -> str:
    """
    Generate an AI summary of the planned workout with trainer-level insights.

    Args:
        session_state: Current planning session state

    Returns:
        Natural language summary with exercise analysis and progression context
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage, HumanMessage

    try:
        # Extract workout details
        workout_type = session_state.get('suggested_type', 'Unknown')
        suggestion_reason = session_state.get('suggestion_reason', '')
        template = session_state.get('planned_template', {})
        exercises = template.get('exercises', [])
        adaptations = template.get('adaptations', [])
        coaching_notes = template.get('coaching_notes', [])

        # Get historical context
        from src.data import get_logs_by_date_range
        from datetime import datetime, timedelta, date

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        all_recent_logs = get_logs_by_date_range(start_date, end_date)
        past_workouts = [log for log in all_recent_logs if log.get('type') == workout_type]

        # Build detailed exercise context
        exercise_details = []
        for ex in exercises[:4]:  # First 4 exercises for detail
            ex_detail = f"{ex.get('name')} - {ex.get('target_sets')}×{ex.get('target_reps')}"

            weight = ex.get('suggested_weight_lbs')
            if weight:
                ex_detail += f" @ {weight:.0f} lbs"

            # Include reasoning about weights/progression
            reasoning = ex.get('reasoning', '')
            if reasoning:
                # Truncate if too long, but keep key progression info
                if len(reasoning) > 80:
                    ex_detail += f" (Reasoning: {reasoning[:80]}...)"
                else:
                    ex_detail += f" (Reasoning: {reasoning})"

            exercise_details.append(ex_detail)

        # Calculate days since last workout
        days_since_last = None
        if past_workouts and len(past_workouts) > 0:
            last_workout = past_workouts[0]
            last_date_str = last_workout.get('date')
            if last_date_str:
                try:
                    last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
                    days_since_last = (end_date - last_date).days
                except:
                    pass

        # Create prompt
        llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.7)

        system_msg = SystemMessage(content="""You are an expert personal trainer providing workout guidance.

Format requirements:
- Start with 1 bold sentence about the primary focus
- Use bullet points (•) for each exercise with brief explanation (1 sentence per exercise)
- End with 1-2 sentences on recovery/timing
- Be concise but insightful - cut unnecessary words
- Use **bold** for exercise names only

Structure:
**[Focus statement]**

• **Exercise 1** - [Why it's positioned here, what it does]
• **Exercise 2** - [How it builds on exercise 1]
• **Exercise 3** - [Its role in the workout]

[Recovery note in 1-2 sentences]

Keep it tight and actionable.""")

        workout_context = f"""
Workout Type: {workout_type}
Why Suggested: {suggestion_reason}

Exercises with Details:
{chr(10).join(f'• {detail}' for detail in exercise_details)}
{'• ...and ' + str(len(exercises) - 4) + ' more' if len(exercises) > 4 else ''}

Template Adaptations:
{chr(10).join(f'• {adapt}' for adapt in adaptations) if adaptations else '• Using base template'}

{f'Coaching Notes: {chr(10).join(coaching_notes)}' if coaching_notes else ''}

Historical Context:
- Total {workout_type} workouts in last 30 days: {len(past_workouts)}
{f'- Last {workout_type} workout: {days_since_last} days ago' if days_since_last is not None else ''}
"""

        human_msg = HumanMessage(content=f"""Create a concise workout summary:

{workout_context}

IMPORTANT: Reference specific weights when provided. Mention if they represent progression, maintenance, or deload.

Format exactly as:
**[One bold sentence on primary goal]**

• **Exercise 1** - [Include weight if provided. Explain why this weight/position makes sense]
• **Exercise 2** - [Include weight if provided. How it complements exercise 1]
• **Exercise 3** - [Include weight if provided. Its unique role]
(continue for all exercises)

[1-2 sentences on recovery timing or progression context]

Examples:
- "**Squat** at 185 lbs - Heavy opener while CNS is fresh, progressing from last week's 180"
- "**Leg Press** at 225 lbs - Maintains intensity with reduced stabilizer demands"
- "**Leg Curl** - Target hamstrings for balance (choose weight based on feel)"

Be direct. Make weights part of the analysis, not just numbers.""")

        response = llm.invoke([system_msg, human_msg])
        return response.content

    except Exception as e:
        # Log error for debugging
        print(f"Error generating workout summary: {str(e)}")
        import traceback
        traceback.print_exc()

        # Fallback summary if AI generation fails
        workout_type = session_state.get('suggested_type', 'workout')
        num_exercises = len(session_state.get('planned_template', {}).get('exercises', []))
        return f"Ready for your {workout_type} workout with {num_exercises} exercises. Let's get stronger today!"


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
        "next_suggestion": None,  # Phase 2: AI suggestions
        "current_deviation": None,  # Phase 3: Deviation detection
        # Set-by-set tracking fields (NEW)
        "in_progress_exercise": None,
        "current_exercise_name": None,
        "current_exercise_sets_completed": [],
        "current_set_number": 0,  # 0 means no set in progress
        "target_sets": 0,
        "current_set_suggestion": None,
        "user_action": None,
        "saved": False,
        "workout_id": None,
        "response": None,
        "workout_summary": None  # AI-generated workout summary
    }

    # Call initialize_planning to populate with AI recommendation
    result = initialize_planning(initial_state)

    # Generate AI summary of the workout
    result['workout_summary'] = generate_workout_summary(result)

    # Generate initial suggestion (first exercise from plan)
    result = generate_next_suggestion(result)

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

    # Regenerate AI summary with updated plan
    result['workout_summary'] = generate_workout_summary(result)

    # Regenerate suggestion with updated plan
    result = generate_next_suggestion(result)

    return result


def refresh_next_suggestion(session_state: dict) -> dict:
    """
    Refresh the next exercise suggestion.

    Call this after accumulating an exercise or when user needs a new suggestion.

    Args:
        session_state: Current SessionWithPlanState

    Returns:
        Updated state with refreshed next_suggestion
    """
    return generate_next_suggestion(session_state)


def adapt_plan(session_state: dict) -> dict:
    """
    Adapt workout plan after deviation.

    Call this when user chooses "Adapt Rest of Plan" after a major deviation.

    Args:
        session_state: Current SessionWithPlanState with deviation detected

    Returns:
        Updated state with adapted template and refreshed suggestion
    """
    # Regenerate plan
    result = regenerate_plan_after_deviation(session_state)

    # Refresh suggestion with new plan
    result = refresh_next_suggestion(result)

    return result
