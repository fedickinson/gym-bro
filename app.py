"""
Gym Bro - Mobile-First AI Fitness Coach

Main home page with weekly split status and quick actions.
"""

# Load environment variables FIRST (before any other imports)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import date, timedelta
from src.ui.session import init_session_state
from src.ui.navigation import render_bottom_nav
from src.ui.confirmation_dialogs import show_delete_confirmation
from src.tools.recommend_tools import get_weekly_split_status
from src.data import get_all_logs, get_logs_by_date_range
from src.ui.styles import get_global_styles

# CRITICAL: Import audio recorder here to initialize component for multipage app
try:
    from audio_recorder_streamlit import audio_recorder
except:
    pass  # Component will be available in pages even if import fails here

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Gym Bro - AI Fitness Coach",
    page_icon="🏋️",
    layout="centered",  # Centered for better desktop UX
    initial_sidebar_state="auto"
)

# Initialize session state
init_session_state()

# Validate templates exist for all workout types
def validate_templates():
    """Validate that all workout types have corresponding templates."""
    from src.data import get_template
    required_types = ["Push", "Pull", "Legs", "Upper", "Lower"]
    missing = []

    for workout_type in required_types:
        template = get_template(workout_type.lower())
        if not template:
            missing.append(workout_type)

    if missing:
        st.warning(f"⚠️ Missing templates for: {', '.join(missing)}")
        st.caption("Some workout types may not load properly. Check data/templates.json")

# Call validation on app startup
validate_templates()

# Render bottom navigation
st.session_state.current_page = 'Home'
render_bottom_nav('Home')

# ============================================================================
# Apply Global Design System
# ============================================================================

st.markdown(get_global_styles(), unsafe_allow_html=True)

