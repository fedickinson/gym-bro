"""
Log Workout Page - Audio-based workout logging with state machine.

This is the CORE mobile experience - optimized for gym use.

State Machine:
- ready: Show record button + template reference
- preview: Show parsed workout, approve/edit/cancel
- saved: Success message, next suggestion
"""

import streamlit as st
from src.ui.session import init_session_state, reset_log_workflow
from src.ui.navigation import render_bottom_nav
from src.ui.audio_recorder import combined_input
from src.ui.loading_overlay import show_loading_overlay, hide_loading_overlay
from src.agents.log_graph import start_workout_log, continue_workout_log
from src.tools.recommend_tools import suggest_next_workout, get_workout_template

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Log Workout - Gym Bro",
    page_icon="🎙️",
    layout="centered"  # Centered for better desktop UX
)

# Initialize session state
init_session_state()

# Render bottom navigation
st.session_state.current_page = 'Log'
render_bottom_nav('Log')

# Desktop optimizations
st.markdown("""
<style>
@media (min-width: 769px) {
    /* Hide bottom nav on desktop */
    .bottom-nav {
        display: none !important;
    }

    /* Better spacing */
    .main .block-container {
        padding: 2rem 2rem !important;
        max-width: 1000px !important;
    }
}

@media (max-width: 768px) {
    /* Mobile padding with space for bottom nav */
    .main .block-container {
        padding: 1rem 1rem 5rem 1rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# State Machine Functions
# ============================================================================

def render_ready_state():
    """State 1: Ready to record/type workout"""
    st.title("🎙️ Log Workout")
    st.caption("Record your workout via voice or type it out")

    # Show template reference (collapsible)
    with st.expander("📋 Your Personalized Workout (Tap to View)", expanded=False):
        try:
            suggestion = suggest_next_workout.invoke({})
            suggested_type = suggestion.get('suggested_type', 'Push')

            st.success(f"**Suggested:** {suggested_type}")
            st.caption(f"*{suggestion.get('reason', '')}*")

            # Get template for suggested type (adaptive by default)
            template = get_workout_template.invoke({"workout_type": suggested_type, "adaptive": True})

            if template and template.get('found'):
                # Show mode indicator
                mode = template.get('mode', 'static')
                if mode == 'adaptive':
                    st.info("✨ **Personalized** based on your training history")

                    # Show adaptations made
                    if template.get('adaptations'):
                        with st.expander("🔍 What Changed?", expanded=False):
                            for adaptation in template['adaptations']:
                                st.write(f"• {adaptation}")

                    # Show coaching notes
                    if template.get('coaching_notes'):
                        for note in template['coaching_notes']:
                            st.warning(note)

                # Display exercises with details
                st.subheader(f"{suggested_type} Workout")

                for ex in template.get('exercises', []):
                    with st.expander(f"**{ex.get('name')}**", expanded=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            target_sets = ex.get('target_sets', 3)
                            target_reps = ex.get('target_reps', 10)
                            st.metric("Sets × Reps", f"{target_sets} × {target_reps}")

                        with col2:
                            suggested_weight = ex.get('suggested_weight_lbs')
                            if suggested_weight:
                                st.metric("Suggested Weight", f"{suggested_weight:.0f} lbs")

                        # Show reasoning for adaptive templates
                        if mode == 'adaptive' and ex.get('reasoning'):
                            st.caption(f"💡 {ex['reasoning']}")

            else:
                st.caption("No template found for this workout type")

        except Exception as e:
            st.warning(f"Could not load template: {str(e)}")

    st.divider()

    # Combined audio + text input
    workout_input = combined_input()

    # Continue button
    if workout_input:
        if st.button("Continue →", type="primary", key="continue_btn"):
            try:
                # Show loading overlay (Step 2 of 2)
                show_loading_overlay(
                    step=2,
                    total=2,
                    message="Understanding your workout... 🧠"
                )

                # Start the log workflow
                workflow_state = start_workout_log(workout_input)

                # Hide overlay before rerun
                hide_loading_overlay()

                # Update state and rerun
                st.session_state.log_workflow_state = workflow_state
                st.session_state.log_state = 'preview'
                st.rerun()

            except Exception as e:
                hide_loading_overlay()
                st.error(f"❌ Failed to parse workout: {str(e)}")
                st.caption("Please try again or adjust your input")


def render_preview_state():
    """State 2: Preview parsed workout and get approval"""
    st.title("📋 Review Your Workout")

    workflow_state = st.session_state.log_workflow_state

    if not workflow_state or 'parsed_workout' not in workflow_state:
        st.error("No workout data found. Returning to start...")
        reset_log_workflow()
        st.rerun()
        return

    parsed = workflow_state.get('parsed_workout')

    # Display parsed workout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric("📅 Date", parsed.get('date', 'Unknown'))

    with col2:
        st.metric("🏋️ Type", parsed.get('type', 'Unknown'))

    st.divider()
    st.subheader("Exercises")

    # Display each exercise
    for ex in parsed.get('exercises', []):
        with st.expander(f"**{ex.get('name')}**", expanded=True):
            sets = ex.get('sets', [])

            if sets:
                # Display sets in a table format
                for i, s in enumerate(sets, 1):
                    reps = s.get('reps') if s.get('reps') is not None else '?'
                    weight = s.get('weight_lbs')

                    if weight:
                        st.write(f"Set {i}: **{reps} reps** @ **{weight} lbs**")
                    else:
                        st.write(f"Set {i}: **{reps} reps** (bodyweight)")
            else:
                st.caption("No sets recorded")

    if parsed.get('notes'):
        st.divider()
        st.info(f"**Notes:** {parsed['notes']}")

    st.divider()

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ SAVE", key="approve", type="primary"):
            save_workout("approve")

    with col2:
        if st.button("✏️ Edit", key="edit"):
            st.session_state.edit_mode = True
            st.rerun()

    with col3:
        if st.button("🔄 Re-record", key="re_record"):
            reset_log_workflow()
            st.rerun()

    with col4:
        if st.button("❌ Cancel", key="cancel"):
            cancel_workflow()

    # Edit mode
    if st.session_state.get('edit_mode'):
        st.divider()
        with st.form("edit_form"):
            st.subheader("Make Corrections")
            edit_instructions = st.text_area(
                "What needs to change?",
                placeholder="Example: Actually it was 145 lbs on bench",
                height=100
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Apply Changes"):
                    save_workout("edit", edit_instructions)
            with col2:
                if st.form_submit_button("Cancel Edit"):
                    st.session_state.edit_mode = False
                    st.rerun()


def render_saved_state():
    """State 3: Saved confirmation and next steps"""
    st.balloons()

    st.success("✅ Workout Saved!")
    st.title("Great job! 💪")

    workout_id = st.session_state.log_workflow_state.get('workout_id')
    if workout_id:
        st.caption(f"Workout ID: {workout_id}")

    st.divider()

    # Show what's next
    st.subheader("What's Next?")

    try:
        suggestion = suggest_next_workout.invoke({})
        st.info(f"**Suggested:** {suggestion.get('suggested_type', 'Unknown')}")
        st.write(suggestion.get('reason', ''))
    except:
        st.caption("Keep up the great work!")

    st.divider()

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎙️ Log Another Workout"):
            reset_log_workflow()
            st.rerun()

    with col2:
        if st.button("📊 View Progress"):
            reset_log_workflow()
            st.switch_page("pages/4_Progress.py")

    with col3:
        if st.button("🏠 Back to Home"):
            reset_log_workflow()
            st.switch_page("app.py")


def save_workout(choice: str, edit_instructions: str = None):
    """Continue workflow with user choice"""
    try:
        # Show loading overlay
        show_loading_overlay(
            step=1,
            total=1,
            message="Saving your workout... 💾"
        )

        final_state = continue_workout_log(
            state=st.session_state.log_workflow_state,
            user_choice=choice,
            edit_instructions=edit_instructions
        )

        # Hide overlay
        hide_loading_overlay()

        st.session_state.log_workflow_state = final_state

        if choice == "approve" or (choice == "edit" and final_state.get('saved')):
            st.session_state.log_state = 'saved'
        else:
            # Re-parse if edited
            st.session_state.log_state = 'preview'

        st.session_state.edit_mode = False
        st.rerun()

    except Exception as e:
        hide_loading_overlay()
        st.error(f"❌ Failed to save: {str(e)}")
        st.caption("Please try again")


def cancel_workflow():
    """Cancel and reset"""
    reset_log_workflow()
    st.rerun()


# ============================================================================
# Main State Machine
# ============================================================================

if st.session_state.log_state == 'ready':
    render_ready_state()
elif st.session_state.log_state == 'preview':
    render_preview_state()
elif st.session_state.log_state == 'saved':
    render_saved_state()
else:
    # Fallback - reset to ready
    reset_log_workflow()
    st.rerun()
