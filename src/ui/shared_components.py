"""
Shared UI Components for Gym Bro.

Provides reusable components to ensure visual consistency across all pages:
- Sidebar stats and navigation
- Page headers
- Stat cards
- Empty states
- Progress indicators

All components follow the mobile-first design system from styles.py.
"""

import streamlit as st
from datetime import date, timedelta
from typing import Optional, Callable


# ============================================================================
# Sidebar Components
# ============================================================================

def render_sidebar_stats():
    """
    Render standardized sidebar stats section.

    Shows:
    - Last 7 Days workout count
    - Last 30 Days workout count
    - Current Streak (consecutive days)

    Identical across all pages - single source of truth.
    """
    st.subheader("Stats")

    try:
        from src.data import get_workout_count, get_all_logs

        workouts_last_7 = get_workout_count(7)
        workouts_last_30 = get_workout_count(30)

        st.metric("Last 7 Days", workouts_last_7)
        st.metric("Last 30 Days", workouts_last_30)

        # Workout streak calculation
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


def render_sidebar_navigation(current_page: str):
    """
    Render standardized sidebar navigation section.

    Args:
        current_page: Name of current page ('Home', 'Log', 'Chat', 'History', 'Progress', 'Trash')
                     Used to hide the current page's button (prevent redundant navigation)

    Navigation Links:
    - Home (🏠)
    - History (📅)
    - Progress (📊)
    - Trash (🗑️)

    Note: Log and Chat intentionally omitted from sidebar (use bottom nav on mobile)
    """
    st.subheader("Quick Links")

    # Home button (hidden when on home page)
    if current_page != 'Home':
        if st.button("🏠 Home", key=f"sidebar_{current_page.lower()}_home", use_container_width=True):
            st.switch_page("app.py")

    # History button (hidden when on history page)
    if current_page != 'History':
        if st.button("📅 View History", key=f"sidebar_{current_page.lower()}_history", use_container_width=True):
            st.switch_page("pages/3_History.py")

    # Progress button (hidden when on progress page)
    if current_page != 'Progress':
        if st.button("📊 View Progress", key=f"sidebar_{current_page.lower()}_progress", use_container_width=True):
            st.switch_page("pages/4_Progress.py")

    # Trash button (always shown - not a primary page)
    if st.button("🗑️ View Trash", key=f"sidebar_{current_page.lower()}_trash", use_container_width=True):
        st.switch_page("pages/5_Trash.py")


def render_sidebar_header():
    """
    Render standardized sidebar header section.

    Shows:
    - App title
    - Tagline
    - Divider
    """
    st.title("🏋️ Gym Bro")
    st.caption("AI Fitness Coach")
    st.divider()


def render_sidebar_footer(show_version: bool = False):
    """
    Render standardized sidebar footer section.

    Args:
        show_version: Whether to show version number (typically only on home page)
    """
    st.divider()
    if show_version:
        st.caption("Version 1.0.0")


def render_sidebar(current_page: str, show_version: bool = False):
    """
    Render complete standardized sidebar for a page.

    Args:
        current_page: Name of current page for navigation context
        show_version: Whether to show version in footer (default False)

    Complete sidebar includes:
    - Header (title, caption)
    - Navigation (quick links)
    - Stats (7-day, 30-day, streak)
    - Footer (optional version)

    Usage:
        with st.sidebar:
            render_sidebar(current_page="Home", show_version=True)
    """
    render_sidebar_header()
    render_sidebar_navigation(current_page)
    st.divider()
    render_sidebar_stats()
    render_sidebar_footer(show_version)


# ============================================================================
# Page Header Components
# ============================================================================

def render_page_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None):
    """
    Render standardized page header.

    Args:
        title: Page title (e.g., "GYM BRO", "Chat with Your Coach")
        subtitle: Optional subtitle/tagline
        icon: Optional emoji icon (if not already in title)

    Mobile: Larger text, centered
    Desktop: Left-aligned, slightly smaller

    Example:
        render_page_header("💬 Chat with Your Coach", "Ask questions or get recommendations")
    """
    if icon and icon not in title:
        title = f"{icon} {title}"

    st.title(title)
    if subtitle:
        st.caption(subtitle)