# Additional home-specific styles
st.markdown("""
<style>
/* Huge button for LOG WORKOUT (primary action) */
.huge-button {
    padding: 0.5rem 0;
}

.huge-button > div > div > div > button {
    min-height: 56px !important;
    font-size: 1.125rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    border-radius: 12px !important;
    background: var(--color-accent-gradient) !important;
    border: none !important;
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

/* X button styling for recent activity - match expander height */
button:has(p:contains("❌")) {
    height: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
    padding: 0 !important;
    font-size: 24px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
}

/* Desktop optimizations */
@media (min-width: 769px) {
    .huge-button > div > div > div > button {
        min-height: 48px !important;
    }
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

    if st.button("📅 View History", key="sidebar_history", use_container_width=True):
        st.switch_page("pages/3_History.py")

    if st.button("📊 View Progress", key="sidebar_progress", use_container_width=True):
        st.switch_page("pages/4_Progress.py")

    if st.button("🗑️ View Trash", key="sidebar_trash", use_container_width=True):
        st.switch_page("pages/5_Trash.py")

    st.divider()

    # Quick stats
    st.subheader("Stats")

    try:
        from src.data import get_workout_count
        workouts_last_7 = get_workout_count(7)
        workouts_last_30 = get_workout_count(30)

        st.metric("Last 7 Days", workouts_last_7)
        st.metric("Last 30 Days", workouts_last_30)

        # Workout streak
        from datetime import date, timedelta
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
    st.caption("Version 1.0.0")

# ============================================================================
# Header
# ============================================================================

st.title("🏋️ GYM BRO")
st.caption("Your AI Fitness Coach")

# ============================================================================
# Weekly Split Status (Priority Display)
# ============================================================================

st.header("📊 This Week's Progress")

try:
    split_status = get_weekly_split_status.invoke({})

    # Create two columns for mobile-friendly layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Completed This Week")

        # Display each workout type with progress
        for workout_type in ['Push', 'Pull', 'Legs', 'Upper', 'Lower']:
            completed = split_status.get('completed', {}).get(workout_type, 0)
            target = split_status.get('targets', {}).get(workout_type, 0)

            if target > 0:  # Only show types that have targets
                if completed >= target:
                    icon = "✅"
                    delta_color = "normal"
                elif completed > 0:
                    icon = "⏳"
                    delta_color = "normal"
                else:
                    icon = "❌"
                    delta_color = "inverse"

                st.metric(
                    f"{icon} {workout_type}",
                    f"{completed}/{target}",
                    delta=f"{completed - target}" if completed != target else None,
                    delta_color=delta_color
                )

    with col2:
        st.subheader("🎯 Next Up")
        next_workout = split_status.get('next_suggested', 'Unknown')
        st.info(f"**{next_workout}**")

        days_left = split_status.get('days_left_in_week', 7)
        st.caption(f"{days_left} days left this week")

    # Supplementary Work Status
    st.divider()
    st.subheader("Supplementary Work")

    abs_status = split_status.get('supplementary', {}).get('abs', {})
    abs_count = abs_status.get('count', 0)
    abs_target = abs_status.get('target', 2)

    if abs_count >= abs_target:
        icon = "✅"
        delta_color = "normal"
    elif abs_count > 0:
        icon = "⏳"
        delta_color = "normal"
    else:
        icon = "❌"
        delta_color = "inverse"

    st.metric(
        f"{icon} Abs",
        f"{abs_count}/{abs_target}",
        delta=f"{abs_count - abs_target}" if abs_count != abs_target else None,
        delta_color=delta_color
    )

except Exception as e:
    st.error(f"Could not load weekly split status: {str(e)}")
    st.caption("You may need to log your first workout!")

# ============================================================================
# Quick Actions
# ============================================================================

st.header("Quick Actions")

# Huge LOG WORKOUT button (mobile-first priority)
st.markdown('<div class="huge-button">', unsafe_allow_html=True)
if st.button("🎙️ LOG WORKOUT", key="log_btn", type="primary"):
    st.switch_page("pages/1_Log_Workout.py")
st.markdown('</div>', unsafe_allow_html=True)

# Secondary actions
col1, col2 = st.columns(2)

with col1:
    if st.button("💬 Chat with Coach", key="chat_btn"):
        st.switch_page("pages/2_Chat.py")

with col2:
    if st.button("📊 View Progress", key="progress_btn"):
        st.switch_page("pages/4_Progress.py")

# ============================================================================
# Recent Activity
# ============================================================================

st.header("Recent Activity")

try:
    # Get workouts from last 30 days only (truly recent)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    recent_logs = get_logs_by_date_range(start_date, end_date)

    if not recent_logs:
        st.info("📭 No workouts logged in the last 30 days. Ready to start fresh?")
        st.caption("💡 Your workout history is still available in the History page!")
    else:
        # Show up to 5 most recent
        recent_logs = recent_logs[-5:] if len(recent_logs) > 5 else recent_logs
        recent_logs.reverse()  # Most recent first

        for log in recent_logs:
            # Create columns: expander on left, delete button on right
            col_expand, col_delete = st.columns([6, 1])

            with col_expand:
                # Create expander title with exercise preview
                exercises = log.get('exercises', [])
                workout_type = log.get('type', 'Unknown')
                workout_date = log.get('date', 'Unknown date')

                # Build title with first 2 exercises as preview
                exercise_preview = ''
                if exercises:
                    exercise_names = [ex.get('name', 'Unknown') for ex in exercises[:2]]
                    exercise_preview = f" - {', '.join(exercise_names)}"
                    if len(exercises) > 2:
                        exercise_preview += f", +{len(exercises)-2} more"

                expander_title = f"**{workout_type}** {workout_date}{exercise_preview}"

                # Add supplementary work badge
                supplementary = log.get('supplementary_work', [])
                if supplementary:
                    supp_badges = ' '.join([f"💪 {s.title()}" for s in supplementary])
                    expander_title += f" | {supp_badges}"

                with st.expander(expander_title):
                    # Phase 2: Show exercises with larger, more prominent text
                    if exercises:
                        for i, ex in enumerate(exercises, 1):
                            ex_name = ex.get('name', 'Unknown')
                            sets = ex.get('sets', [])
                            sets_count = len(sets)

                            # Exercise name - larger text
                            st.markdown(f'<div class="text-emphasis">{i}. {ex_name}</div>', unsafe_allow_html=True)
                            st.caption(f"{sets_count} sets")

                            # Show set details
                            for j, s in enumerate(sets, 1):
                                reps = s.get('reps', '?')
                                weight = s.get('weight_lbs')
                                if weight:
                                    st.caption(f"  Set {j}: {reps} reps @ {weight} lbs")
                                else:
                                    st.caption(f"  Set {j}: {reps} reps")

                            if i < len(exercises):
                                st.write("")  # Spacing between exercises

                    if log.get('notes'):
                        st.divider()
                        st.caption(f"*Notes: {log['notes']}*")

                    # View full workout button
                    st.divider()
                    if st.button("View Full Workout", key=f"view_{log.get('id')}", use_container_width=True):
                        st.session_state.expanded_log_id = log.get('id')
                        st.switch_page("pages/3_History.py")

            with col_delete:
                # Delete button aligned with expander header - no margin needed with CSS fix
                if st.button("❌", key=f"x_{log.get('id')}", help="Delete workout"):
                    show_delete_confirmation(log)

except Exception as e:
    st.error(f"Could not load recent activity: {str(e)}")

# ============================================================================
# Footer / About
# ============================================================================

st.divider()
st.caption("Built with Claude Code + LangGraph | Version 1.0.0")
