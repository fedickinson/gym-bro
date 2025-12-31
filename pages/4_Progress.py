"""
Progress Page - Charts and analytics for desktop/home analysis.

Displays 4 chart types:
1. Exercise progression (line chart)
2. Weekly split balance (pie chart)
3. Volume trends (bar chart)
4. Workout frequency (heatmap)
"""

import streamlit as st
from src.ui.session import init_session_state
from src.ui.navigation import render_bottom_nav
from src.ui.styles import get_global_styles
from src.ui.charts import (
    create_exercise_progression_chart,
    create_weekly_split_pie,
    create_volume_trends_chart,
    create_frequency_heatmap,
    get_unique_exercises
)

# Page configuration
st.set_page_config(
    page_title="Progress - Gym Bro",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
init_session_state()

# Render bottom navigation
st.session_state.current_page = 'Progress'
render_bottom_nav('Progress')

# ============================================================================
# Sidebar Navigation & Stats
# ============================================================================

with st.sidebar:
    st.title("🏋️ Gym Bro")
    st.caption("AI Fitness Coach")

    st.divider()

    # Quick navigation
    st.subheader("Quick Links")

    if st.button("🏠 Home", key="sidebar_prog_home", use_container_width=True):
        st.switch_page("app.py")

    if st.button("📅 View History", key="sidebar_prog_history", use_container_width=True):
        st.switch_page("pages/3_History.py")

    if st.button("🗑️ View Trash", key="sidebar_prog_trash", use_container_width=True):
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
    st.caption("Version 1.0.0")

# Apply global design system styles
st.markdown(get_global_styles(), unsafe_allow_html=True)

# ============================================================================
# Page Content
# ============================================================================

st.title("📊 Progress Tracking")
st.caption("Analyze your training trends and performance over time")

# ============================================================================
# Exercise Selector
# ============================================================================

# Get unique exercises from recent workouts, with fallback to all-time
exercises = get_unique_exercises(days=180)
time_range_used = 180  # Track which range we're actually using

if not exercises:
    # No recent data, try all-time
    st.info("📅 No workout data in the last 6 months. Showing all-time data instead.")
    exercises = get_unique_exercises(days=0)  # 0 = all time
    time_range_used = 0

if not exercises:
    st.warning("No workout data found. Log some workouts to see your progress!")
else:
    # Exercise selector for progression chart
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_exercise = st.selectbox(
            "Select Exercise to Track",
            exercises,
            index=0
        )

    with col2:
        time_range = st.selectbox(
            "Time Range",
            ["30 days", "60 days", "90 days", "6 months", "1 year", "All Time"],
            index=2 if time_range_used != 0 else 5  # Default: 90 days, or All Time if we fell back
        )

    # Convert time range to days
    range_map = {
        "30 days": 30,
        "60 days": 60,
        "90 days": 90,
        "6 months": 180,
        "1 year": 365,
        "All Time": 0  # 0 = all time
    }
    days = range_map[time_range]

    st.divider()

    # ========================================================================
    # Chart Layout
    # ========================================================================

    # Check if mobile (simplified detection)
    # On mobile, we'll stack charts vertically
    # On desktop, we'll use a 2x2 grid

    # Row 1: Exercise Progression (full width)
    st.plotly_chart(
        create_exercise_progression_chart(selected_exercise, days),
        use_container_width=True,
        key="exercise_progression"
    )

    st.divider()

    # Row 2: Weekly Split + Volume Trends (side by side on desktop)
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            create_weekly_split_pie(days=7),
            use_container_width=True,
            key="weekly_split"
        )

    with col2:
        st.plotly_chart(
            create_volume_trends_chart(days),
            use_container_width=True,
            key="volume_trends"
        )

    st.divider()

    # Row 3: Frequency Heatmap (full width)
    st.plotly_chart(
        create_frequency_heatmap(days),
        use_container_width=True,
        key="frequency_heatmap"
    )

    # ========================================================================
    # Insights Section
    # ========================================================================

    st.divider()
    st.subheader("💡 Insights")

    with st.expander("How to Use These Charts", expanded=False):
        st.write("""
        **Exercise Progression:**
        - Track your max weight over time for any exercise
        - Look for upward trends indicating strength gains
        - Plateaus suggest it might be time to adjust your program

        **Weekly Split:**
        - See the balance of workout types this week
        - Ensure you're hitting your Push/Pull/Legs targets
        - A balanced split prevents overtraining and injuries

        **Volume Trends:**
        - Total weight × reps per week
        - Rising volume = progressive overload
        - Dips might indicate recovery weeks or time off

        **Frequency Heatmap:**
        - Visual of your workout consistency
        - Green = active training days
        - Patterns help identify your training rhythm
        """)
