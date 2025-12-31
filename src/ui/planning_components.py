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
    Render the "Start Workout" and "Cancel" buttons.

    Returns:
        True if "Start Workout" was clicked, False otherwise
        (Cancel is handled internally)
    """
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        start_clicked = st.button(
            "🏋️ Start Workout",
            type="primary",
            use_container_width=True,
            key="start_workout_btn"
        )

    with col2:
        cancel_clicked = st.button(
            "❌ Cancel",
            use_container_width=True,
            key="cancel_planning_btn"
        )

    # Handle cancel - navigate away from workout page
    if cancel_clicked:
        from src.ui.session import reset_workout_session
        reset_workout_session()
        # Navigate to home instead of staying on this page
        st.switch_page("app.py")

    return start_clicked


# ============================================================================
# Weekly Progress Summary Components
# ============================================================================

def _get_days_since_last_workout(workout_type: str) -> tuple[int, str]:
    """
    Calculate days since last workout of given type.

    Args:
        workout_type: Workout type (Push, Pull, Legs, etc.)

    Returns:
        Tuple of (days_count, display_string)
        - days_count: -1 if never done, otherwise days since
        - display_string: "2 days ago", "Yesterday", "Today", or "Never done"
    """
    from src.tools.recommend_tools import get_last_workout_by_type

    result = get_last_workout_by_type.invoke({"workout_type": workout_type})

    if not result.get("found"):
        return (-1, "Never done")

    days_since = result.get("days_since", 0)

    if days_since == 0:
        return (0, "Today")
    elif days_since == 1:
        return (1, "Yesterday")
    else:
        return (days_since, f"{days_since} days ago")


def _render_workout_type_card(
    workout_type: str,
    completed: int,
    target: int,
    remaining: int,
    days_left: int
):
    """
    Render individual workout type progress card.

    Shows completion status, progress bar, and last workout date.
    """
    # Determine status
    if completed >= target:
        status_emoji = "✓"
        progress_percent = 1.0
    elif completed > 0:
        status_emoji = "⏳"
        progress_percent = min(completed / target, 1.0) if target > 0 else 0
    else:
        status_emoji = "○"
        progress_percent = 0.0

    # Check if urgent (need to do multiple in remaining days)
    is_urgent = remaining > 0 and remaining >= days_left

    # Card header with status
    if completed >= target:
        st.success(f"**{workout_type}** {status_emoji}")
    elif is_urgent:
        st.error(f"**{workout_type}** {status_emoji}")
    else:
        st.info(f"**{workout_type}** {status_emoji}")

    # Progress count
    st.caption(f"{completed}/{target} complete")

    # Progress bar
    st.progress(progress_percent)

    # Last workout date
    days_since, date_str = _get_days_since_last_workout(workout_type)

    if days_since == 0:
        st.caption(f"🟢 {date_str}")
    elif days_since == -1:
        st.caption(f"⚪ {date_str}")
    elif days_since <= 3:
        st.caption(f"🟡 {date_str}")
    else:
        st.caption(f"🟠 {date_str}")

    st.markdown("")  # Spacing


def render_weekly_progress_summary():
    """
    Render comprehensive weekly workout progress summary.

    Shows:
    - Overall week completion percentage
    - Progress bars for each workout type
    - Days since last workout of each type
    - Days remaining in week
    """
    from src.tools.recommend_tools import get_weekly_split_status

    # Get weekly status data
    status = get_weekly_split_status.invoke({})

    completed = status.get("completed", {})
    targets = status.get("targets", {})
    remaining = status.get("remaining", {})
    days_left = status.get("days_left_in_week", 7)

    # Calculate overall progress
    total_completed = sum(completed.values())
    total_target = sum(targets.values())
    overall_percent = (total_completed / total_target) if total_target > 0 else 0

    # --- Overall Summary ---
    st.markdown("### 📅 This Week")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric(
            "Week Progress",
            f"{total_completed}/{total_target} workouts",
            delta=f"{int(overall_percent * 100)}% complete"
        )

    with col2:
        total_remaining = sum(remaining.values())
        # Better messaging for last day
        if days_left == 1:
            days_label = "Last day!"
        elif days_left == 0:
            days_label = "Week ends today"
        else:
            days_label = f"{days_left} days"

        st.metric(
            "Days Left",
            days_label,
            delta=f"{total_remaining} to go"
        )

    # Overall progress bar (cap at 100% if over target)
    st.progress(min(overall_percent, 1.0))

    st.divider()

    # --- Workout Type Progress ---
    st.markdown("#### Workout Types")

    # Define workout types order
    workout_types = ["Push", "Pull", "Legs", "Upper", "Lower"]

    # Create 2-column layout for mobile
    for i in range(0, len(workout_types), 2):
        # Check if this is the last item and it's odd
        if i == len(workout_types) - 1:
            # Center the last item
            _, col_center, _ = st.columns([1, 2, 1])
            with col_center:
                _render_workout_type_card(
                    workout_types[i],
                    completed.get(workout_types[i], 0),
                    targets.get(workout_types[i], 0),
                    remaining.get(workout_types[i], 0),
                    days_left
                )
        else:
            col1, col2 = st.columns(2)

            # First workout type in row
            with col1:
                _render_workout_type_card(
                    workout_types[i],
                    completed.get(workout_types[i], 0),
                    targets.get(workout_types[i], 0),
                    remaining.get(workout_types[i], 0),
                    days_left
                )

            # Second workout type in row
            with col2:
                if i + 1 < len(workout_types):
                    _render_workout_type_card(
                        workout_types[i + 1],
                        completed.get(workout_types[i + 1], 0),
                        targets.get(workout_types[i + 1], 0),
                        remaining.get(workout_types[i + 1], 0),
                        days_left
                    )


# ============================================================================
# Catch-Up Mode Components
# ============================================================================

def render_catch_up_suggestion(catch_up_workouts: list[str], days_left: int, total_needed: int):
    """
    Render catch-up mode UI when multiple workouts needed in limited time.

    Shows:
    - Alert that user is in catch-up mode
    - All needed workout types as cards
    - Express version toggle
    - Time estimates
    - Recommended approach

    Args:
        catch_up_workouts: List of workout types needed (e.g., ["Upper", "Lower"])
        days_left: Days remaining in the week
        total_needed: Total number of workouts needed
    """
    # Alert banner
    st.error(f"⚡ **Catch-Up Mode:** {total_needed} workouts needed in {days_left} day(s)!")

    st.markdown("**Today's recommended workouts:**")

    # Show all needed workouts as cards
    cols = st.columns(len(catch_up_workouts))

    for i, workout_type in enumerate(catch_up_workouts):
        with cols[i]:
            # Card for each needed workout
            st.info(f"**{workout_type}**")

            # Time estimate (Express vs Full)
            if st.session_state.get('use_express_mode', True):
                st.caption("~35 min (Express)")
            else:
                st.caption("~50 min (Full)")

    st.divider()

    # Express mode toggle
    express_mode = st.checkbox(
        "Use Express versions (shorter workouts)",
        value=True,
        key="express_mode_toggle",
        help="Express versions keep compound lifts but reduce volume by ~40%"
    )

    if express_mode:
        total_time = len(catch_up_workouts) * 35
        st.caption(f"💡 Total time estimate: ~{total_time} minutes")
    else:
        total_time = len(catch_up_workouts) * 50
        st.caption(f"⏱️ Total time estimate: ~{total_time} minutes")

    # Store express mode preference
    st.session_state.use_express_mode = express_mode

    # Recommended approach
    if len(catch_up_workouts) == 1:
        st.info(
            f"💪 **Suggested approach:** Complete {catch_up_workouts[0]} to finish your week strong!"
        )
    elif len(catch_up_workouts) == 2:
        st.info(
            f"💪 **Suggested approach:** Complete {catch_up_workouts[0]} first, "
            f"then immediately log {catch_up_workouts[1]} to finish your week strong!"
        )
    else:
        remaining_workouts = ' and '.join(catch_up_workouts[1:])
        st.info(
            f"💪 **Suggested approach:** Complete {catch_up_workouts[0]} first, "
            f"then immediately log {remaining_workouts} to finish your week strong!"
        )
