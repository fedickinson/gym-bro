"""
Central CSS styling system for the gym-bro app.

This module provides a unified design system with:
- Design tokens (colors, spacing)
- Typography scale
- Component styles
- Responsive breakpoints

Mobile-first approach optimized for gym environment (large text, high contrast, touch-friendly).
"""

def get_global_styles():
    """
    Returns centralized CSS for the entire app.

    Includes design tokens, typography scale, spacing system, and component styles.
    All pages should import and apply these styles for consistency.

    Returns:
        str: Complete CSS as a string to be used with st.markdown(unsafe_allow_html=True)
    """
    return """
    <style>
    /* ========================================
       DESIGN TOKENS
       ======================================== */

    :root {
        /* Animation & Transitions */
        --transition-fast: 0.1s ease;
        --transition-normal: 0.2s ease;
        --transition-slow: 0.3s ease;
        /* Colors - Primary (Success/Progress) */
        --color-primary-500: #4CAF50;
        --color-primary-600: #45a049;
        --color-primary-700: #3d8b40;
        --color-primary-100: #c8e6c9;

        /* Colors - Accent (Exercise focus with green theme) */
        --color-accent-500: #66BB6A;
        --color-accent-gradient: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);

        /* Colors - Semantic */
        --color-success: #4CAF50;
        --color-warning: #FFC107;
        --color-error: #F44336;
        --color-info: #2196F3;

        /* Colors - Action-specific (for consistency) */
        --color-destructive: #d32f2f;        /* Delete buttons */
        --color-destructive-hover: #b71c1c;  /* Delete button hover */
        --color-restore: #2e7d32;            /* Restore actions */
        --color-restore-hover: #1b5e20;      /* Restore hover */

        /* Colors - Neutrals (Dark Theme) */
        --color-bg-primary: #0E1117;
        --color-bg-secondary: #1E1E1E;
        --color-bg-tertiary: #2A2A2A;
        --color-text-primary: #FAFAFA;
        --color-text-secondary: #B0B0B0;
        --color-border: #3A3A3A;

        /* Spacing (8pt grid system) */
        --space-1: 0.25rem;  /* 4px */
        --space-2: 0.5rem;   /* 8px */
        --space-3: 0.75rem;  /* 12px */
        --space-4: 1rem;     /* 16px */
        --space-5: 1.5rem;   /* 24px */
        --space-6: 2rem;     /* 32px */
        --space-8: 3rem;     /* 48px */
        --space-10: 4rem;    /* 64px */
    }

    /* ========================================
       TYPOGRAPHY SCALE
       ======================================== */

    .text-display {
        font-size: 2.5rem;      /* 40px mobile */
        font-weight: 700;
        line-height: 1.2;
    }

    .text-h1 {
        font-size: 2rem;        /* 32px mobile */
        font-weight: 700;
        line-height: 1.3;
    }

    .text-h2 {
        font-size: 1.5rem;      /* 24px mobile */
        font-weight: 600;
        line-height: 1.4;
    }

    .text-h3 {
        font-size: 1.25rem;     /* 20px mobile */
        font-weight: 600;
        line-height: 1.4;
    }

    .text-emphasis {
        font-size: 1.125rem;    /* 18px mobile */
        font-weight: 600;
        line-height: 1.4;
    }

    .text-body {
        font-size: 1rem;        /* 16px */
        font-weight: 400;
        line-height: 1.6;
    }

    .text-small {
        font-size: 0.875rem;    /* 14px */
        font-weight: 400;
        line-height: 1.5;
    }

    .text-caption {
        font-size: 0.75rem;     /* 12px */
        font-weight: 400;
        line-height: 1.4;
    }

    /* Phase 2: Exercise detail prominence (for summaries/review screens) */
    .exercise-title {
        font-size: 1.75rem;     /* 28px mobile - Exercise names in summaries */
        font-weight: 700;
        line-height: 1.2;
        color: var(--color-primary-500);
    }

    .set-detail {
        font-size: 1.25rem;     /* 20px mobile - Set details like "Set 1: 8 reps @ 65 lbs" */
        font-weight: 600;
        line-height: 1.5;
    }

    .stat-highlight {
        font-size: 1.5rem;      /* 24px mobile - Volume and key stats */
        font-weight: 700;
        color: var(--color-primary-500);
    }

    /* ========================================
       COMPONENT STYLES
       ======================================== */

    /* Buttons */
    .btn-primary {
        min-height: 56px !important;
        font-size: 1.125rem !important;
        font-weight: 600 !important;
        padding: var(--space-4) var(--space-6) !important;
        border-radius: 12px !important;
        background: var(--color-accent-gradient) !important;
        color: white !important;
        border: none !important;
    }

    .btn-secondary {
        min-height: 48px !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        padding: var(--space-3) var(--space-5) !important;
        border-radius: 8px !important;
        background: var(--color-bg-secondary) !important;
        color: var(--color-text-primary) !important;
        border: 1px solid var(--color-border) !important;
    }

    .btn-full-width {
        width: 100% !important;
    }

    /* Number inputs for workout (LARGE for sweaty hands) */
    .workout-number-input {
        min-height: 64px !important;
        font-size: 1.5rem !important;  /* 24px - LARGE */
        font-weight: 700 !important;
        text-align: center !important;
        border: 2px solid var(--color-border) !important;
        border-radius: 8px !important;
        background: var(--color-bg-secondary) !important;
        color: var(--color-text-primary) !important;
    }

    .workout-number-input:focus {
        border-color: var(--color-primary-500) !important;
        outline: 2px solid var(--color-primary-100) !important;
        outline-offset: 2px;
    }

    /* Cards */
    .card {
        background: var(--color-bg-secondary);
        padding: var(--space-5);
        border-radius: 12px;
        border: 1px solid var(--color-border);
    }

    /* Progress items */
    .progress-item {
        background: var(--color-bg-secondary);
        padding: var(--space-4);
        border-radius: 8px;
        border-left: 4px solid var(--color-border);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--space-3);
    }

    .progress-item.complete {
        border-left-color: var(--color-success);
    }

    .progress-item.in-progress {
        border-left-color: var(--color-warning);
    }

    .progress-item.missing {
        border-left-color: var(--color-error);
    }

    /* Exercise banner (GREEN theme, not purple) */
    .exercise-banner {
        background: var(--color-accent-gradient);
        color: white;
        padding: var(--space-6) var(--space-5);
        border-radius: 12px;
        text-align: center;
        margin-bottom: var(--space-5);
    }

    .exercise-name {
        font-size: 2rem;        /* 32px mobile */
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: var(--space-2);
    }

    .exercise-progress {
        font-size: 0.875rem;
        font-weight: 500;
        opacity: 0.9;
    }

    /* Exercise target display */
    .exercise-target {
        background: var(--color-bg-secondary);
        padding: var(--space-5);
        border-radius: 8px;
        text-align: center;
        margin-bottom: var(--space-4);
    }

    .target-label {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--color-text-secondary);
        margin-bottom: var(--space-3);
    }

    .target-value {
        font-size: 1rem;
        line-height: 1.6;
    }

    /* Set number display (LARGE for gym visibility) */
    .set-number-display {
        font-size: 2.5rem;      /* 40px mobile - LARGE for glancing */
        font-weight: 700;
        text-align: center;
        margin: var(--space-6) 0 var(--space-4);
        color: var(--color-primary-500);
    }

    .set-target {
        font-size: 1.125rem;
        font-weight: 600;
        text-align: center;
        color: var(--color-text-primary);  /* Changed from secondary to primary for better visibility */
        margin-bottom: var(--space-6);
    }

    /* Rest timer (VERY LARGE for quick glancing) */
    .rest-timer-display {
        font-size: 4rem;        /* 64px mobile - VERY LARGE */
        font-weight: 700;
        text-align: center;
        color: var(--color-primary-500);
        margin: var(--space-8) 0;
        line-height: 1;
        font-variant-numeric: tabular-nums; /* Monospace numbers for timer */
    }

    /* Progress bars */
    .progress-bar {
        height: 8px;
        background: var(--color-bg-tertiary);
        border-radius: 4px;
        overflow: hidden;
        margin: var(--space-4) 0;
    }

    .rest-progress-bar {
        height: 8px;
        background: var(--color-bg-tertiary);
        border-radius: 4px;
        overflow: hidden;
        margin: var(--space-4) 0 var(--space-6);
    }

    .progress-fill {
        height: 100%;
        background: var(--color-accent-gradient);
        transition: width 0.3s ease;
    }

    .rest-progress-fill {
        height: 100%;
        background: var(--color-accent-gradient);
        transition: width 1s linear;
    }

    /* Workout progress bar */
    .workout-progress {
        margin: var(--space-5) 0;
    }

    .workout-progress-label {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        margin-bottom: var(--space-2);
    }

    .workout-progress-bar {
        height: 12px;
        background: var(--color-bg-tertiary);
        border-radius: 6px;
        overflow: hidden;
    }

    .workout-progress-fill {
        height: 100%;
        background: var(--color-accent-gradient);
    }

    /* Exercise complete banner */
    .exercise-complete-banner {
        background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
        color: white;
        padding: var(--space-5);
        border-radius: 12px;
        text-align: center;
        margin-bottom: var(--space-5);
    }

    .set-summary-item {
        display: flex;
        justify-content: space-between;
        padding: var(--space-3) var(--space-4);
        background: var(--color-bg-secondary);
        border-radius: 8px;
        margin-bottom: var(--space-2);
        font-size: 1rem;
    }

    /* Activity items */
    .activity-item {
        background: var(--color-bg-secondary);
        padding: var(--space-4);
        border-radius: 8px;
        margin-bottom: var(--space-3);
        border: 1px solid var(--color-border);
    }

    .activity-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--space-2);
    }

    .activity-title {
        font-size: 1rem;
        font-weight: 600;
    }

    .activity-date {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
    }

    /* Rest adjustment buttons */
    .rest-adjustment-btn {
        min-height: 48px;
        font-size: 1rem;
        font-weight: 600;
    }

    /* ========================================
       LAYOUT & SPACING
       ======================================== */

    /* Main container */
    .main .block-container {
        padding: 1rem 1rem 5rem 1rem !important;
        max-width: 100% !important;
    }

    /* Section spacing */
    .section-gap {
        margin-bottom: var(--space-6);
    }

    /* Reduce divider usage (make less prominent) */
    hr {
        margin: var(--space-6) 0 !important;
        border-color: var(--color-border) !important;
        opacity: 0.3 !important;
    }

    /* Weekly progress grid */
    .weekly-progress-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: var(--space-3);
    }

    .progress-label {
        font-size: 1rem;
        font-weight: 500;
    }

    .progress-value {
        font-size: 1.5rem;
        font-weight: 700;
    }

    /* ========================================
       RESPONSIVE BREAKPOINTS
       ======================================== */

    /* Desktop (≥769px) */
    @media (min-width: 769px) {
        /* Typography scaling */
        .text-display { font-size: 3rem; }          /* 48px desktop */
        .text-h1 { font-size: 2.5rem; }             /* 40px desktop */
        .text-h2 { font-size: 1.75rem; }            /* 28px desktop */
        .text-emphasis { font-size: 1.25rem; }      /* 20px desktop */

        /* Phase 2: Exercise detail scaling */
        .exercise-title { font-size: 2rem; }        /* 32px desktop */
        .set-detail { font-size: 1.375rem; }        /* 22px desktop */
        .stat-highlight { font-size: 1.75rem; }     /* 28px desktop */

        .exercise-name { font-size: 2.5rem; }       /* 40px desktop */
        .target-value { font-size: 1.125rem; }

        /* Component sizing */
        .btn-primary { min-height: 48px !important; }
        .btn-secondary { min-height: 44px !important; }
        .workout-number-input {
            min-height: 56px !important;
            font-size: 1.25rem !important;          /* 20px desktop */
        }
        .set-number-display { font-size: 3rem; }    /* 48px desktop */
        .rest-timer-display { font-size: 5rem; }    /* 80px desktop */

        /* Layout */
        .main .block-container {
            padding: 2rem 2rem !important;
            max-width: 1200px !important;
            margin: 0 auto;
        }

        .section-gap { margin-bottom: var(--space-8); }

        /* Weekly progress - 2 columns on desktop */
        .weekly-progress-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: var(--space-4);
        }

        /* Hide bottom nav on desktop */
        .bottom-nav { display: none !important; }
    }

    /* Tablet (481px - 768px) */
    @media (min-width: 481px) and (max-width: 768px) {
        .main .block-container {
            padding: 1.5rem 1.5rem 5rem 1.5rem !important;
        }
    }

    /* Mobile small (≤480px) */
    @media (max-width: 480px) {
        /* Tighter spacing on very small screens */
        .card { padding: var(--space-4); }
        .exercise-banner { padding: var(--space-5) var(--space-4); }
    }

    /* Mobile (≤768px) - ensure bottom nav doesn't cover content */
    @media (max-width: 768px) {
        .main .block-container {
            padding-bottom: 80px !important;
        }
    }

    /* ========================================
       BOTTOM NAVIGATION (Mobile)
       ======================================== */

    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: var(--color-bg-secondary);
        border-top: 1px solid var(--color-border);
        display: flex;
        justify-content: space-around;
        align-items: center;
        z-index: 999;
        padding: 0 var(--space-2);
        box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
    }

    .bottom-nav-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 44px;
        min-height: 44px;
        padding: 8px 4px;
        color: var(--color-text-secondary);
        text-decoration: none;
        font-size: 0.75rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    .bottom-nav-item:active {
        background: var(--color-bg-tertiary);
    }

    .bottom-nav-item.active {
        color: var(--color-primary-500);
        border-top: 2px solid var(--color-primary-500);
    }

    /* ========================================
       UTILITY CLASSES
       ======================================== */

    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .mt-4 { margin-top: var(--space-4); }
    .mb-4 { margin-bottom: var(--space-4); }
    .mb-6 { margin-bottom: var(--space-6); }
    .p-4 { padding: var(--space-4); }
    .p-5 { padding: var(--space-5); }

    /* ========================================
       STREAMLIT OVERRIDES
       ======================================== */

    /* Reduce Streamlit's default spacing */
    .element-container {
        margin-bottom: var(--space-3) !important;
    }

    /* Improve button styling */
    .stButton > button {
        width: 100%;
    }

    /* Number input styling (apply large workout input styles) */
    .stNumberInput > div > div > input {
        min-height: 64px;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
    }

    @media (min-width: 769px) {
        .stNumberInput > div > div > input {
            min-height: 56px;
            font-size: 1.25rem;
        }
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }

    /* Caption reduction (use sparingly) */
    .stCaptionContainer {
        font-size: 0.75rem;
        color: var(--color-text-secondary);
    }

    /* Sidebar styling */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            display: none;
        }
    }

    /* ========================================
       TOUCH INTERACTIONS & MOBILE UX
       ======================================== */

    /* Better button press states for mobile */
    button:active {
        transform: scale(0.98);
        transition: transform var(--transition-fast);
    }

    button {
        transition: all var(--transition-normal);
    }

    /* Primary buttons get special press feedback */
    button[kind="primary"]:active {
        transform: scale(0.97);
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
    }

    /* Larger minimum tap spacing on mobile */
    @media (max-width: 768px) {
        .stButton {
            margin-bottom: var(--space-3) !important;
        }

        /* Ensure buttons have adequate height */
        .stButton > button {
            min-height: 44px !important;
            padding: 0.5rem 1rem !important;
        }
    }

    /* Enhanced focus for accessibility */
    button:focus-visible,
    input:focus-visible,
    textarea:focus-visible,
    select:focus-visible {
        outline: 3px solid var(--color-primary-500) !important;
        outline-offset: 2px !important;
    }

    /* Remove default focus for mouse users (keeps keyboard focus) */
    button:focus:not(:focus-visible),
    input:focus:not(:focus-visible) {
        outline: none;
    }

    /* Smooth transitions for interactive elements */
    .stButton > button,
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        transition: all var(--transition-normal);
    }

    /* Hover states with smooth transitions */
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Mobile: Remove hover effects (no cursor on touch) */
    @media (hover: none) and (pointer: coarse) {
        .stButton > button:hover {
            transform: none;
            box-shadow: none;
        }
    }

    /* Tap highlight color for iOS */
    button, a, input, textarea {
        -webkit-tap-highlight-color: rgba(76, 175, 80, 0.2);
    }

    /* Prevent text selection on buttons (better touch UX) */
    button {
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }

    /* ========================================
       MOBILE OPTIMIZATION - COLUMN STACKING
       ======================================== */

    /* Auto-stack Streamlit columns on mobile (GLOBAL FIX) */
    @media (max-width: 768px) {
        [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: var(--space-3);
        }

        /* Remove bottom margin from last column in a row */
        [data-testid="column"]:last-child {
            margin-bottom: 0;
        }
    }

    /* ========================================
       MOBILE OPTIMIZATION - SPECIFIC PATTERNS
       ======================================== */

    /* Action button rows (3-4 column button layouts) */
    .action-button-row [data-testid="column"] {
        margin-bottom: var(--space-2) !important;
    }

    @media (max-width: 768px) {
        .action-button-row [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }

    /* Checkbox rows (narrow split fix - keep checkbox column at 48px on mobile) */
    @media (max-width: 768px) {
        .checkbox-row {
            display: flex !important;
            align-items: center !important;
        }

        .checkbox-row [data-testid="column"]:first-child {
            min-width: 48px !important;
            max-width: 48px !important;
            flex: 0 0 48px !important;
            margin-bottom: 0 !important;
        }

        .checkbox-row [data-testid="column"]:not(:first-child) {
            flex: 1 1 auto !important;
            min-width: 0 !important;
            margin-bottom: 0 !important;
        }
    }

    /* Expandable row with action button (e.g., History/Trash delete/restore) */
    @media (max-width: 768px) {
        .expandable-row-with-action {
            flex-direction: column !important;
        }

        .expandable-row-with-action [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: var(--space-2) !important;
        }

        .expandable-row-with-action [data-testid="column"]:last-child {
            margin-bottom: 0 !important;
        }
    }

    /* Mobile-only filter UI (show on mobile, hide on desktop) */
    .mobile-filters {
        display: none;
    }

    @media (max-width: 768px) {
        .mobile-filters {
            display: block;
            margin-bottom: var(--space-4);
        }
    }

    @media (min-width: 769px) {
        .mobile-filters {
            display: none !important;
        }
    }

    /* Desktop-only content (hide on mobile) */
    @media (max-width: 768px) {
        .desktop-only {
            display: none !important;
        }
    }

    </style>
    """
