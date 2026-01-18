"""
Planning UI Components - Pre-workout planning interface.

Components for AI-guided workout planning, including:
- Template preview with exercise details
- Chat interface for modifications
- Adjustment history display
"""

import streamlit as st
from datetime import datetime


def render_template_preview(template: dict, compact: bool = False):
    """
    Render a workout template preview with exercises and details.

    NEW: Compact mode hides verbose AI rationale by default for mobile.

    Args:
        template: Template dict with exercises, coaching notes, etc.
        compact: If True, show abbreviated version with collapsed details
    """
    if not template or not template.get('exercises'):
        st.warning("No template loaded")
        return

    # Display workout type and count
    st.subheader(f"💪 {template.get('type', 'Unknown')} Workout")

    # Show estimated duration if available
    duration = template.get('estimated_duration_min')
    if duration:
        st.caption(f"{len(template['exercises'])} exercises • ~{duration} min")
    else:
        st.caption(f"{len(template['exercises'])} exercises")

    if compact:
        # COMPACT MODE: Show exercise name, sets×reps @ weight on one line
        # Hide AI rationale in collapsed expander
        for i, ex in enumerate(template['exercises'], 1):
            sets = ex.get('target_sets', 3)
            reps = ex.get('target_reps', 10)
            weight = ex.get('suggested_weight_lbs')

            # Format: "1. Squat - 3×8 @ 185 lbs"
            exercise_line = f"**{i}. {ex.get('name')}** - {sets}×{reps}"
            if weight:
                exercise_line += f" @ {weight:.0f} lbs"

            st.markdown(exercise_line)

            # NEW: Collapsible details for rationale
            reasoning = ex.get('reasoning', '')
            if reasoning:
                with st.expander("💡 View details", expanded=False):
                    st.caption(reasoning)

        st.caption("👆 You can modify these via chat below")
    else:
        # Full mode: Show coaching notes and expandable exercises
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


def render_weekly_progress_summary(compact: bool = False):
    """
    Render comprehensive weekly workout progress summary.

    Args:
        compact: If True, show abbreviated version (mobile-friendly)

    Shows:
    - Overall week completion percentage
    - Progress bars for each workout type (collapsed in compact mode)
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

    # --- Overall Summary (ALWAYS SHOWN) ---
    st.markdown("### 📅 This Week")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric(
            "Progress",
            f"{total_completed}/{total_target}",
            delta=f"{int(overall_percent * 100)}%"
        )

    with col2:
        total_remaining = sum(remaining.values())
        # Better messaging for last day
        if days_left == 1:
            days_label = "Last day!"
        elif days_left == 0:
            days_label = "Week ends"
        else:
            days_label = f"{days_left} days"

        st.metric(
            "Remaining",
            f"{total_remaining} to go",
            delta=days_label
        )

    # Overall progress bar (cap at 100% if over target)
    st.progress(min(overall_percent, 1.0))

    # --- Workout Type Progress (COLLAPSED IN COMPACT MODE) ---
    if compact:
        # Compact mode: Show details in expander
        with st.expander("📋 View detailed breakdown by workout type", expanded=False):
            _render_workout_type_details(completed, targets, remaining, days_left)
    else:
        # Full mode: Show details inline
        st.divider()
        st.markdown("#### Workout Types")
        _render_workout_type_details(completed, targets, remaining, days_left)


def _render_workout_type_details(completed, targets, remaining, days_left):
    """
    Helper to render workout type details (used by both compact and full modes).
    """
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

def render_catch_up_suggestion(catch_up_combos: list[dict]):
    """
    Render catch-up mode UI with smart workout combos.

    NEW: Shows workouts grouped by day (e.g., "Today: Legs + Upper (70 min)").

    Args:
        catch_up_combos: List of combo dicts from suggest_next_workout()
            [
                {
                    "day": "Today",
                    "types": ["Legs", "Upper"],
                    "duration_min": 70,
                    "rest_between_min": 5
                },
                ...
            ]
    """
    if not catch_up_combos:
        return

    total_workouts = sum(len(combo["types"]) for combo in catch_up_combos)
    days_needed = len(catch_up_combos)

    # Alert banner
    st.error(f"⚡ **Catch-Up Mode:** {total_workouts} workouts in {days_needed} day(s)!")

    st.markdown("**Recommended Schedule:**")

    # Show each day's combo
    for combo in catch_up_combos:
        day = combo["day"]
        types = combo["types"]
        duration = combo["duration_min"]

        # Format: "Today: Legs + Upper (70 min)"
        combo_label = " + ".join(types)

        # Card for this day's combo
        if day == "Today":
            st.info(f"**{day}**: {combo_label} (~{duration} min)")
        else:
            st.caption(f"{day}: {combo_label} (~{duration} min)")

    st.divider()

    # Express mode toggle (applies to all combos)
    express_mode = st.checkbox(
        "Use Express versions (shorter workouts)",
        value=True,
        key="express_mode_toggle",
        help="Express versions keep compound lifts but reduce volume by ~40%"
    )

    st.session_state.use_express_mode = express_mode

    # Total time for today's combo
    today_combo = catch_up_combos[0]
    today_types = today_combo["types"]

    if express_mode:
        total_time = today_combo["duration_min"]
        st.caption(f"💡 **Today's total time:** ~{total_time} minutes")
    else:
        full_time = len(today_types) * 50
        st.caption(f"⏱️ **Today's total time:** ~{full_time} minutes")

    # Suggested approach
    if len(today_types) == 1:
        st.info(f"💪 **Start with {today_types[0]}** to get back on track!")
    else:
        st.info(
            f"💪 **Complete {today_types[0]} first**, then immediately log "
            f"{today_types[1]} to finish strong today!"
        )
