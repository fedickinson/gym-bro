"""
History Page - Browse and filter past workouts.

Allows filtering by type, date range, and exercise search.
"""

import streamlit as st
from datetime import date, timedelta
from src.ui.session import init_session_state
from src.ui.navigation import render_bottom_nav
from src.ui.confirmation_dialogs import show_delete_confirmation, show_bulk_delete_confirmation
from src.data import get_all_logs, get_logs_by_date_range

# Page configuration
st.set_page_config(
    page_title="History - Gym Bro",
    page_icon="📅",
    layout="centered"  # Centered for better desktop UX
)

# Initialize session state
init_session_state()

# Render bottom navigation
st.session_state.current_page = 'History'
render_bottom_nav('History')

# Desktop optimizations
st.markdown("""
<style>
@media (min-width: 769px) {
    /* Hide bottom nav on desktop */
    .bottom-nav {
        display: none !important;
    }

    /* Better spacing */
    .main .block-container {
        padding: 2rem 2rem !important;
        max-width: 1000px !important;
    }
}

@media (max-width: 768px) {
    /* Mobile padding with space for bottom nav */
    .main .block-container {
        padding: 1rem 1rem 5rem 1rem !important;
    }
}

/* Red delete buttons */
button[kind="secondary"]:has(p:contains("Delete")),
button[kind="secondary"]:has(p:contains("🗑️")),
button:has(p:contains("❌")) {
    background-color: #d32f2f !important;
    color: white !important;
    border: 1px solid #b71c1c !important;
}

button[kind="secondary"]:has(p:contains("Delete")):hover,
button[kind="secondary"]:has(p:contains("🗑️")):hover,
button:has(p:contains("❌")):hover {
    background-color: #b71c1c !important;
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
    st.title("🏋️ Gym Bro")
    st.caption("AI Fitness Coach")

    st.divider()

    # Quick navigation
    st.subheader("Quick Links")

    if st.button("🏠 Home", key="sidebar_hist_home", use_container_width=True):
        st.switch_page("app.py")

    if st.button("📊 View Progress", key="sidebar_hist_progress", use_container_width=True):
        st.switch_page("pages/4_Progress.py")

    if st.button("🗑️ View Trash", key="sidebar_hist_trash", use_container_width=True):
        st.switch_page("pages/5_Trash.py")

    st.divider()

    # Quick stats
    st.subheader("Stats")

    try:
        from src.data import get_workout_count, get_all_logs
        from datetime import date, timedelta

        workouts_last_7 = get_workout_count(7)
        workouts_last_30 = get_workout_count(30)

        st.metric("Last 7 Days", workouts_last_7)
        st.metric("Last 30 Days", workouts_last_30)

        # Workout streak
        logs = get_all_logs()
        if logs:
            # Calculate streak (consecutive days with workouts)
            logs_by_date = {}
            for log in logs:
                log_date = log.get('date')
                if log_date:
                    logs_by_date[log_date] = True

            streak = 0
            current_date = date.today()
            while current_date.isoformat() in logs_by_date:
                streak += 1
                current_date -= timedelta(days=1)

            if streak > 0:
                st.metric("Current Streak", f"{streak} day{'s' if streak != 1 else ''}")

    except Exception as e:
        st.caption("Stats unavailable")

    st.divider()

    # History-specific filters below
    st.subheader("Filters")

    # Workout type filter
    workout_types = ['All', 'Push', 'Pull', 'Legs', 'Upper', 'Lower', 'Other']
    selected_type = st.selectbox("Workout Type", workout_types)

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
    selected_range = st.selectbox("Date Range", list(date_range_options.keys()), index=4)  # Default: Last 3 months
    days = date_range_options[selected_range]

    # Exercise search
    search_exercise = st.text_input("Search Exercise", placeholder="e.g., bench press")

    st.divider()

    # Clear filters button
    if st.button("Clear Filters", use_container_width=True):
        st.rerun()

    st.divider()
    st.caption("Version 1.0.0")

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

        st.divider()
        # Display most recent first
        logs_sorted = sorted(logs, key=lambda x: x.get('date', ''), reverse=True)

        for log in logs_sorted:
            workout_type = log.get('type', 'Unknown')
            workout_date = log.get('date', 'Unknown date')
            workout_id = log.get('id', '')

            # Checkbox and expander
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
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🗑️ Delete", key=f"delete_{workout_id}"):
                            # Show confirmation dialog
                            show_delete_confirmation(log)

                    with col2:
                        st.caption(f"ID: {workout_id}")

except Exception as e:
    st.error(f"Error loading workouts: {str(e)}")
