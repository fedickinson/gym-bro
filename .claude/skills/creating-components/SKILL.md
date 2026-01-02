---
name: creating-components
description: Generates Streamlit UI components following the centralized design system. Use when building pages, creating cards, or adding UI elements that need mobile-first design and consistent styling.
---

# Streamlit Component Generator

## Design System Overview

**File**: `/Users/franklindickinson/Projects/gym-bro/src/ui/styles.py` (611 LOC)

**Key Principles**:
- Mobile-first (optimized for gym environment)
- 8pt grid system for spacing
- High contrast for readability
- Large touch targets (44px minimum)

---

## Quick Component Creation Workflow

```
Component Creation:
- [ ] Step 1: Identify component type (Page/Widget/Card/Form)
- [ ] Step 2: Read design system reference
- [ ] Step 3: Generate component with design tokens
- [ ] Step 4: Test on mobile viewport
- [ ] Step 5: Integrate into page
```

---

## Top 10 Design System Classes

```css
/* Typography */
.text-h1 { font-size: 2.5rem; font-weight: 700; }
.text-h2 { font-size: 2rem; font-weight: 600; }
.text-emphasis { font-size: 1.125rem; font-weight: 600; }
.text-body { font-size: 1rem; line-height: 1.6; }
.text-small { font-size: 0.875rem; }
.text-caption { font-size: 0.75rem; }

/* Layout */
.card { background: var(--color-bg-secondary); padding: var(--space-4); }
.container { max-width: 800px; margin: 0 auto; }

/* Components */
.activity-item { border: 1px solid var(--color-border); }
.exercise-banner { background: var(--color-primary-500); }
```

---

## Color Tokens

```css
--color-primary-500: #4CAF50  /* Green */
--color-text-primary: #FFFFFF
--color-text-secondary: #B0B0B0
--color-bg-primary: #0E1117   /* Dark */
--color-bg-secondary: #1A1A1A
--color-border: #2A2A2A
```

---

## Spacing Tokens

```css
--space-1: 0.25rem   /* 4px */
--space-2: 0.5rem    /* 8px */
--space-3: 0.75rem   /* 12px */
--space-4: 1rem      /* 16px */
--space-6: 1.5rem    /* 24px */
--space-8: 2rem      /* 32px */
```

---

## Component Templates

### Template 1: Workout Card

```python
def workout_summary_card(log: dict):
    """
    Display workout summary card following design system.

    Args:
        log: Workout log dict from workout_logs.json
    """
    from datetime import datetime

    # Extract data
    log_date = log.get("date", "Unknown")
    workout_type = log.get("type", "Unknown")
    exercises = log.get("exercises", [])
    notes = log.get("notes")

    # Calculate volume
    total_volume = 0
    for ex in exercises:
        for set_data in ex.get("sets", []):
            reps = set_data.get("reps", 0)
            weight = set_data.get("weight_lbs", 0)
            total_volume += reps * weight

    # Format date
    try:
        date_obj = datetime.strptime(log_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%b %d, %Y")
    except:
        formatted_date = log_date

    # Render card
    card_html = f"""
    <div class="activity-item">
        <div class="activity-header">
            <span class="activity-title text-emphasis">{workout_type}</span>
            <span class="activity-date text-small">{formatted_date}</span>
        </div>
        <div style="display: flex; gap: var(--space-4); margin-top: var(--space-3);">
            <div>
                <div class="text-caption" style="color: var(--color-text-secondary);">Exercises</div>
                <div class="text-emphasis">{len(exercises)}</div>
            </div>
            <div>
                <div class="text-caption" style="color: var(--color-text-secondary);">Volume</div>
                <div class="text-emphasis">{int(total_volume):,} lbs</div>
            </div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    # Expandable details
    with st.expander("View Exercises"):
        for ex in exercises:
            st.markdown(f"**{ex.get('name')}**")
            for i, set_data in enumerate(ex.get("sets", []), 1):
                reps = set_data.get("reps", 0)
                weight = set_data.get("weight_lbs")
                if weight:
                    st.caption(f"Set {i}: {reps} reps @ {weight} lbs")
                else:
                    st.caption(f"Set {i}: {reps} reps (bodyweight)")
```

---

### Template 2: Stat Metric

```python
def stat_metric(label: str, value: str | int, delta: str | None = None):
    """
    Display a metric with optional delta indicator.

    Args:
        label: Metric label (e.g., "Workouts This Week")
        value: Main value (e.g., "5" or "2 of 6")
        delta: Optional change indicator (e.g., "+2" or "-1")
    """
    delta_html = ""
    if delta:
        delta_color = "var(--color-primary-500)" if "+" in str(delta) else "var(--color-error)"
        delta_html = f"""
        <div class="text-caption" style="color: {delta_color};">
            {delta}
        </div>
        """

    metric_html = f"""
    <div style="
        background: var(--color-bg-secondary);
        padding: var(--space-4);
        border-radius: 8px;
        border: 1px solid var(--color-border);
    ">
        <div class="text-caption" style="color: var(--color-text-secondary);">
            {label}
        </div>
        <div class="text-h2" style="margin-top: var(--space-2);">
            {value}
        </div>
        {delta_html}
    </div>
    """

    st.markdown(metric_html, unsafe_allow_html=True)
```

---

### Template 3: Page Layout

```python
# pages/NewPage.py

import streamlit as st
from src.ui.styles import get_global_styles
from src.ui.navigation import render_bottom_nav, render_sidebar

# Page config
st.set_page_config(
    page_title="My Page - Gym Bro",
    page_icon="💪",
    layout="centered"
)

# Apply global styles
st.markdown(get_global_styles(), unsafe_allow_html=True)

# Render navigation
render_sidebar()

# Page content
st.title("My Page Title")

# Use components here
stat_metric("Metric Label", "Value", delta="+1")

# Bottom navigation (mobile)
render_bottom_nav()
```

---

## Mobile-First Patterns

### Responsive Breakpoints

```python
# In styles.py
@media (max-width: 768px) {
    .text-h1 { font-size: 2rem; }  /* Smaller on mobile */
    .container { padding: var(--space-2); }
}
```

### Touch Targets

```python
# Buttons/links should be at least 44px
st.button("Action", use_container_width=True)  # Full width on mobile
```

### Mobile Navigation

```python
from src.ui.navigation import render_bottom_nav

# Bottom nav only shows on mobile (max-width: 768px)
render_bottom_nav()
```

---

## Integration Example

### Adding New Page

```python
# pages/6_New_Feature.py

import streamlit as st
from src.ui.styles import get_global_styles
from src.ui.navigation import render_bottom_nav, render_sidebar
from src.data import get_all_logs

st.set_page_config(page_title="New Feature", page_icon="🆕", layout="centered")
st.markdown(get_global_styles(), unsafe_allow_html=True)

render_sidebar()

st.title("New Feature")

# Fetch data
logs = get_all_logs()

# Display with component
for log in logs[:5]:
    workout_summary_card(log)

render_bottom_nav()
```

---

## Reference Files

- [DESIGN-SYSTEM.md](DESIGN-SYSTEM.md) - Complete design token reference
- [COMPONENT-EXAMPLES.md](COMPONENT-EXAMPLES.md) - More examples from existing pages

**Design System File**: `/Users/franklindickinson/Projects/gym-bro/src/ui/styles.py`
