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

    # More compact header - single line with type and duration
    duration = template.get('estimated_duration_min')
    if duration:
        st.markdown(f"**💪 {template.get('type', 'Unknown')} Workout** • {len(template['exercises'])} exercises • ~{duration} min")
    else:
        st.markdown(f"**💪 {template.get('type', 'Unknown')} Workout** • {len(template['exercises'])} exercises")

    if compact:
        # COMPACT MODE: Exercise name is clickable to show details
        for i, ex in enumerate(template['exercises'], 1):
            sets = ex.get('target_sets', 3)
            reps = ex.get('target_reps', 10)
            weight = ex.get('suggested_weight_lbs')

            # Format: "1. Squat - 3×8 @ 185 lbs"
            exercise_line = f"{i}. {ex.get('name')} - {sets}×{reps}"
            if weight:
                exercise_line += f" @ {weight:.0f} lbs"

            # Make exercise name itself clickable for details
            reasoning = ex.get('reasoning', '')
            if reasoning:
                # Exercise line IS the expander label - click to see details
                with st.expander(exercise_line, expanded=False):
                    st.caption(reasoning)
            else:
                # No reasoning, just show the exercise
                st.markdown(f"**{exercise_line}**")
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
    st.markdown("**💬 Modify Your Plan**")
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
    days_left: int,
    rotation_status: str = None
):
    """
    Render individual workout type progress card.

    Shows completion status, progress bar, and last workout date.

    Args:
        workout_type: Type of workout (Push, Pull, Legs, etc.)
        completed: Number completed this week
        target: Weekly target
        remaining: Number remaining
        days_left: Days left in week
        rotation_status: "behind" | "pending" | None
    """
    # Determine status emoji and color based on rotation status
    if rotation_status == "behind":
        # BEHIND: Should have done before current rotation position
        status_emoji = "⚠️"
        progress_color = "error"
    elif completed >= target:
        # COMPLETED: Hit the weekly target
        status_emoji = "✅"
        progress_color = "success"
    elif completed > 0:
        # IN PROGRESS: Started but not at target
        status_emoji = "⏳"
        progress_color = "warning"
    else:
        # PENDING: Not started, still okay
        status_emoji = "○"
        progress_color = "info"

    # Calculate progress percentage
    if target > 0:
        progress_percent = min(completed / target, 1.0)
    else:
        progress_percent = 0.0

    # Card header with status
    if progress_color == "success":
        st.success(f"**{workout_type}** {status_emoji}")
    elif progress_color == "error":
        st.error(f"**{workout_type}** {status_emoji}")
    elif progress_color == "warning":
        st.warning(f"**{workout_type}** {status_emoji}")
    else:
        st.info(f"**{workout_type}** {status_emoji}")

    # Show status message for behind
    if rotation_status == "behind":
        st.caption("⚠️ Should have done before current rotation position")

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

    # --- Overall Summary (ULTRA-COMPACT for mobile) ---
    total_remaining = sum(remaining.values())
    if days_left == 1:
        days_label = "last day"
    elif days_left == 0:
        days_label = "ends today"
    else:
        days_label = f"{days_left}d left"

    # Ultra-compact: Everything on one line with thin progress bar
    st.markdown(f"**📅 This Week:** {total_completed}/{total_target} • {int(overall_percent * 100)}% • {total_remaining} to go • {days_label}")

    # Thinner progress bar via custom CSS
    st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        height: 0.3rem;
    }
    </style>
    """, unsafe_allow_html=True)
    st.progress(min(overall_percent, 1.0))

    # Get rotation status from weekly_status
    rotation_status_dict = status.get("rotation_status", {})

    # --- Workout Type Progress (COLLAPSED IN COMPACT MODE) ---
    if compact:
        # Compact mode: Show details in expander
        with st.expander("📋 View detailed breakdown by workout type", expanded=False):
            _render_workout_type_details(completed, targets, remaining, days_left, rotation_status_dict)
    else:
        # Full mode: Show details inline
        st.divider()
        st.markdown("#### Workout Types")
        _render_workout_type_details(completed, targets, remaining, days_left, rotation_status_dict)


def _render_workout_type_details(completed, targets, remaining, days_left, rotation_status_dict=None):
    """
    Helper to render workout type details (used by both compact and full modes).

    Args:
        completed: Dict of completed counts by type
        targets: Dict of targets by type
        remaining: Dict of remaining counts by type
        days_left: Days remaining in week
        rotation_status_dict: Dict mapping workout type to rotation status ("behind" | "pending")
    """
    if rotation_status_dict is None:
        rotation_status_dict = {}

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
                    days_left,
                    rotation_status_dict.get(workout_types[i])
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
                    days_left,
                    rotation_status_dict.get(workout_types[i])
                )

            # Second workout type in row
            with col2:
                if i + 1 < len(workout_types):
                    _render_workout_type_card(
                        workout_types[i + 1],
                        completed.get(workout_types[i + 1], 0),
                        targets.get(workout_types[i + 1], 0),
                        remaining.get(workout_types[i + 1], 0),
                        days_left,
                        rotation_status_dict.get(workout_types[i + 1])
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
