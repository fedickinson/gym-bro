"""
Navigation Component for Gym Bro.

Provides mobile-first bottom navigation bar that:
- Fixes to bottom on mobile viewports
- Hides on desktop (uses sidebar instead)
- Shows active page highlighting
- Provides large touch targets (60px height)
"""

import streamlit as st


def inject_bottom_nav_css():
    """
    Inject CSS for mobile-first bottom navigation.

    This creates a fixed bottom nav bar on mobile that:
    - Sticks to the bottom of the viewport
    - Has large touch targets (44px minimum per iOS guidelines)
    - Hides on desktop (>768px width)
    - Adds bottom padding to content so it doesn't overlap
    """
    st.markdown("""
    <style>
    /* Bottom Navigation Bar (Mobile Only) */
    @media (max-width: 768px) {
        /* Bottom nav container */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: #1E1E1E;
            border-top: 1px solid #333;
            display: flex;
            justify-content: space-around;
            align-items: center;
            z-index: 999;
            padding: 0;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
        }

        /* Nav items */
        .nav-item {
            flex: 1;
            text-align: center;
            padding: 8px 4px;
            cursor: pointer;
            transition: all 0.2s;
            min-height: 44px; /* iOS touch target guideline */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #FAFAFA;
            text-decoration: none;
        }

        .nav-item:active {
            background: #333;
        }

        .nav-item.active {
            color: #4CAF50;
            border-top: 2px solid #4CAF50;
        }

        /* Icon sizing */
        .nav-item .icon {
            font-size: 24px;
            margin-bottom: 2px;
        }

        .nav-item .label {
            font-size: 10px;
            font-weight: 500;
        }

        /* Add bottom padding to main content to prevent overlap */
        .main .block-container {
            padding-bottom: 80px !important;
        }
    }

    /* Desktop: hide bottom nav */
    @media (min-width: 769px) {
        .bottom-nav {
            display: none;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def render_bottom_nav(current_page: str):
    """
    Render the bottom navigation bar.

    Args:
        current_page: Name of the current page ('Home', 'Log', 'Chat', 'History', 'Progress')
    """
    inject_bottom_nav_css()

    # Navigation items
    nav_items = [
        {"label": "Home", "icon": "🏠", "page": "app"},
        {"label": "Log", "icon": "🎙️", "page": "pages/1_Log_Workout"},
        {"label": "Chat", "icon": "💬", "page": "pages/2_Chat"},
        {"label": "History", "icon": "📅", "page": "pages/3_History"},
        {"label": "Progress", "icon": "📊", "page": "pages/4_Progress"},
    ]

    # Build HTML for bottom nav
    nav_html = '<div class="bottom-nav">'

    for item in nav_items:
        active_class = "active" if item["label"] == current_page else ""

        nav_html += f'''
        <div class="nav-item {active_class}" onclick="window.parent.location.href='/{item["page"]}.py'">
            <div class="icon">{item["icon"]}</div>
            <div class="label">{item["label"]}</div>
        </div>
        '''

    nav_html += '</div>'

    st.markdown(nav_html, unsafe_allow_html=True)


def get_current_page_name() -> str:
    """
    Get the current page name for navigation highlighting.

    Returns:
        Page name ('Home', 'Log', 'Chat', 'History', or 'Progress')
    """
    # Try to determine from query params or session state
    # For now, we'll rely on pages setting this manually
    return st.session_state.get('current_page', 'Home')
