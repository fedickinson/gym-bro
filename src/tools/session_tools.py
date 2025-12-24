"""
Session Tools - Tools for initiating and managing workout sessions.

These tools allow the chat agent to create workout planning sessions
and bridge between conversational AI and the workout logging UI.
"""

import streamlit as st
from langchain_core.tools import tool
from src.agents.session_graph import initialize_planning_session, modify_plan_via_chat


@tool
def start_workout_session(workout_type: str = None, equipment_unavailable: str = None) -> dict:
    """
    Initialize a new workout planning session.

    This creates a complete workout plan with AI recommendations and prepares
    the user to start logging their workout.

    Args:
        workout_type: Optional specific workout type to do
                     (Push/Pull/Legs/Upper/Lower). If None, AI will suggest
                     based on weekly split rotation.
        equipment_unavailable: Optional comma-separated list of equipment
                              that's not available (e.g., "Barbell,Leg Press")

    Returns:
        Dict with session creation result:
        - success: True/False
        - message: Description of what happened
        - session_id: ID of created session (if successful)
        - suggested_type: What workout type was planned
        - exercise_count: Number of exercises in the plan
        - error: Error message (if failed)

    Examples:
        start_workout_session()
        → Creates session with AI-suggested workout type

        start_workout_session(workout_type="Push")
        → Creates Push workout session

        start_workout_session(equipment_unavailable="Barbell,Leg Press")
        → Creates session avoiding barbell and leg press exercises
    """
    # ========================================================================
    # Risk Mitigation #1: Session Conflict Detection
    # ========================================================================

    # Check if there's already an active session
    if st.session_state.get('workout_session') is not None:
        existing_session = st.session_state.workout_session
        existing_type = existing_session.get('suggested_type', 'Unknown')
        exercise_count = len(existing_session.get('accumulated_exercises', []))

        return {
            "success": False,
            "error": "active_session_exists",
            "message": (
                f"You already have an active {existing_type} workout session "
                f"with {exercise_count} exercises logged. Please finish or "
                f"cancel your current workout before starting a new one."
            ),
            "existing_type": existing_type,
            "existing_exercise_count": exercise_count
        }

    # ========================================================================
    # Create New Session
    # ========================================================================

    try:
        # Initialize the planning session (gets AI recommendation and template)
        session_state = initialize_planning_session()

        # Apply user-specified workout type if provided
        if workout_type:
            # Validate workout type
            valid_types = ["Push", "Pull", "Legs", "Upper", "Lower"]
            if workout_type.title() not in valid_types:
                return {
                    "success": False,
                    "error": "invalid_workout_type",
                    "message": (
                        f"'{workout_type}' is not a valid workout type. "
                        f"Choose from: {', '.join(valid_types)}"
                    )
                }

            # User specified a type different from AI suggestion
            if workout_type.title() != session_state.get('suggested_type'):
                # Modify the plan via chat to change workout type
                modification_request = f"I want to do {workout_type.title()} instead"
                session_state = modify_plan_via_chat(session_state, modification_request)

        # Apply equipment constraints if provided
        if equipment_unavailable:
            # Parse comma-separated equipment list
            equipment_list = [e.strip() for e in equipment_unavailable.split(',')]
            session_state['equipment_unavailable'] = equipment_list

            # Modify plan to avoid this equipment
            equipment_text = ", ".join(equipment_list)
            modification_request = f"I don't have access to: {equipment_text}"
            session_state = modify_plan_via_chat(session_state, modification_request)

        # ====================================================================
        # Store in Streamlit Session State
        # ====================================================================

        st.session_state.workout_session = session_state
        st.session_state.chat_initiated_workout = True

        # ====================================================================
        # Build Success Response
        # ====================================================================

        suggested_type = session_state.get('suggested_type', 'Unknown')
        exercise_count = len(session_state.get('planned_template', {}).get('exercises', []))
        suggestion_reason = session_state.get('suggestion_reason', '')

        return {
            "success": True,
            "message": (
                f"Great! I've created a {suggested_type} workout for you with "
                f"{exercise_count} exercises. {suggestion_reason}"
            ),
            "session_id": session_state.get('session_id'),
            "suggested_type": suggested_type,
            "exercise_count": exercise_count,
            "equipment_unavailable": equipment_list if equipment_unavailable else None
        }

    except Exception as e:
        # Handle any errors during session creation
        import traceback
        error_trace = traceback.format_exc()

        return {
            "success": False,
            "error": "session_creation_failed",
            "message": f"Failed to create workout session: {str(e)}",
            "details": error_trace
        }


# ============================================================================
# Export all session tools
# ============================================================================

SESSION_TOOLS = [
    start_workout_session
]


# ============================================================================
# Quick Test
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of session tools.

    NOTE: This won't work outside of Streamlit context since it requires
    st.session_state. This is just for reference.
    """
    print("⚠️  Session tools require Streamlit context to run")
    print("Test these tools within the Streamlit app using the chat agent")
