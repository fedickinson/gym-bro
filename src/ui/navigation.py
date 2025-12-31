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
    # We'll style them to look like the fixed bottom nav with CSS
    st.markdown("""
    <style>
    /* Override for navigation buttons to look like nav items */
    div[data-testid="column"] > div > div > div > button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        color: var(--color-text-secondary) !important;
        min-height: 60px !important;
        padding: 8px 4px !important;
        font-size: 0.75rem !important;
    }

    div[data-testid="column"] > div > div > div > button[kind="secondary"]:hover {
        background: var(--color-bg-tertiary) !important;
        color: var(--color-text-primary) !important;
    }

    /* Container for bottom nav */
    .nav-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--color-bg-secondary);
        border-top: 1px solid var(--color-border);
        box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
        z-index: 999;
        padding: 0;
    }

    /* Hide on desktop */
    @media (min-width: 769px) {
        .nav-container {
            display: none !important;
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
                # Active page - show without button
                st.markdown(f"""
                <div style="text-align: center; padding: 8px 4px; color: var(--color-primary-500); border-top: 2px solid var(--color-primary-500);">
                    <div style="font-size: 24px; margin-bottom: 2px;">{item["icon"]}</div>
                    <div style="font-size: 0.75rem;">{item["label"]}</div>
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