# ============================================================================
# Stat Card Components
# ============================================================================

def render_stat_card(
    label: str,
    value: str,
    status: str = "neutral",
    sublabel: Optional[str] = None,
    icon: Optional[str] = None
):
    """
    Render standardized stat card component.

    Args:
        label: Main label (e.g., "Push", "Pull")
        value: Value to display (e.g., "1/1", "✓")
        status: Visual status ("success" | "warning" | "incomplete" | "neutral")
        sublabel: Optional secondary info
        icon: Optional emoji icon

    Status colors:
    - success: Green (#4CAF50)
    - warning: Yellow (#FFC107)
    - incomplete: Muted gray (#B0B0B0)
    - neutral: Default text color

    Example:
        render_stat_card("Push", "1/1", status="success", icon="✓")
    """
    # Determine color based on status
    status_colors = {
        "success": "var(--color-success)",
        "warning": "var(--color-warning)",
        "incomplete": "var(--color-text-secondary)",
        "neutral": "var(--color-text-primary)"
    }
    color = status_colors.get(status, status_colors["neutral"])

    # Build HTML
    icon_html = f'<span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>' if icon else ''
    sublabel_html = f'<div style="font-size: 0.875rem; color: var(--color-text-secondary); margin-top: 0.25rem;">{sublabel}</div>' if sublabel else ''

    st.markdown(f"""
    <div class="stat-card" style="
        background: var(--color-bg-secondary);
        padding: var(--space-4);
        border-radius: 12px;
        border-left: 4px solid {color};
        margin-bottom: var(--space-3);
    ">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 0.875rem; color: var(--color-text-secondary); margin-bottom: 0.25rem;">
                    {label}
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {color};">
                    {icon_html}{value}
                </div>
                {sublabel_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# Empty State Components
# ============================================================================

def render_empty_state(
    icon: str,
    title: str,
    message: str,
    action_text: Optional[str] = None,
    action_page: Optional[str] = None,
    size: str = "default"
):
    """
    Render standardized empty state component.

    Args:
        icon: Emoji icon (e.g., "📊", "🏋️", "📅")
        title: Empty state title
        message: Explanatory message
        action_text: Optional CTA button text (e.g., "Log Workout →")
        action_page: Optional page to navigate to when button clicked
        size: "small" | "default" | "large" (affects spacing and icon size)

    Size guide:
    - small: Inline empty state (e.g., no filter results) - compact
    - default: Section empty (e.g., no recent workouts) - medium
    - large: Page empty (e.g., no history at all) - spacious with large icon

    Mobile: Larger icons, more padding
    Desktop: Compact

    Example:
        render_empty_state(
            icon="📊",
            title="No data yet",
            message="Log some workouts to see your progress",
            action_text="Log Workout →",
            action_page="pages/1_Log_Workout.py",
            size="large"
        )
    """
    # Size configurations
    size_config = {
        "small": {"icon_size": "2rem", "padding": "var(--space-4)", "title_size": "1rem"},
        "default": {"icon_size": "3rem", "padding": "var(--space-6)", "title_size": "1.25rem"},
        "large": {"icon_size": "4rem", "padding": "var(--space-8)", "title_size": "1.5rem"}
    }
    config = size_config.get(size, size_config["default"])

    # Render empty state
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: {config['padding']};
        color: var(--color-text-secondary);
    ">
        <div style="font-size: {config['icon_size']}; margin-bottom: var(--space-3);">
            {icon}
        </div>
        <div style="font-size: {config['title_size']}; font-weight: 600; color: var(--color-text-primary); margin-bottom: var(--space-2);">
            {title}
        </div>
        <div style="font-size: 1rem;">
            {message}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Optional action button
    if action_text and action_page:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(action_text, use_container_width=True, type="primary"):
                st.switch_page(action_page)


# ============================================================================
# Progress Indicator Components
# ============================================================================

def render_workflow_progress(
    steps: list[str],
    current_step: int,
    show_labels: bool = True
):
    """
    Render horizontal step progress indicator for multi-step workflows.

    Args:
        steps: List of step names (e.g., ["Plan", "Exercise 1", "Exercise 2", "Review"])
        current_step: Current step index (0-based)
        show_labels: Show step names (False for very small mobile screens)

    Visual styles:
    - Completed steps: Green filled circle with checkmark
    - Current step: Large green outlined circle
    - Future steps: Gray outlined circle

    Mobile: Horizontal dots with current step highlighted
    Desktop: Full breadcrumb with labels

    Example:
        # For a 4-step workout flow
        steps = ["Plan", "Exercise 1", "Exercise 2", "Review"]
        render_workflow_progress(steps, current_step=1)  # Currently on Exercise 1

        Result:
        ✓ ━━━ ● ━━━ ○ ━━━ ○
        Step 2 of 4: Exercise 1
    """
    total_steps = len(steps)

    # Build step indicator HTML
    step_html = '<div style="display: flex; align-items: center; justify-content: center; margin-bottom: var(--space-3);">'

    for i, step in enumerate(steps):
        # Determine step state
        if i < current_step:
            # Completed step
            circle = '<span style="display: inline-block; width: 24px; height: 24px; border-radius: 50%; background: var(--color-primary-500); color: white; text-align: center; line-height: 24px; font-size: 14px;">✓</span>'
            color = "var(--color-primary-500)"
        elif i == current_step:
            # Current step
            circle = '<span style="display: inline-block; width: 32px; height: 32px; border-radius: 50%; border: 3px solid var(--color-primary-500); color: var(--color-primary-500); text-align: center; line-height: 26px; font-size: 16px; font-weight: 700;">●</span>'
            color = "var(--color-primary-500)"
        else:
            # Future step
            circle = '<span style="display: inline-block; width: 24px; height: 24px; border-radius: 50%; border: 2px solid var(--color-text-secondary); color: var(--color-text-secondary); text-align: center; line-height: 20px;">○</span>'
            color = "var(--color-text-secondary)"

        step_html += circle

        # Add connector line (except after last step)
        if i < total_steps - 1:
            connector_color = "var(--color-primary-500)" if i < current_step else "var(--color-border)"
            step_html += f'<span style="display: inline-block; width: 40px; height: 2px; background: {connector_color}; margin: 0 4px;"></span>'

    step_html += '</div>'

    # Render progress indicator
    st.markdown(step_html, unsafe_allow_html=True)

    # Step label
    step_label = f"Step {current_step + 1} of {total_steps}"
    if show_labels and current_step < total_steps:
        step_label += f": {steps[current_step]}"

    st.markdown(f"""
    <div style="text-align: center; color: var(--color-text-secondary); font-size: 0.875rem; margin-bottom: var(--space-4);">
        {step_label}
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# Skeleton Loading Components
# ============================================================================

def render_skeleton_card(count: int = 1):
    """
    Render skeleton placeholder for loading cards.

    Args:
        count: Number of skeleton cards to show

    Provides better perceived performance than spinners.
    Uses CSS animation for shimmer effect.

    Example:
        # While loading recent workouts
        render_skeleton_card(count=3)
    """
    skeleton_css = """
    <style>
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }

    .skeleton {
        background: linear-gradient(
            90deg,
            var(--color-bg-secondary) 0%,
            var(--color-bg-tertiary) 50%,
            var(--color-bg-secondary) 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite;
        border-radius: 12px;
    }
    </style>
    """

    st.markdown(skeleton_css, unsafe_allow_html=True)

    for _ in range(count):
        st.markdown("""
        <div class="skeleton" style="
            height: 100px;
            margin-bottom: var(--space-3);
        "></div>
        """, unsafe_allow_html=True)


def render_skeleton_list(items: int = 3):
    """
    Render skeleton placeholder for loading list items.

    Args:
        items: Number of skeleton list items to show

    Example:
        # While loading workout history
        render_skeleton_list(items=5)
    """
    skeleton_css = """
    <style>
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }

    .skeleton {
        background: linear-gradient(
            90deg,
            var(--color-bg-secondary) 0%,
            var(--color-bg-tertiary) 50%,
            var(--color-bg-secondary) 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite;
        border-radius: 8px;
    }
    </style>
    """

    st.markdown(skeleton_css, unsafe_allow_html=True)

    for _ in range(items):
        st.markdown("""
        <div style="margin-bottom: var(--space-4);">
            <div class="skeleton" style="height: 24px; width: 60%; margin-bottom: var(--space-2);"></div>
            <div class="skeleton" style="height: 16px; width: 80%;"></div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# Mobile-Responsive Layout Helpers
# ============================================================================

def action_button_row(button_configs: list[dict], key_prefix: str = "action_btn"):
    """
    Render a row of action buttons that stack vertically on mobile.

    Desktop: Buttons arranged horizontally in columns
    Mobile: Buttons stack vertically, full-width

    Args:
        button_configs: List of button config dicts, each containing:
            - label: Button text (required)
            - on_click: Callback function when clicked (optional)
            - type: "primary" | "secondary" (default: "secondary")
            - disabled: Whether button is disabled (default: False)
            - use_container_width: Whether to use full width (default: True)
        key_prefix: Prefix for button keys (to ensure uniqueness)

    Example:
        action_button_row([
            {"label": "30s", "on_click": lambda: set_timer(30)},
            {"label": "60s", "on_click": lambda: set_timer(60)},
            {"label": "90s", "on_click": lambda: set_timer(90)},
            {"label": "120s", "on_click": lambda: set_timer(120)}
        ], key_prefix="rest_timer")

    Returns:
        List of button click states (True if clicked, False otherwise)
    """
    st.markdown('<div class="action-button-row">', unsafe_allow_html=True)

    # Create columns based on number of buttons
    cols = st.columns(len(button_configs))

    button_clicks = []
    for i, (col, config) in enumerate(zip(cols, button_configs)):
        with col:
            label = config.get("label", f"Button {i+1}")
            on_click = config.get("on_click", None)
            btn_type = config.get("type", "secondary")
            disabled = config.get("disabled", False)
            use_full_width = config.get("use_container_width", True)

            # Create button
            clicked = st.button(
                label,
                key=f"{key_prefix}_{i}_{label}",
                type=btn_type,
                disabled=disabled,
                use_container_width=use_full_width
            )

            # Execute callback if provided and button was clicked
            if clicked and on_click:
                on_click()

            button_clicks.append(clicked)

    st.markdown('</div>', unsafe_allow_html=True)

    return button_clicks


def expandable_item_with_action(
    title: str,
    content_callback: Callable,
    action_label: str,
    action_callback: Callable,
    action_type: str = "secondary",
    key_prefix: str = "expandable"
):
    """
    Render an expandable item with an action button.

    Desktop: Expander and action button side-by-side (e.g., [expander: 85%] [button: 15%])
    Mobile: Both stacked vertically, full-width

    Args:
        title: Expander title text
        content_callback: Function to call to render content inside expander
        action_label: Action button label (e.g., "Delete", "Restore")
        action_callback: Function to call when action button clicked
        action_type: Button type ("primary" | "secondary", default: "secondary")
        key_prefix: Prefix for unique keys

    Example:
        def render_workout_details():
            st.write("Exercise 1: Bench Press")
            st.write("Exercise 2: Squats")

        def delete_workout():
            # Delete logic here
            pass

        expandable_item_with_action(
            title="Workout on 2024-01-15",
            content_callback=render_workout_details,
            action_label="Delete",
            action_callback=delete_workout,
            action_type="secondary",
            key_prefix="workout_123"
        )

    Returns:
        True if action button was clicked, False otherwise
    """
    st.markdown('<div class="expandable-row-with-action">', unsafe_allow_html=True)

    col1, col2 = st.columns([6, 1])

    with col1:
        with st.expander(title):
            content_callback()

    with col2:
        action_clicked = st.button(
            action_label,
            key=f"{key_prefix}_action",
            type=action_type,
            use_container_width=True
        )

        if action_clicked:
            action_callback()

    st.markdown('</div>', unsafe_allow_html=True)

    return action_clicked
