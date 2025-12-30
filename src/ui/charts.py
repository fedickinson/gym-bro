"""
Chart Components for Progress Tracking.

Uses Plotly for interactive, dark-mode charts optimized for mobile and desktop.
"""

import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
from src.data import get_exercise_history, get_logs_by_date_range, get_all_logs
import pandas as pd


def create_exercise_progression_chart(exercise: str, days: int = 90) -> go.Figure:
    """
    Create a line chart showing weight progression for an exercise over time.

    Args:
        exercise: Exercise name (e.g., "Bench Press")
        days: Number of days to look back

    Returns:
        Plotly figure object
    """
    history = get_exercise_history(exercise, days)

    if not history:
        # Empty state
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data for {exercise} in the last {days} days",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#888")
        )
        fig.update_layout(
            template='plotly_dark',
            height=400,
            paper_bgcolor='#0E1117',
            plot_bgcolor='#1E1E1E'
        )
        return fig

    # Extract dates and max weights
    dates = [h['date'] for h in history]
    max_weights = [h['max_weight'] for h in history]

    # Create line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=max_weights,
        mode='lines+markers',
        name='Max Weight',
        line=dict(color='#4CAF50', width=3),
        marker=dict(
            size=10,
            color='#4CAF50',
            line=dict(color='white', width=1)
        ),
        hovertemplate='<b>%{x}</b><br>Max Weight: %{y} lbs<extra></extra>'
    ))

    # Calculate trend
    if len(max_weights) > 1:
        improvement = max_weights[-1] - max_weights[0]
        improvement_pct = (improvement / max_weights[0] * 100) if max_weights[0] > 0 else 0

        # Add trend annotation
        fig.add_annotation(
            text=f"Trend: {improvement:+.1f} lbs ({improvement_pct:+.1f}%)",
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            showarrow=False,
            font=dict(size=12, color='#4CAF50' if improvement >= 0 else '#e74c3c'),
            align="left",
            bgcolor='rgba(30,30,30,0.8)',
            borderpad=4
        )

    fig.update_layout(
        title=f"{exercise} Progression",
        xaxis_title="Date",
        yaxis_title="Weight (lbs)",
        template='plotly_dark',
        height=400,
        hovermode='x unified',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#1E1E1E',
        font=dict(color='#FAFAFA'),
        margin=dict(l=40, r=20, t=60, b=40)
    )

    return fig


