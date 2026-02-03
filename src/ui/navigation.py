"""
Navigation Component for Gym Bro.

Provides mobile-first bottom navigation bar that:
- Fixes to bottom on mobile viewports
- Hides on desktop (uses sidebar instead)
- Shows active page highlighting
- Provides large touch targets (60px height)
"""

import streamlit as st


def render_bottom_nav(current_page: str):
    """
    Render the bottom navigation bar.

    Uses classes from global styles (src/ui/styles.py) with proper Streamlit navigation.

    Args:
        current_page: Name of the current page ('Home', 'Log', 'Chat', 'History', 'Progress')
    """
    # Navigation items - using Streamlit button approach for reliable navigation
    nav_items = [
        {"label": "Home", "icon": "🏠", "page": "app.py"},
        {"label": "Log", "icon": "🎙️", "page": "pages/1_Log_Workout.py"},
        {"label": "Chat", "icon": "💬", "page": "pages/2_Chat.py"},
        {"label": "History", "icon": "📅", "page": "pages/3_History.py"},
        {"label": "Progress", "icon": "📊", "page": "pages/4_Progress.py"},
    ]

    # Use columns to create the bottom nav layout
    # Styles are defined in src/ui/styles.py - no inline CSS overrides
    st.markdown("""
    <style>
    /* Navigation Button Overrides (use adaptive spacing, no !important) */
    div[data-testid="column"] {
        padding: 0;
        margin: 0;
    }

    /* Navigation buttons styled as nav items */
    div[data-testid="column"] > div > div > div > button[kind="secondary"] {
        background: transparent;
        border: none;
        color: var(--color-text-secondary);
        min-height: 50px; /* Above iOS 44pt minimum */
        padding: var(--spacing-element) 0.25rem; /* Adaptive spacing - Apple HIG compliant */
        font-size: 0.75rem;
        margin: 0;
    }

    div[data-testid="column"] > div > div > div > button[kind="secondary"]:hover {
        background: var(--color-bg-tertiary);
        color: var(--color-text-primary);
    }

    /* PRIMARY action button (Log) - emphasized */
    div[data-testid="column"]:nth-child(2) > div > div > div > button[kind="secondary"] {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--color-primary-500);
    }

    div[data-testid="column"]:nth-child(2) > div > div > div > button[kind="secondary"]:hover {
        background: rgba(76, 175, 80, 0.1);
        color: var(--color-primary-500);
    }

    /* SECONDARY primary action button (Chat) - slightly emphasized */
    div[data-testid="column"]:nth-child(3) > div > div > div > button[kind="secondary"] {
        font-size: 0.8125rem;
        font-weight: 500;
    }

    div[data-testid="column"]:nth-child(3) > div > div > div > button[kind="secondary"]:hover {
        background: rgba(76, 175, 80, 0.05);
    }

    /* Container for bottom nav - uses adaptive spacing */
    .nav-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--color-bg-secondary);
        border-top: 1px solid var(--color-border);
        box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
        z-index: 999;
        padding: var(--spacing-element) 0;
        margin: 0;
    }

    /* Add padding to main content to account for fixed nav */
    .main {
        padding-bottom: 70px;
    }

    /* Hide on desktop */
    @media (min-width: 769px) {
        .nav-container {
            display: none;
        }
    }
    </style>
    <div class="nav-container">
    """, unsafe_allow_html=True)

    # Create equal columns for nav items
    cols = st.columns(len(nav_items))

    for idx, item in enumerate(nav_items):
        with cols[idx]:
            # Check if this is the active page
            if item["label"] == current_page:
                # Determine if this is a primary action item for enhanced styling
                is_primary = item["label"] == "Log"
                is_secondary_primary = item["label"] == "Chat"

                # Active page - show without button with enhanced visual state
                font_size = "0.875rem" if is_primary else "0.8125rem" if is_secondary_primary else "0.75rem"
                font_weight = "600" if is_primary else "500" if is_secondary_primary else "normal"
                bg_color = "rgba(76, 175, 80, 0.15)" if (is_primary or is_secondary_primary) else "transparent"

                st.markdown(f"""
                <div style="
                    text-align: center;
                    padding: var(--spacing-element) 0.25rem;
                    min-height: 50px;
                    color: var(--color-primary-500);
                    border-top: 3px solid var(--color-primary-500);
                    background: {bg_color};
                    font-weight: {font_weight};
                    margin: 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                ">
                    <div style="font-size: 20px; margin-bottom: var(--space-1);">{item["icon"]}</div>
                    <div style="font-size: {font_size};">{item["label"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Not active - show as clickable button
                if st.button(
                    f"{item['icon']}\n{item['label']}",
                    key=f"nav_{item['label']}_btn",
                    use_container_width=True,
                    type="secondary"
                ):
                    st.switch_page(item["page"])

    st.markdown("</div>", unsafe_allow_html=True)


def get_current_page_name() -> str:
    """
    Get the current page name for navigation highlighting.

    Returns:
        Page name ('Home', 'Log', 'Chat', 'History', or 'Progress')
    """
    # Try to determine from query params or session state
    # For now, we'll rely on pages setting this manually
    return st.session_state.get('current_page', 'Home')


def scroll_to_top():
    """Force scroll to top of page using JavaScript."""
    st.markdown("""
    <script>
        window.scrollTo({top: 0, behavior: 'instant'});
        document.addEventListener('DOMContentLoaded', function() {
            window.scrollTo({top: 0, behavior: 'instant'});
        });
    </script>
    """, unsafe_allow_html=True)
