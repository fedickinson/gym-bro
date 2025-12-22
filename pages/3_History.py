"""
History Page - Browse and filter past workouts.

Allows filtering by type, date range, and exercise search.
"""

import streamlit as st
from datetime import date, timedelta
from src.ui.session import init_session_state
from src.ui.navigation import render_bottom_nav
from src.data import get_all_logs, get_logs_by_date_range, delete_log

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
        # Display most recent first
        logs_sorted = sorted(logs, key=lambda x: x.get('date', ''), reverse=True)

        for log in logs_sorted:
            workout_type = log.get('type', 'Unknown')
            workout_date = log.get('date', 'Unknown date')
            workout_id = log.get('id', '')

            with st.expander(f"**{workout_type}** - {workout_date}", expanded=False):
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
                        if delete_log(workout_id):
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete")

                with col2:
                    st.caption(f"ID: {workout_id}")

except Exception as e:
    st.error(f"Error loading workouts: {str(e)}")
