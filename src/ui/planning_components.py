"""
Planning UI Components - Pre-workout planning interface.

Components for AI-guided workout planning, including:
- Template preview with exercise details
- Chat interface for modifications
- Adjustment history display
"""

import streamlit as st
from datetime import datetime


def render_template_preview(template: dict):
    """
    Render a workout template preview with exercises and details.

    Args:
        template: Template dict with exercises, coaching notes, etc.
    """
    if not template or not template.get('exercises'):
        st.warning("No template loaded")
        return

    # Display exercises
    st.subheader(f"{template.get('type', 'Unknown')} Workout")
    st.caption(f"{len(template['exercises'])} exercises")

    # Show coaching notes if any (simplified)
    coaching_notes = template.get('coaching_notes', [])
    if coaching_notes:
        for note in coaching_notes:
            st.info(f"💡 {note}")

    for i, ex in enumerate(template['exercises'], 1):
        # Expand first exercise by default to show weights clearly
        expanded = (i == 1)

        with st.expander(f"**{i}. {ex.get('name')}**", expanded=expanded):
            col1, col2 = st.columns(2)

            with col1:
                target_sets = ex.get('target_sets', 3)
                target_reps = ex.get('target_reps', 10)
                st.metric("Sets × Reps", f"{target_sets} × {target_reps}")

            with col2:
                suggested_weight = ex.get('suggested_weight_lbs')
                if suggested_weight:
                    st.metric("Suggested Weight", f"{suggested_weight:.0f} lbs")
                else:
                    st.metric("Weight", "Your choice")


def render_adjustment_history(adjustments: list[dict]):
    """
    Render history of chat-based template adjustments.

    Args:
        adjustments: List of adjustment dicts with user_message, ai_response, timestamp
    """
    if not adjustments:
        return

    st.divider()
    st.subheader("✏️ Adjustments Made")

    # Show last 3 adjustments (most recent first)
    for adj in reversed(adjustments[-3:]):
        timestamp = adj.get('timestamp', '')
        if timestamp:
            time_str = datetime.fromisoformat(timestamp).strftime("%I:%M %p")
            st.caption(f"🕐 {time_str}")

        st.markdown(f"**You:** {adj['user_message']}")
        st.info(f"**AI:** {adj['ai_response']}")
        st.caption("")  # Spacing


def render_planning_chat_interface():
    """
    Render the chat interface for template modifications.

    Returns:
        User's input message (or None if no input)
    """
    st.subheader("💬 Modify Your Plan")
    st.caption("Ask to change exercises, equipment, or focus")

    # Use a form to prevent reprocessing on rerun
    with st.form(key="planning_chat_form", clear_on_submit=True):
        planning_input = st.text_input(
            "Planning chat",
            placeholder="e.g., 'No barbell today' or 'Add more shoulder work'",
            label_visibility="collapsed"
        )

        submitted = st.form_submit_button("Update Plan", use_container_width=True)

        if submitted and planning_input and planning_input.strip():
            return planning_input

    return None


def render_equipment_constraints(equipment_unavailable: list[str] | None):
    """
    Render current equipment constraints if any.

    Args:
        equipment_unavailable: List of unavailable equipment
    """
    if equipment_unavailable:
        st.warning(
            f"⚠️ **Equipment not available:** {', '.join(equipment_unavailable)}"
        )


def render_start_workout_button() -> bool:
    """
    Render the "Start Workout" button.

    Returns:
        True if button was clicked, False otherwise
    """
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        clicked = st.button(
            "🏋️ Start Workout",
            type="primary",
            use_container_width=True,
            key="start_workout_btn"
        )

    return clicked
