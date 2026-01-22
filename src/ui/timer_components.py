"""Client-side JavaScript timer component."""
import streamlit as st
import time


def render_rest_timer(
    duration_seconds: int,
    on_complete_callback: callable = None,
    show_quick_adjust: bool = True
):
    """
    Client-side countdown timer with auto-advance.

    Uses JavaScript for smooth countdown without st.rerun() polling.
    Auto-advances by programmatically clicking hidden button when timer expires.

    Args:
        duration_seconds: Rest duration in seconds
        on_complete_callback: Function to call when timer completes (for state updates)
        show_quick_adjust: Show 30s/60s/90s quick adjust buttons
    """
    # Initialize timer state
    if 'rest_timer_active' not in st.session_state:
        st.session_state.rest_timer_active = False

    if not st.session_state.rest_timer_active:
        # Start timer
        st.session_state.rest_start_time = time.time()
        st.session_state.rest_duration = duration_seconds
        st.session_state.rest_timer_active = True

    elapsed = time.time() - st.session_state.rest_start_time
    remaining = max(0, st.session_state.rest_duration - elapsed)

    # Timer display and JavaScript countdown
    st.markdown(f"""
    <div class="rest-timer-container">
        <div class="rest-timer-display" id="timer-display">
            {int(remaining // 60)}:{int(remaining % 60):02d}
        </div>
        <div class="rest-progress-bar">
            <div class="rest-progress-fill" id="progress-fill"></div>
        </div>
    </div>

    <script>
        // Client-side countdown
        let startTime = {st.session_state.rest_start_time};
        let duration = {st.session_state.rest_duration};

        function updateTimer() {{
            let elapsed = (Date.now() / 1000) - startTime;
            let remaining = Math.max(0, duration - elapsed);

            // Update display
            let mins = Math.floor(remaining / 60);
            let secs = Math.floor(remaining % 60);
            let display = document.getElementById('timer-display');
            if (display) {{
                display.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
            }}

            // Update progress bar
            let progress = (elapsed / duration) * 100;
            let fill = document.getElementById('progress-fill');
            if (fill) {{
                fill.style.width = Math.min(100, progress) + '%';
            }}

            // Auto-complete when timer expires
            if (remaining <= 0) {{
                let completeBtn = document.getElementById('timer-complete-btn');
                if (completeBtn) {{
                    completeBtn.click();
                }}
                return;  // Stop interval
            }}

            // Continue countdown
            setTimeout(updateTimer, 100);  // Update every 100ms for smooth display
        }}

        // Start countdown on page load
        updateTimer();
    </script>
    """, unsafe_allow_html=True)

    # Hidden button for auto-complete (clicked by JavaScript)
    if st.button("Complete", key="timer-complete-btn", type="primary", use_container_width=True):
        st.session_state.rest_timer_active = False
        if on_complete_callback:
            on_complete_callback()
        st.rerun()

    # Quick adjust buttons (these DO use st.rerun, but only on explicit user action)
    if show_quick_adjust:
        st.markdown("**Quick Adjust:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("30s", use_container_width=True):
                st.session_state.rest_start_time = time.time()
                st.session_state.rest_duration = 30
                st.rerun()

        with col2:
            if st.button("60s", use_container_width=True):
                st.session_state.rest_start_time = time.time()
                st.session_state.rest_duration = 60
                st.rerun()

        with col3:
            if st.button("90s", use_container_width=True):
                st.session_state.rest_start_time = time.time()
                st.session_state.rest_duration = 90
                st.rerun()
