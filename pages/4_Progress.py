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
from src.ui.shared_components import render_sidebar, render_stat_card, render_empty_state
from src.ui.styles import get_global_styles
from src.ui.charts import (
    create_exercise_progression_chart,
    create_weekly_split_pie,
    create_volume_trends_chart,
    create_frequency_heatmap,
    get_unique_exercises,
    get_chart_config
)
from src.ui.insights import (
    generate_exercise_insights,
    generate_volume_insights,
    generate_consistency_insights,
    get_quick_stats
)

# Page configuration
st.set_page_config(
    page_title="Progress - Gym Bro",
    page_icon="📊",
    layout="centered"  # Changed from "wide" for better mobile experience
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
    render_sidebar(current_page="Progress")

# Apply global design system styles
st.markdown(get_global_styles(), unsafe_allow_html=True)

# ============================================================================
# Page Content
# ============================================================================

st.title("📊 Progress Tracking")
st.caption("Analyze your training trends and performance over time")

# ============================================================================
# Quick Stats Cards
# ============================================================================

stats = get_quick_stats()

# Show quick overview if user has data
if stats['total_workouts'] > 0:
    st.info(f"📈 You've logged **{stats['total_workouts']} workout{'s' if stats['total_workouts'] != 1 else ''}** total. Track your progress with personalized insights below.")

if stats['total_workouts'] > 0:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Workouts", stats['total_workouts'])

    with col2:
        streak_label = "Current Streak"
        if stats['current_streak'] > 0:
            st.metric(streak_label, f"{stats['current_streak']} days", delta="🔥")
        else:
            st.metric(streak_label, "0 days")

    with col3:
        st.metric("This Month", stats['this_month'])

    st.divider()
else:
    render_empty_state(
        icon="🏋️",
        title="No Workout Data Yet",
        message="Start your fitness journey by logging your first workout!",
        action_text="Log Workout →",
        action_page="pages/1_Log_Workout.py",
        size="large"
    )
    st.stop()  # Don't show charts if no data

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
            ["30d", "60d", "90d", "6mo", "1yr", "All"],
            index=2 if time_range_used != 0 else 5,  # Default: 90 days, or All Time if we fell back
            help="Select time period for analysis"
        )

    # Convert time range to days
    range_map = {
        "30d": 30,
        "60d": 60,
        "90d": 90,
        "6mo": 180,
        "1yr": 365,
        "All": 0  # 0 = all time
    }
    days = range_map[time_range]

    st.divider()

    # ========================================================================
    # Exercise Progression Chart with Smart Insights
    # ========================================================================

    st.subheader("💪 Exercise Progression")
    st.caption("Track strength gains over time with your selected exercise")

    # Generate smart insights for this exercise
    exercise_insights = generate_exercise_insights(selected_exercise, days)

    if not exercise_insights['has_data']:
        # Data quality warning
        st.warning(f"⚠️ Insufficient data: Only {exercise_insights['data_points']} workout(s) with {selected_exercise}.")
        st.info(f"📝 Log {exercise_insights['needed']} more workout(s) with {selected_exercise} to see progression trends")

        render_empty_state(
            icon="📊",
            title=f"Not Enough Data for {selected_exercise}",
            message=f"You need at least 3 workouts to see meaningful trends. You have {exercise_insights['data_points']}.",
            action_text="Log Workout →",
            action_page="pages/1_Log_Workout.py"
        )
    else:
        # Show data quality badge
        quality_badges = {
            'low': ("🟡", "Limited data - trends may not be accurate"),
            'moderate': ("🟢", "Moderate data quality"),
            'good': ("✅", "Excellent data quality")
        }
        badge_icon, badge_text = quality_badges.get(exercise_insights['quality'], ("", ""))
        st.caption(f"{badge_icon} {badge_text} ({exercise_insights['data_points']} data points)")

        # Show the chart (mobile-optimized by default for better phone experience)
        st.plotly_chart(
            create_exercise_progression_chart(selected_exercise, days, mobile=True),
            use_container_width=True,
            config=get_chart_config(mobile_optimized=True),
            key="exercise_progression"
        )

        # Display personalized insights
        if exercise_insights['insights']:
            insight_count = len(exercise_insights['insights'])
            rec_count = len(exercise_insights.get('recommendations', []))
            total_count = insight_count + rec_count

            with st.expander(f"💡 AI Insights ({total_count} tip{'s' if total_count != 1 else ''}) - Tap to view", expanded=False):
                for insight in exercise_insights['insights']:
                    st.markdown(insight)

                if exercise_insights['recommendations']:
                    st.markdown("**Recommendations:**")
                    for rec in exercise_insights['recommendations']:
                        st.markdown(f"- {rec}")

    st.divider()

    # ========================================================================
    # Volume Trends with Smart Insights
    # ========================================================================

    st.subheader("📈 Training Volume Trends")
    st.caption("Total weight × reps per week - key indicator of progressive overload")

    volume_insights = generate_volume_insights(days)

    if volume_insights['has_data']:
        st.plotly_chart(
            create_volume_trends_chart(days, mobile=True),
            use_container_width=True,
            config=get_chart_config(mobile_optimized=True),
            key="volume_trends"
        )

        # Display volume insights
        if volume_insights['insights']:
            with st.expander("💡 Volume Analysis", expanded=False):
                for insight in volume_insights['insights']:
                    st.markdown(insight)

                if volume_insights['recommendations']:
                    st.markdown("**Recommendations:**")
                    for rec in volume_insights['recommendations']:
                        st.markdown(f"- {rec}")

    st.divider()

    # ========================================================================
    # Additional Charts (Progressive Disclosure)
    # ========================================================================

    with st.expander("📊 More Analytics (2 charts) - Tap to explore", expanded=False):
        st.markdown("### Weekly Split Balance")
        st.caption("See the balance of workout types this week")

        st.plotly_chart(
            create_weekly_split_pie(days=7, mobile=True),
            use_container_width=True,
            config=get_chart_config(mobile_optimized=True),
            key="weekly_split"
        )

        st.divider()

        st.markdown("### Workout Frequency Calendar")
        st.caption("Visual of your workout consistency over time")

        st.plotly_chart(
            create_frequency_heatmap(days, mobile=True),
            use_container_width=True,
            config=get_chart_config(mobile_optimized=True),
            key="frequency_heatmap"
        )

    # ========================================================================
    # Consistency Insights
    # ========================================================================

    st.divider()
    st.subheader("⚡ Consistency Insights")
    st.caption("How you're showing up for your training")

    consistency_insights = generate_consistency_insights(days)

    if consistency_insights['has_data']:
        # Combine insights into a single compact card
        insights_text = "\n\n".join([f"• {insight}" for insight in consistency_insights['insights']])
        st.info(insights_text)

        if consistency_insights['recommendations']:
            st.warning("**💪 Action Items:**")
            for rec in consistency_insights['recommendations']:
                st.markdown(f"- {rec}")
