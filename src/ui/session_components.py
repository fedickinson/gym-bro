"""
Session-Based Workout Logging UI Components.

Reusable UI components for session mode workout logging.
"""

import streamlit as st
from datetime import datetime


# DEPRECATED: render_session_start() removed 2025-12-24
# All sessions now go through initialize_planning_session() to ensure proper
# workout type tracking and weekly split integration.
# See: src/agents/session_graph.py::initialize_planning_session()


def render_exercise_preview(exercise: dict):
    """
    Render a single exercise preview.

    Args:
        exercise: Exercise dict with name and sets
    """
    st.success(f"✅ Added: **{exercise.get('name', 'Unknown')}**")

    # Show sets
    sets = exercise.get('sets', [])
    if sets:
        st.write(f"**{len(sets)} sets:**")
        for i, s in enumerate(sets, 1):
            reps = s.get('reps', '?')
            weight = s.get('weight_lbs')

            if weight:
                st.write(f"  Set {i}: {reps} reps @ {weight} lbs")
            else:
                st.write(f"  Set {i}: {reps} reps (bodyweight)")
    else:
        st.caption("No sets recorded")


def render_workout_review(session: dict):
    """
    Render the full workout review before saving.

    Args:
        session: Workout session dict with accumulated_exercises (SessionWithPlanState)
    """
    st.title("📋 Review Your Workout")

    accumulated_exercises = session.get('accumulated_exercises', [])
    intended_type = session.get('intended_type') or session.get('actual_workout_type', 'Unknown')

    if not accumulated_exercises:
        st.warning("No exercises recorded yet")
        return

    # Phase 6: Show plan vs actual comparison if available
    suggested_type = session.get('suggested_type')
    actual_type = session.get('actual_workout_type')

    # Show workout summary
    st.subheader(f"{actual_type or intended_type} Workout")

    # Plan vs Actual indicator
    if suggested_type and actual_type and suggested_type != actual_type:
        st.warning(f"⚠️ **Deviated from plan:** Originally suggested {suggested_type}, completed {actual_type}")
    elif suggested_type:
        st.success(f"✅ **Followed plan:** {suggested_type} workout as suggested")

    st.caption(f"Started: {session.get('started_at', 'Unknown')}")
    st.caption(f"{len(accumulated_exercises)} exercises completed")

    # Show plan adjustments if any
    plan_adjustments = session.get('plan_adjustments', [])
    if plan_adjustments:
        with st.expander(f"📝 Plan Modifications ({len(plan_adjustments)})", expanded=False):
            for adj in plan_adjustments:
                if adj.get('adaptation'):
                    st.info(f"🔄 **Adapted:** {adj.get('ai_response', 'Plan adapted mid-workout')}")
                else:
                    st.caption(f"💬 {adj.get('user_message', 'Modified')}: {adj.get('ai_response', '')[:80]}...")

    # Show equipment constraints if any
    equipment_unavailable = session.get('equipment_unavailable')
    if equipment_unavailable:
        st.caption(f"⚠️ Equipment unavailable: {', '.join(equipment_unavailable)}")

    # List all exercises
    st.divider()
    for i, ex in enumerate(accumulated_exercises, 1):
        with st.expander(f"**{i}. {ex.get('name')}**", expanded=False):
            sets = ex.get('sets', [])
            if sets:
                for j, s in enumerate(sets, 1):
                    reps = s.get('reps', '?')
                    weight = s.get('weight_lbs')

                    if weight:
                        st.write(f"Set {j}: **{reps} reps** @ **{weight} lbs**")
                    else:
                        st.write(f"Set {j}: **{reps} reps** (bodyweight)")
            else:
                st.caption("No sets recorded")

    # Show total sets
    total_sets = sum(len(ex.get('sets', [])) for ex in accumulated_exercises)
    st.metric("Total Sets", total_sets)


def render_session_progress(session: dict):
    """
    Render session progress indicator (exercises added so far).

    Args:
        session: Workout session dict
    """
    num_accumulated = len(session.get('accumulated_exercises', []))
    intended_type = session.get('intended_type', 'Unknown')
    planned_template = session.get('planned_template', {})
    planned_count = len(planned_template.get('exercises', []))

    # Show progress relative to plan (if plan exists)
    if planned_count > 0:
        if num_accumulated < planned_count:
            # Still working through plan
            st.caption(f"**{intended_type} Session:** {num_accumulated}/{planned_count} planned exercises completed")
        elif num_accumulated == planned_count:
            # Exactly completed plan
            st.success(f"✅ **Plan Complete!** {planned_count}/{planned_count} exercises done")
        else:
            # Exceeded plan (bonus exercises)
            bonus = num_accumulated - planned_count
            st.success(f"✅ **Plan Complete!** {planned_count} exercises + {bonus} bonus")
    else:
        # No plan - just show count (legacy behavior)
        st.caption(f"**{intended_type} Session:** {num_accumulated} exercise{'s' if num_accumulated != 1 else ''} logged")


def render_coaching_panel(next_suggestion: str = None, balance: dict = None, progress: str = None):
    """
    Render AI coaching insights panel.

    Args:
        next_suggestion: Suggested next exercise
        balance: Muscle balance check result
        progress: Progress insight

    Note: This is a placeholder for Phase 2. For Phase 1, this does nothing.
    """
    # Phase 2: Will render AI coaching here
    # For Phase 1 (minimal session tracking), we don't show coaching yet
    pass
