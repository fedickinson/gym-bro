"""
Gym Bro - Mobile-First AI Fitness Coach

Main home page with weekly split status and quick actions.
"""

import streamlit as st
from src.ui.session import init_session_state
from src.ui.navigation import render_bottom_nav
from src.tools.recommend_tools import get_weekly_split_status
from src.data import get_all_logs

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

# Render bottom navigation
st.session_state.current_page = 'Home'
render_bottom_nav('Home')

# ============================================================================
# Custom CSS for Mobile-First Design
# ============================================================================

st.markdown("""
<style>
/* Desktop optimizations (default) */
@media (min-width: 769px) {
    /* Hide bottom nav on desktop (use sidebar instead) */
    .bottom-nav {
        display: none !important;
    }

    /* Better spacing for desktop */
    .main .block-container {
        padding: 2rem 2rem !important;
        max-width: 1200px !important;
    }

    /* Slightly smaller buttons on desktop */
    .huge-button > div > div > div > button {
        height: 80px !important;
    }
}

/* Mobile optimizations */
@media (max-width: 768px) {
    /* Reduce padding on mobile */
    .main .block-container {
        padding: 1rem 1rem 5rem 1rem !important;
    }

    /* Larger text for readability */
    .main {
        font-size: 16px !important;
    }

    /* Hide sidebar on mobile (will use bottom nav) */
    section[data-testid="stSidebar"] {
        display: none;
    }
}

/* Huge button for primary actions */
.huge-button {
    padding: 0.5rem 0;
}

.huge-button > div > div > div > button {
    height: 100px !important;
    font-size: 24px !important;
    font-weight: bold !important;
    width: 100% !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
    border: none !important;
}

/* Touch-friendly buttons */
.stButton > button {
    min-height: 50px !important;
    font-size: 16px !important;
    width: 100% !important;
}

/* Metrics styling */
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    color: #4CAF50 !important;
}

/* Card styling */
.workout-card {
    background: #1E1E1E;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    border: 1px solid #333;
}

/* Desktop improvements */
@media (min-width: 769px) {
    /* Better header sizing */
    h1 {
        font-size: 2.5rem !important;
    }

    h2 {
        font-size: 1.8rem !important;
    }

    /* Better metric display */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
    }
}
</style>
""", unsafe_allow_html=True)

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
    all_logs = get_all_logs()

    if not all_logs:
        st.info("No workouts logged yet. Tap **LOG WORKOUT** above to get started!")
    else:
        # Show last 5 workouts
        recent_logs = all_logs[-5:]
        recent_logs.reverse()  # Most recent first

        for log in recent_logs:
            with st.expander(f"{log.get('type', 'Unknown')} - {log.get('date', 'Unknown date')}"):
                exercises = log.get('exercises', [])

                if exercises:
                    st.write("**Exercises:**")
                    for ex in exercises:
                        sets_count = len(ex.get('sets', []))
                        st.write(f"• {ex.get('name', 'Unknown')}: {sets_count} sets")

                if log.get('notes'):
                    st.caption(f"*Notes: {log['notes']}*")

                # Quick action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View Full Workout", key=f"view_{log.get('id')}"):
                        st.session_state.expanded_log_id = log.get('id')
                        st.switch_page("pages/3_History.py")
                with col2:
                    if st.button("Delete", key=f"delete_{log.get('id')}"):
                        # TODO: Implement delete confirmation
                        st.warning("Delete functionality coming soon!")

except Exception as e:
    st.error(f"Could not load recent activity: {str(e)}")

# ============================================================================
# Footer / About
# ============================================================================

st.divider()
st.caption("Built with Claude Code + LangGraph | Version 1.0.0")
