"""
Chart Components for Progress Tracking.

Uses Plotly for interactive, dark-mode charts optimized for mobile and desktop.
"""

import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
from src.data import get_exercise_history, get_logs_by_date_range, get_all_logs
import pandas as pd

# Design System Colors (matching src/ui/styles.py)
# Plotly doesn't support CSS variables, so we define constants here
COLORS = {
    'primary': '#4CAF50',
    'primary_dark': '#45a049',
    'accent': '#66BB6A',
    'warning': '#FFC107',
    'error': '#F44336',
    'info': '#2196F3',
    'bg_primary': '#0E1117',
    'bg_secondary': '#1E1E1E',
    'bg_tertiary': '#2A2A2A',
    'text_primary': '#FAFAFA',
    'text_secondary': '#B0B0B0',
    'border': '#3A3A3A',
    'restore': '#2e7d32',
    'restore_light': '#81C784',
}

# Responsive chart configuration
def get_chart_config(mobile_optimized: bool = True) -> dict:
    """
    Get Plotly configuration for mobile or desktop.

    Args:
        mobile_optimized: If True, hide toolbar and optimize for touch

    Returns:
        dict: Plotly config object
    """
    if mobile_optimized:
        return {
            'displayModeBar': False,  # Hide toolbar on mobile
            'doubleClick': 'reset',
            'scrollZoom': False,
            'responsive': True
        }
    else:
        return {
            'displayModeBar': True,
            'displaylogo': False,
            'responsive': True
        }

def get_mobile_layout_settings() -> dict:
    """
    Get mobile-optimized layout settings for Plotly charts.

    Mobile optimizations:
    - Reduced height (250px) for less scrolling
    - Tighter margins to maximize chart area
    - Smaller font size for better space utilization
    - Compact legends with horizontal orientation

    Returns:
        dict: Layout settings for mobile
    """
    return {
        'font': {'size': 8, 'color': COLORS['text_primary']},
        'margin': {'l': 20, 'r': 5, 't': 40, 'b': 30},
        'height': 250,  # Reduced from 300px for less scrolling
        'legend': {
            'orientation': 'h',  # Horizontal legend
            'yanchor': 'bottom',
            'y': -0.3,
            'xanchor': 'center',
            'x': 0.5,
            'font': {'size': 8}
        }
    }

def get_desktop_layout_settings() -> dict:
    """
    Get desktop-optimized layout settings for Plotly charts.

    Returns:
        dict: Layout settings for desktop
    """
    return {
        'font': {'size': 12, 'color': COLORS['text_primary']},
        'margin': {'l': 40, 'r': 20, 't': 60, 'b': 40},
        'height': 400,
    }


def create_exercise_progression_chart(exercise: str, days: int = 90, mobile: bool = False) -> go.Figure:
    """
    Create a line chart showing weight progression for an exercise over time.

    Args:
        exercise: Exercise name (e.g., "Bench Press")
        days: Number of days to look back
        mobile: If True, optimize for mobile viewing

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
            font=dict(size=14, color=COLORS['text_secondary'])
        )
        fig.update_layout(
            template='plotly_dark',
            height=400,
            paper_bgcolor=COLORS['bg_primary'],
            plot_bgcolor=COLORS['bg_secondary']
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
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(
            size=10,
            color=COLORS['primary'],
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
            font=dict(size=12, color=COLORS['primary'] if improvement >= 0 else COLORS['error']),
            align="left",
            bgcolor='rgba(30,30,30,0.8)',
            borderpad=4
        )

    # Get responsive settings
    layout_settings = get_mobile_layout_settings() if mobile else get_desktop_layout_settings()

    fig.update_layout(
        title=f"{exercise} Progression",
        xaxis_title="" if mobile else "Date",  # Hide axis title on mobile to save space
        yaxis_title="lbs" if mobile else "Weight (lbs)",  # Shorter label on mobile
        template='plotly_dark',
        hovermode='x unified',
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_secondary'],
        **layout_settings
    )

    return fig


def create_weekly_split_pie(days: int = 7, mobile: bool = False) -> go.Figure:
    """
    Create a pie chart showing workout type distribution for the current week.

    Args:
        days: Number of days to look back (default: 7 for current week)
        mobile: If True, optimize for mobile viewing

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
            font=dict(size=14, color=COLORS['text_secondary'])
        )
        fig.update_layout(
            template='plotly_dark',
            height=400,
            paper_bgcolor=COLORS['bg_primary'],
            plot_bgcolor=COLORS['bg_secondary']
        )
        return fig

    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=list(counts.keys()),
        values=list(counts.values()),
        hole=0.3,  # Donut chart
        marker=dict(
            colors=[COLORS['primary'], COLORS['info'], COLORS['warning'], '#FF5722', '#9C27B0'],
            line=dict(color=COLORS['bg_primary'], width=2)
        ),
        textinfo='label+percent',
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>%{label}</b><br>%{value} workouts<br>%{percent}<extra></extra>'
    )])

    # Get responsive settings
    layout_settings = get_mobile_layout_settings() if mobile else get_desktop_layout_settings()

    fig.update_layout(
        title="This Week's Workout Split",
        template='plotly_dark',
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_secondary'],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2 if not mobile else -0.15,
            xanchor="center",
            x=0.5
        ),
        **layout_settings
    )

    return fig


def create_volume_trends_chart(days: int = 90, mobile: bool = False) -> go.Figure:
    """
    Create a bar chart showing total training volume (weight × reps) per week.

    Args:
        days: Number of days to look back (0 = all time)
        mobile: If True, optimize for mobile viewing

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
            font=dict(size=14, color=COLORS['text_secondary'])
        )
        fig.update_layout(
            template='plotly_dark',
            height=400,
            paper_bgcolor=COLORS['bg_primary'],
            plot_bgcolor=COLORS['bg_secondary']
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
            color=COLORS['primary'],
            line=dict(color=COLORS['primary_dark'], width=1)
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

    # Get responsive settings
    layout_settings = get_mobile_layout_settings() if mobile else get_desktop_layout_settings()

    fig.update_layout(
        title="Weekly Training Volume",
        xaxis_title="" if mobile else "Week",  # Hide axis title on mobile
        yaxis_title="lbs" if mobile else "Total Volume (lbs)",  # Shorter label on mobile
        template='plotly_dark',
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_secondary'],
        hovermode='x unified',
        **layout_settings
    )

    return fig


def create_frequency_heatmap(days: int = 90, mobile: bool = False) -> go.Figure:
    """
    Create a calendar heatmap showing workout frequency over time.

    Args:
        days: Number of days to look back (0 = all time)
        mobile: If True, optimize for mobile viewing

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
            [0, COLORS['bg_secondary']],      # No workout
            [0.33, COLORS['restore']],   # 1 workout
            [0.66, COLORS['primary']],   # 2 workouts
            [1, COLORS['restore_light']]       # 3+ workouts
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

    # Use compact layout for heatmap (works well on both mobile and desktop)
    fig.update_layout(
        title="Workout Frequency Calendar",
        template='plotly_dark',
        height=280 if mobile else 300,
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_secondary'],
        font=dict(size=9 if mobile else 10, color=COLORS['text_primary']),
        margin=dict(l=80 if mobile else 100, r=10 if mobile else 20, t=40 if mobile else 60, b=30 if mobile else 40),
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