def create_weekly_split_pie(days: int = 7) -> go.Figure:
    """
    Create a pie chart showing workout type distribution for the current week.

    Args:
        days: Number of days to look back (default: 7 for current week)

    Returns:
        Plotly figure object
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    logs = get_logs_by_date_range(week_start, today)

    # Count workouts by type
    counts = {}
    for log in logs:
        workout_type = log.get('type', 'Other')
        counts[workout_type] = counts.get(workout_type, 0) + 1

    if not counts:
        # Empty state
        fig = go.Figure()
        fig.add_annotation(
            text="No workouts this week yet",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#888")
        )
        fig.update_layout(
            template='plotly_dark',
            height=400,
            paper_bgcolor='#0E1117',
            plot_bgcolor='#1E1E1E'
        )
        return fig

    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=list(counts.keys()),
        values=list(counts.values()),
        hole=0.3,  # Donut chart
        marker=dict(
            colors=['#4CAF50', '#2196F3', '#FFC107', '#FF5722', '#9C27B0'],
            line=dict(color='#0E1117', width=2)
        ),
        textinfo='label+percent',
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>%{label}</b><br>%{value} workouts<br>%{percent}<extra></extra>'
    )])

    fig.update_layout(
        title="This Week's Workout Split",
        template='plotly_dark',
        height=400,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#1E1E1E',
        font=dict(color='#FAFAFA'),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    return fig


def create_volume_trends_chart(days: int = 90) -> go.Figure:
    """
    Create a bar chart showing total training volume (weight × reps) per week.

    Args:
        days: Number of days to look back (0 = all time)

    Returns:
        Plotly figure object
    """
    if days == 0:
        # All time - get all logs
        logs = get_all_logs()
    else:
        # Specific time range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        logs = get_logs_by_date_range(start_date, end_date)

    # Calculate weekly volume
    weekly_volume = {}
    for log in logs:
        try:
            log_date = date.fromisoformat(log['date'])
        except (ValueError, KeyError):
            continue

        # Get week start (Monday)
        week_start = log_date - timedelta(days=log_date.weekday())
        week_key = week_start.isoformat()

        # Calculate volume for this workout
        volume = 0
        for ex in log.get('exercises', []):
            for s in ex.get('sets', []):
                reps = s.get('reps', 0)
                weight = s.get('weight_lbs', 0)
                if reps and weight:
                    volume += reps * weight

        weekly_volume[week_key] = weekly_volume.get(week_key, 0) + volume

    if not weekly_volume:
        # Empty state
        fig = go.Figure()
        fig.add_annotation(
            text=f"No volume data in the last {days} days",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#888")
        )
        fig.update_layout(
            template='plotly_dark',
            height=400,
            paper_bgcolor='#0E1117',
            plot_bgcolor='#1E1E1E'
        )
        return fig

    # Create DataFrame
    df = pd.DataFrame({
        'Week': list(weekly_volume.keys()),
        'Volume': list(weekly_volume.values())
    })
    df = df.sort_values('Week')

    # Create bar chart
    fig = go.Figure(data=[go.Bar(
        x=df['Week'],
        y=df['Volume'],
        marker=dict(
            color='#4CAF50',
            line=dict(color='#45a049', width=1)
        ),
        hovertemplate='Week of %{x}<br>Volume: %{y:,.0f} lbs<extra></extra>'
    )])

    # Calculate average
    avg_volume = df['Volume'].mean()
    fig.add_hline(
        y=avg_volume,
        line_dash="dash",
        line_color="#FFC107",
        annotation_text=f"Average: {avg_volume:,.0f} lbs",
        annotation_position="top left"
    )

    fig.update_layout(
        title="Weekly Training Volume",
        xaxis_title="Week",
        yaxis_title="Total Volume (lbs)",
        template='plotly_dark',
        height=400,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#1E1E1E',
        font=dict(color='#FAFAFA'),
        hovermode='x unified',
        margin=dict(l=60, r=20, t=60, b=40)
    )

    return fig


def create_frequency_heatmap(days: int = 90) -> go.Figure:
    """
    Create a calendar heatmap showing workout frequency over time.

    Args:
        days: Number of days to look back (0 = all time)

    Returns:
        Plotly figure object
    """
    if days == 0:
        # All time - get all logs
        logs = get_all_logs()
        # For all-time, use actual date range from data
        if logs:
            all_dates = [log.get('date') for log in logs if log.get('date')]
            if all_dates:
                start_date = date.fromisoformat(min(all_dates))
                end_date = date.today()
                days = (end_date - start_date).days
            else:
                start_date = date.today()
                end_date = date.today()
                days = 0
        else:
            start_date = date.today()
            end_date = date.today()
            days = 0
    else:
        # Specific time range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        logs = get_logs_by_date_range(start_date, end_date)

    # Create date -> count mapping
    date_counts = {}
    for log in logs:
        log_date = log.get('date')
        if log_date:
            date_counts[log_date] = date_counts.get(log_date, 0) + 1

    # Create full date range
    dates = []
    counts = []
    for i in range(days + 1):
        d = start_date + timedelta(days=i)
        date_str = d.isoformat()
        dates.append(date_str)
        counts.append(date_counts.get(date_str, 0))

    # Reshape into weeks (7 days per row)
    weeks = []
    week_labels = []
    current_week = []
    current_week_dates = []

    for i, (d, c) in enumerate(zip(dates, counts)):
        current_week.append(c)
        current_week_dates.append(d)

        # Every 7 days or end of data
        if (i + 1) % 7 == 0 or i == len(dates) - 1:
            # Pad if necessary
            while len(current_week) < 7:
                current_week.append(0)
                current_week_dates.append('')

            weeks.append(current_week)
            week_labels.append(current_week_dates[0])  # Label with Monday
            current_week = []
            current_week_dates = []

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=weeks,
        y=week_labels,
        x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        colorscale=[
            [0, '#1E1E1E'],      # No workout
            [0.33, '#2E7D32'],   # 1 workout
            [0.66, '#4CAF50'],   # 2 workouts
            [1, '#81C784']       # 3+ workouts
        ],
        showscale=True,
        colorbar=dict(
            title="Workouts",
            tickmode="linear",
            tick0=0,
            dtick=1
        ),
        hovertemplate='%{y}<br>%{x}<br>Workouts: %{z}<extra></extra>'
    ))

    fig.update_layout(
        title="Workout Frequency Calendar",
        template='plotly_dark',
        height=300,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#1E1E1E',
        font=dict(color='#FAFAFA'),
        margin=dict(l=100, r=20, t=60, b=40),
        yaxis=dict(autorange='reversed')  # Most recent at top
    )

    return fig


def get_unique_exercises(days: int = 90) -> list[str]:
    """
    Get a list of unique exercises from recent workouts.

    Args:
        days: Number of days to look back (0 = all time)

    Returns:
        Sorted list of unique exercise names
    """
    if days == 0:
        # All time - get all logs
        logs = get_all_logs()
    else:
        # Specific time range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        logs = get_logs_by_date_range(start_date, end_date)

    exercises = set()
    for log in logs:
        for ex in log.get('exercises', []):
            name = ex.get('name')
            if name:
                exercises.add(name)

    return sorted(list(exercises))
