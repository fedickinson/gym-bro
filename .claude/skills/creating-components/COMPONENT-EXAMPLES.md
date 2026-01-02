# Component Examples from Existing Pages

## Example 1: Weekly Split Status (from Home Page)

**File**: `/Users/franklindickinson/Projects/gym-bro/app.py`

```python
def display_weekly_split_status():
    """Display weekly split completion status."""
    from src.tools.recommend_tools import get_weekly_split_status

    status = get_weekly_split_status.invoke({})

    st.markdown("### This Week")

    # Metrics row
    cols = st.columns(len(status['targets']))
    for i, (workout_type, target) in enumerate(status['targets'].items()):
        completed = status['completed'].get(workout_type, 0)
        remaining = status['remaining'].get(workout_type, 0)

        with cols[i]:
            # Use design system for metric display
            metric_html = f"""
            <div class="stat-card">
                <div class="stat-label">{workout_type}</div>
                <div class="stat-value">{completed}/{target}</div>
                <div class="text-caption" style="color: var(--color-text-secondary);">
                    {remaining} left
                </div>
            </div>
            """
            st.markdown(metric_html, unsafe_allow_html=True)
```

---

## Example 2: Recent Activity List (from Home Page)

```python
def display_recent_activity():
    """Display recent workouts."""
    from src.data import get_all_logs

    logs = get_all_logs()[:5]  # Last 5 workouts

    st.markdown("### Recent Activity")

    for log in logs:
        # Use activity-item class from design system
        activity_html = f"""
        <div class="activity-item">
            <div class="activity-header">
                <span class="activity-title">{log['type']}</span>
                <span class="activity-date">{log['date']}</span>
            </div>
            <div class="text-small" style="color: var(--color-text-secondary);">
                {len(log['exercises'])} exercises • {_calculate_volume(log)} lbs volume
            </div>
        </div>
        """
        st.markdown(activity_html, unsafe_allow_html=True)

def _calculate_volume(log):
    """Calculate total volume for a workout."""
    total = 0
    for ex in log.get('exercises', []):
        for set_data in ex.get('sets', []):
            total += set_data.get('reps', 0) * set_data.get('weight_lbs', 0)
    return f"{int(total):,}"
```

---

## Example 3: Exercise Review Display (from Session Page)

**File**: `/Users/franklindickinson/Projects/gym-bro/pages/1_Log_Workout.py`

```python
def display_exercise_review(exercise):
    """Display exercise with sets in review mode."""

    # Exercise banner (design system class)
    st.markdown(f"""
    <div class="exercise-banner">
        {exercise['name']}
    </div>
    """, unsafe_allow_html=True)

    # Sets table
    for i, set_data in enumerate(exercise['sets'], 1):
        reps = set_data.get('reps', 0)
        weight = set_data.get('weight_lbs')
        rpe = set_data.get('rpe')

        # Set row with design system spacing
        set_html = f"""
        <div class="set-row">
            <div style="width: 60px;">
                <span class="text-caption" style="color: var(--color-text-secondary);">Set {i}</span>
            </div>
            <div style="flex: 1;">
                <span class="text-body">{reps} reps</span>
            </div>
            <div style="width: 100px;">
                <span class="text-body">{weight} lbs</span> if weight else "Bodyweight"
            </div>
        </div>
        """
        st.markdown(set_html, unsafe_allow_html=True)
```

---

## Example 4: Confirmation Dialog

```python
def show_delete_confirmation(workout_id: str):
    """Show delete confirmation dialog."""

    # Use design system colors for alert
    st.markdown(f"""
    <div style="
        background: var(--color-bg-secondary);
        border-left: 4px solid var(--color-error);
        padding: var(--space-4);
        margin: var(--space-4) 0;
        border-radius: 4px;
    ">
        <div class="text-emphasis" style="color: var(--color-error);">
            Delete Workout?
        </div>
        <div class="text-body" style="margin-top: var(--space-2); color: var(--color-text-secondary);">
            This will move the workout to trash (30-day recovery window).
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Delete", type="primary", use_container_width=True):
            from src.data import delete_log
            delete_log(workout_id)
            st.success("Workout moved to trash")
            st.rerun()
```

---

## Example 5: Progress Chart (from Progress Page)

**File**: `/Users/franklindickinson/Projects/gym-bro/pages/4_Progress.py`

```python
def display_exercise_progression_chart(exercise: str, days: int = 90):
    """Display progression chart for an exercise."""
    from src.data import get_exercise_history
    import plotly.graph_objects as go

    history = get_exercise_history(exercise, days)

    if not history:
        st.info(f"No data found for {exercise}")
        return

    # Extract data for chart
    dates = [h['date'] for h in history]
    max_weights = [max((s.get('weight_lbs', 0) for s in h['sets']), default=0) for h in history]

    # Create chart with design system colors
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=max_weights,
        mode='lines+markers',
        name=exercise,
        line=dict(color='#4CAF50', width=3),  # Primary color
        marker=dict(size=8)
    ))

    # Style chart with design system
    fig.update_layout(
        title=f"{exercise} Progression",
        xaxis_title="Date",
        yaxis_title="Weight (lbs)",
        plot_bgcolor='#0E1117',  # bg-primary
        paper_bgcolor='#0E1117',
        font=dict(color='#FFFFFF', size=14),  # text-primary
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)
```

---

## Example 6: Loading State

```python
def show_loading(message: str = "Loading..."):
    """Display loading indicator with design system."""

    loading_html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--space-8);
    ">
        <div class="text-body" style="color: var(--color-text-secondary);">
            {message}
        </div>
    </div>
    """
    st.markdown(loading_html, unsafe_allow_html=True)

# Usage with spinner
with st.spinner("Loading workout data..."):
    data = load_data()
    time.sleep(0.5)  # Brief pause for UX
```

---

## Example 7: Empty State

```python
def show_empty_state(message: str, action_text: str | None = None, action_callback=None):
    """Display empty state message."""

    empty_html = f"""
    <div style="
        text-align: center;
        padding: var(--space-10) var(--space-4);
        color: var(--color-text-secondary);
    ">
        <div class="text-h3" style="margin-bottom: var(--space-4);">
            {message}
        </div>
    </div>
    """
    st.markdown(empty_html, unsafe_allow_html=True)

    if action_text and action_callback:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(action_text, use_container_width=True):
                action_callback()

# Usage
if len(workouts) == 0:
    show_empty_state(
        "No workouts logged yet",
        "Log First Workout",
        lambda: st.switch_page("pages/1_Log_Workout.py")
    )
```

---

See [DESIGN-SYSTEM.md](DESIGN-SYSTEM.md) for complete token reference.
