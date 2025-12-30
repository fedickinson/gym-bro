"""
Trash Page - View and restore deleted workouts.

Soft-deleted workouts are kept for 30 days before permanent deletion.
"""

import streamlit as st
from datetime import datetime, timedelta
from src.ui.session import init_session_state
from src.ui.navigation import render_bottom_nav
from src.ui.confirmation_dialogs import (
    show_permanent_delete_warning,
    show_bulk_permanent_delete_warning
)
from src.data import get_deleted_logs, restore_log

# Page configuration
st.set_page_config(
    page_title="Trash - Gym Bro",
    page_icon="🗑️",
    layout="centered"
)

# Initialize session state
init_session_state()

# Render bottom navigation
st.session_state.current_page = 'Trash'
render_bottom_nav('Trash')

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

/* Green restore button styling */
button:has(p:contains("♻️")) {
    height: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
    padding: 0 !important;
    font-size: 24px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    background-color: #2e7d32 !important;
    color: white !important;
    border: 1px solid #1b5e20 !important;
}

button:has(p:contains("♻️")):hover {
    background-color: #1b5e20 !important;
}

/* Red delete buttons in trash page */
button[kind="secondary"]:has(p:contains("Delete")),
button[kind="secondary"]:has(p:contains("🗑️")),
button:has(p:contains("🔥")) {
    background-color: #d32f2f !important;
    color: white !important;
    border: 1px solid #b71c1c !important;
}

button[kind="secondary"]:has(p:contains("Delete")):hover,
button[kind="secondary"]:has(p:contains("🗑️")):hover,
button:has(p:contains("🔥")):hover {
    background-color: #b71c1c !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Sidebar Navigation & Stats
# ============================================================================

with st.sidebar:
    st.title("🏋️ Gym Bro")
    st.caption("AI Fitness Coach")

    st.divider()

    # Quick navigation
    st.subheader("Quick Links")

    if st.button("🏠 Home", key="sidebar_home", use_container_width=True):
        st.switch_page("app.py")

    if st.button("📅 View History", key="sidebar_history", use_container_width=True):
        st.switch_page("pages/3_History.py")

    if st.button("📊 View Progress", key="sidebar_progress", use_container_width=True):
        st.switch_page("pages/4_Progress.py")

    st.divider()

    # Quick stats
    st.subheader("Stats")

    try:
        from src.data import get_workout_count, get_all_logs, get_deleted_logs
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

        # Trash stats
        deleted = get_deleted_logs()
        if deleted:
            st.metric("In Trash", len(deleted))

    except Exception as e:
        st.caption("Stats unavailable")

    st.divider()
    st.caption("Version 1.0.0")

# ============================================================================
# Page Content
# ============================================================================

st.title("🗑️ Trash")
st.caption("Deleted workouts are kept for 30 days before permanent deletion")

# ============================================================================
# Get Deleted Workouts
# ============================================================================

try:
    deleted_logs = get_deleted_logs()

    if not deleted_logs:
        st.info("🎉 Trash is empty! No deleted workouts to show.")
    else:
        st.caption(f"Found {len(deleted_logs)} deleted workout{'s' if len(deleted_logs) != 1 else ''}")

        # ====================================================================
        # Cleanup Action
        # ====================================================================

        # Calculate how many are old enough for cleanup
        cutoff_date = datetime.now() - timedelta(days=30)
        old_count = sum(
            1 for log in deleted_logs
            if log.get('deleted_at') and datetime.fromisoformat(log['deleted_at']) < cutoff_date
        )

        if old_count > 0:
            st.warning(f"⚠️ {old_count} workout{'s' if old_count != 1 else ''} {'have' if old_count != 1 else 'has'} been deleted for 30+ days")

            if st.button(f"🔥 Permanently Delete Old Workouts ({old_count})", type="primary"):
                show_bulk_permanent_delete_warning(old_count)

        st.divider()

        # ====================================================================
        # Display Deleted Workouts
        # ====================================================================

        for log in deleted_logs:
            workout_type = log.get('type', 'Unknown')
            workout_date = log.get('date', 'Unknown date')
            workout_id = log.get('id', '')
            deleted_at = log.get('deleted_at', '')

            # Calculate days since deletion
            days_ago = "Unknown"
            if deleted_at:
                try:
                    deleted_dt = datetime.fromisoformat(deleted_at)
                    delta = datetime.now() - deleted_dt
                    days_ago = delta.days
                except ValueError:
                    pass

            # Warning if approaching permanent deletion
            warning_icon = ""
            if isinstance(days_ago, int) and days_ago >= 30:
                warning_icon = "⚠️ "
            elif isinstance(days_ago, int) and days_ago >= 25:
                warning_icon = "🔔 "

            # Create columns: expander on left, restore button on right
            col_expand, col_restore = st.columns([6, 1])

            with col_expand:
                with st.expander(f"{warning_icon}**{workout_type}** - {workout_date} (deleted {days_ago} day{'s' if days_ago != 1 else ''} ago)", expanded=False):
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

                    # Display deletion info
                    st.divider()
                    if isinstance(days_ago, int):
                        days_left = 30 - days_ago
                        if days_left > 0:
                            st.caption(f"⏰ Will be permanently deleted in {days_left} day{'s' if days_left != 1 else ''}")
                        else:
                            st.error(f"⚠️ Eligible for permanent deletion (deleted {days_ago} days ago)")

                        # Action buttons inside expander
                        st.divider()
                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button("🔥 Delete Forever", key=f"permanent_{workout_id}", use_container_width=True):
                                # Show permanent delete confirmation
                                show_permanent_delete_warning(log)

                        with col2:
                            st.caption(f"ID: {workout_id}")

            with col_restore:
                # Restore button aligned with expander header
                if st.button("♻️", key=f"restore_{workout_id}", help="Restore workout"):
                    if restore_log(workout_id):
                        st.success("✅ Workout restored!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to restore workout")

except Exception as e:
    st.error(f"Error loading deleted workouts: {str(e)}")
