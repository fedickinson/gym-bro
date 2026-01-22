"""Mobile-friendly input components for gym environment."""
import streamlit as st


def render_number_stepper(
    label: str,
    value: float,
    step: float = 1.0,
    min_value: float = 0.0,
    max_value: float = 999.0,
    key: str = None
) -> float:
    """
    Large touch-friendly +/- stepper for mobile editing.

    Args:
        label: Display label
        value: Current value
        step: Increment/decrement amount
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        key: Unique key for session state

    Returns:
        Updated value
    """
    st.markdown(f"**{label}**")

    # Use session state to track value
    state_key = f"stepper_{key}" if key else f"stepper_{label}"
    if state_key not in st.session_state:
        st.session_state[state_key] = value

    # 3-column layout: [−] [Display] [+]
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("➖", key=f"{state_key}_minus", use_container_width=True):
            new_val = max(min_value, st.session_state[state_key] - step)
            st.session_state[state_key] = new_val
            st.rerun()

    with col2:
        # Display only, large font
        display_val = st.session_state[state_key]
        st.markdown(f"""
        <div style="
            font-size: 2rem;
            font-weight: 700;
            text-align: center;
            padding: 12px;
            background: var(--color-bg-tertiary);
            border-radius: 8px;
            border: 2px solid var(--color-border);
        ">
            {display_val}
        </div>
        """, unsafe_allow_html=True)

    with col3:
        if st.button("➕", key=f"{state_key}_plus", use_container_width=True):
            new_val = min(max_value, st.session_state[state_key] + step)
            st.session_state[state_key] = new_val
            st.rerun()

    return st.session_state[state_key]
