"""
History Page - Browse and filter past workouts.

Allows filtering by type, date range, and exercise search.
"""

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import date, timedelta
from src.ui.session import init_session_state
from src.ui.navigation import render_bottom_nav, scroll_to_top
from src.ui.shared_components import render_sidebar
from src.ui.confirmation_dialogs import show_delete_confirmation, show_bulk_delete_confirmation
from src.data import get_all_logs, get_logs_by_date_range
from src.ui.styles import get_global_styles

# Page configuration
st.set_page_config(
    page_title="History - Gym Bro",
    page_icon="📅",
    layout="centered"  # Centered for better desktop UX
)

# Initialize session state
init_session_state()

# Scroll to top on page load
scroll_to_top()

# Render bottom navigation
st.session_state.current_page = 'History'
render_bottom_nav('History')

# Apply global design system styles
st.markdown(get_global_styles(), unsafe_allow_html=True)

# Page-specific styles
st.markdown("""
<style>
/* Red delete buttons */
button[kind="secondary"]:has(p:contains("Delete")),
button[kind="secondary"]:has(p:contains("🗑️")),
button:has(p:contains("❌")) {
    background-color: var(--color-destructive) !important;
    color: white !important;
    border: 1px solid var(--color-destructive-hover) !important;
}

button[kind="secondary"]:has(p:contains("Delete")):hover,
button[kind="secondary"]:has(p:contains("🗑️")):hover,
button:has(p:contains("❌")):hover {
    background-color: var(--color-destructive-hover) !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Page Content
# ============================================================================

st.title("📅 Workout History")

# ============================================================================
# Sidebar Filters
# ============================================================================

with st.sidebar:
    render_sidebar(current_page="History")

    st.divider()

    # History-specific filters below
    st.subheader("Filters")

    # Workout type filter
    workout_types = ['All', 'Push', 'Pull', 'Legs', 'Upper', 'Lower', 'Other']
    selected_type = st.selectbox("Workout Type", workout_types, key="sidebar_type")

    # Date range filter
    date_range_options = {
        'Last 7 days': 7,
        'Last 2 weeks': 14,
        'Last month': 30,
        'Last 2 months': 60,
        'Last 3 months': 90,
        'Last 6 months': 180,
        'This year': 365,
        'All time': 0
    }
    selected_range = st.selectbox("Date Range", list(date_range_options.keys()), index=7, key="sidebar_range")  # Default: All time
    days = date_range_options[selected_range]

    # Exercise search
    search_exercise = st.text_input("Search Exercise", placeholder="e.g., bench press", key="sidebar_search")

    st.divider()

    # Clear filters button
    if st.button("Clear Filters", use_container_width=True):
        st.rerun()

    st.divider()
    st.caption("Version 1.0.0")

# ============================================================================
# Mobile Filters (shown on mobile, hidden on desktop)
# ============================================================================

st.markdown('<div class="mobile-filters">', unsafe_allow_html=True)
with st.expander("🔍 Filters", expanded=False):
    # Workout type filter
    mobile_type = st.selectbox("Workout Type", workout_types, key="mobile_type")

    # Date range filter
    mobile_range = st.selectbox("Date Range", list(date_range_options.keys()), index=7, key="mobile_range")

    # Exercise search
    mobile_search = st.text_input("Search Exercise", placeholder="e.g., bench press", key="mobile_search")

    # Use mobile filter values if on mobile
    if 'mobile_type' in st.session_state:
        selected_type = mobile_type
        days = date_range_options[mobile_range]
        search_exercise = mobile_search

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# Apply Filters
# ============================================================================

try:
    # Get logs based on date range
    if days == 0:
        # All time
        logs = get_all_logs()
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        logs = get_logs_by_date_range(start_date, end_date)

    # Filter by type
    if selected_type != 'All':
        logs = [log for log in logs if log.get('type') == selected_type]

    # Filter by exercise
    if search_exercise:
        search_lower = search_exercise.lower()
        logs = [log for log in logs if any(
            search_lower in ex.get('name', '').lower()
            for ex in log.get('exercises', [])
        )]

    # ========================================================================
    # Display Results
    # ========================================================================

    st.caption(f"Found {len(logs)} workouts")

    if not logs:
        st.info("No workouts match your filters. Try adjusting the filters above.")
    else:
        # ====================================================================
        # Bulk Delete Controls
        # ====================================================================

        # Action buttons row
        st.markdown('<div class="action-button-row">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

        with col1:
            if st.button("✅ Select All", use_container_width=True):
                st.session_state.selected_workout_ids = {log.get('id') for log in logs}
                st.rerun()

        with col2:
            if st.button("❌ Deselect All", use_container_width=True):
                st.session_state.selected_workout_ids = set()
                st.rerun()

        with col3:
            selected_count = len(st.session_state.selected_workout_ids)
            if selected_count > 0:
                if st.button(f"🗑️ Delete ({selected_count})", type="primary", use_container_width=True):
                    # Get selected workouts
                    selected_workouts = [log for log in logs if log.get('id') in st.session_state.selected_workout_ids]
                    # Show bulk confirmation dialog
                    show_bulk_delete_confirmation(selected_workouts, on_confirm_callback=lambda: st.session_state.selected_workout_ids.clear())
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        # Display most recent first
        logs_sorted = sorted(logs, key=lambda x: x.get('date', ''), reverse=True)

        for log in logs_sorted:
            workout_type = log.get('type', 'Unknown')
            workout_date = log.get('date', 'Unknown date')
            workout_id = log.get('id', '')

            # Checkbox and expander
            st.markdown('<div class="checkbox-row">', unsafe_allow_html=True)
            col_check, col_expand = st.columns([0.1, 0.9])

            with col_check:
                # Checkbox for bulk selection
                is_selected = workout_id in st.session_state.selected_workout_ids
                if st.checkbox("", value=is_selected, key=f"check_{workout_id}", label_visibility="collapsed"):
                    st.session_state.selected_workout_ids.add(workout_id)
                else:
                    st.session_state.selected_workout_ids.discard(workout_id)

            with col_expand:
                # Create expander title with supplementary work badge
                expander_title = f"**{workout_type}** - {workout_date}"
                supplementary = log.get('supplementary_work', [])
                if supplementary:
                    # Handle both old (list of strings) and new (list of dicts) formats
                    if isinstance(supplementary[0], str):
                        # Old format
                        supp_badges = ' '.join([f"💪 {s.title()}" for s in supplementary])
                        expander_title += f" | {supp_badges}"
                    else:
                        # New format
                        supp_badges = ' '.join([f"💪 {s.get('type', '').title()}" for s in supplementary])
                        expander_title += f" | {supp_badges}"

                with st.expander(expander_title, expanded=False):
                    # Display exercises with full details
                    exercises = log.get('exercises', [])

                    if exercises:
                        for ex in exercises:
                            st.write(f"**{ex.get('name', 'Unknown')}**")

                            sets = ex.get('sets', [])
                            if sets:
                                for i, s in enumerate(sets, 1):
                                    reps = s.get('reps', '?')
                                    weight = s.get('weight_lbs')

                                    if weight:
                                        st.caption(f"  Set {i}: {reps} reps × {weight} lbs")
                                    else:
                                        st.caption(f"  Set {i}: {reps} reps (bodyweight)")
                            else:
                                st.caption("  No sets recorded")

                            st.write("")  # Spacing

                    # Display supplementary work (abs, cardio, etc.)
                    if supplementary and isinstance(supplementary[0], dict):
                        for supp_work in supplementary:
                            supp_type = supp_work.get('type', 'Unknown')
                            supp_exercises = supp_work.get('exercises', [])

                            if supp_exercises:
                                st.divider()
                                st.write(f"**{supp_type.title()} Session:**")

                                for ex in supp_exercises:
                                    st.write(f"  **{ex.get('name', 'Unknown')}**")

                                    sets = ex.get('sets', [])
                                    if sets:
                                        for i, s in enumerate(sets, 1):
                                            reps = s.get('reps', '?')
                                            weight = s.get('weight_lbs')
                                            notes = s.get('notes', '')

                                            if weight:
                                                st.caption(f"    Set {i}: {reps} reps × {weight} lbs {notes}")
                                            else:
                                                if notes:
                                                    st.caption(f"    Set {i}: {reps} reps - {notes}")
                                                else:
                                                    st.caption(f"    Set {i}: {reps} reps")

                                    st.write("")  # Spacing

                                # Show supplementary notes if present
                                supp_notes = supp_work.get('notes')
                                if supp_notes:
                                    st.caption(f"  *{supp_notes}*")

                    # Display warmup if present
                    warmup = log.get('warmup')
                    if warmup:
                        st.divider()
                        st.write("**Warmup:**")
                        if warmup.get('type') == 'jog':
                            distance = warmup.get('distance_miles', '?')
                            duration = warmup.get('duration_min', '?')
                            st.caption(f"Jog: {distance} miles, {duration} min")

                    # Display notes
                    if log.get('notes'):
                        st.divider()
                        st.info(f"**Notes:** {log['notes']}")

                    # Action buttons
                    st.divider()
                    st.markdown('<div class="action-button-row">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("✏️ Edit", key=f"edit_{workout_id}"):
                            # Store workout in session state for edit dialog
                            st.session_state.editing_workout = log
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{workout_id}"):
                            # Show confirmation dialog
                            show_delete_confirmation(log)

                    with col3:
                        st.caption(f"ID: {workout_id}")

                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error loading workouts: {str(e)}")

# ============================================================================
# Edit Dialog
# ============================================================================

# Show workout edit dialog if a workout is being edited
if st.session_state.get("editing_workout"):
    @st.dialog("Edit Workout")
    def show_workout_edit_dialog(workout: dict):
        """
        Show dialog for editing exercise weights in a workout.

        User selects exercise and set, then enters new weight.
        """
        from src.data import update_exercise_weight

        st.info("Select the exercise and set to edit:")

        # Extract workout info
        workout_id = workout.get('id')
        workout_date = workout.get('date', 'Unknown')
        workout_type = workout.get('type', 'Unknown')
        exercises = workout.get('exercises', [])

        if not exercises:
            st.warning("This workout has no exercises to edit.")
            if st.button("Close"):
                del st.session_state.editing_workout
                st.rerun()
            return

        # Display workout summary
        st.markdown(f"**{workout_type}** from **{workout_date}**")
        st.divider()

        # Exercise selector
        exercise_options = [f"{i+1}. {ex.get('name', 'Unknown')}" for i, ex in enumerate(exercises)]
        selected_exercise_str = st.selectbox(
            "Select Exercise",
            exercise_options,
            key="edit_exercise_select"
        )

        # Extract index from selection (e.g., "1. Bench Press" -> 0)
        exercise_index = int(selected_exercise_str.split('.')[0]) - 1
        selected_exercise = exercises[exercise_index]
        exercise_name = selected_exercise.get('name', 'Unknown')

        # Set selector
        sets = selected_exercise.get('sets', [])
        if not sets:
            st.warning(f"**{exercise_name}** has no sets to edit.")
        else:
            # Create set options with current weights
            set_options = []
            for i, s in enumerate(sets):
                weight = s.get('weight_lbs')
                reps = s.get('reps', '?')
                if weight is not None:
                    set_options.append(f"Set {i+1}: {reps} reps @ {weight} lbs")
                else:
                    set_options.append(f"Set {i+1}: {reps} reps (bodyweight)")

            # Add "All sets" option if multiple sets with weights
            weights = [s.get('weight_lbs') for s in sets if s.get('weight_lbs') is not None]
            if len(weights) > 1:
                set_options.append("All sets")

            selected_set_str = st.selectbox(
                "Select Set",
                set_options,
                key="edit_set_select"
            )

            # Determine set index
            if "All sets" in selected_set_str:
                set_index = "all"
                old_weight = sets[0].get('weight_lbs', 0) if sets else 0
            else:
                set_index = int(selected_set_str.split(':')[0].split(' ')[1]) - 1
                old_weight = sets[set_index].get('weight_lbs', 0)

            # Weight input
            st.markdown("### New Weight")
            new_weight = st.number_input(
                "Weight (lbs)",
                value=float(old_weight),
                min_value=0.0,
                max_value=1000.0,
                step=2.5,
                key="edit_weight_input"
            )

            # Show change
            if new_weight != old_weight:
                delta = new_weight - old_weight
                st.metric("Change", f"{delta:+.1f} lbs", delta=f"{delta:+.1f}")

            # Optional reason
            reason = st.text_input(
                "Reason for edit (optional)",
                placeholder="e.g., 'Logged wrong weight'",
                key="edit_reason_input"
            )

            # Action buttons
            st.divider()
            st.markdown('<div class="action-button-row">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            with col1:
                if st.button("❌ Cancel", use_container_width=True):
                    del st.session_state.editing_workout
                    st.rerun()

            with col2:
                if st.button("✅ Save", type="primary", use_container_width=True):
                    try:
                        success = update_exercise_weight(
                            log_id=workout_id,
                            exercise_index=exercise_index,
                            set_index=set_index,
                            new_weight=new_weight,
                            reason=reason if reason else None
                        )

                        if success:
                            st.success(f"✅ Weight updated to {new_weight} lbs!")
                            del st.session_state.editing_workout

                            # Brief pause to show success
                            import time
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Failed to update weight. The workout may have been deleted.")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

            st.markdown('</div>', unsafe_allow_html=True)

    # Show the dialog
    show_workout_edit_dialog(st.session_state.editing_workout)
