"""
Log Workout Page - Audio-based workout logging with state machine.

This is the CORE mobile experience - optimized for gym use.

State Machine:
- ready: Show record button + template reference
- preview: Show parsed workout, approve/edit/cancel
- saved: Success message, next suggestion
"""

# Load environment variables FIRST (before any other imports)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from src.ui.session import init_session_state, reset_log_workflow
from src.ui.navigation import render_bottom_nav
from src.ui.audio_recorder import combined_input
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

def render_planning_chat_state():
    """
    Pre-workout planning with AI chat.
    Shows suggested workout type, adaptive template, and chat interface for modifications.
    """
    st.title("🤖 Plan Your Workout")

    # Initialize planning if needed
    if not st.session_state.workout_session:
        from src.agents.session_graph import initialize_planning_session
        with st.spinner("Getting AI recommendation... 🧠"):
            st.session_state.workout_session = initialize_planning_session()

    session = st.session_state.workout_session

    # Show AI suggestion
    st.success(f"**Suggested:** {session.get('suggested_type', 'Push')}")
    st.caption(session.get('suggestion_reason', 'Based on your weekly split'))

    # Show current template (collapsible)
    with st.expander("📋 Your Plan", expanded=True):
        from src.ui.planning_components import render_template_preview, render_equipment_constraints
        render_template_preview(session.get('planned_template', {}))

        # Show equipment constraints if any
        render_equipment_constraints(session.get('equipment_unavailable'))

        # Show adjustments made
        from src.ui.planning_components import render_adjustment_history
        adjustments = session.get('plan_adjustments', [])
        if adjustments:
            render_adjustment_history(adjustments)

    st.divider()

    # Chat interface for modifications
    from src.ui.planning_components import render_planning_chat_interface
    planning_input = render_planning_chat_interface()

    if planning_input:
        # Process planning chat modification
        from src.agents.session_graph import modify_plan_via_chat
        with st.spinner("Updating plan... 🔄"):
            updated_session = modify_plan_via_chat(st.session_state.workout_session, planning_input)
            st.session_state.workout_session = updated_session
        st.rerun()

    # Start Workout button
    from src.ui.planning_components import render_start_workout_button
    if render_start_workout_button():
        # Lock plan and begin workout
        st.session_state.log_state = 'session_active'
        st.rerun()


def render_ready_state_deprecated():
    """DEPRECATED: Old single-shot mode - to be removed in Phase 6"""
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

    # Force break from any column context with empty container
    st.container()

    # Auto-parse when input is available
    if workout_input:
        try:
            with st.spinner("Understanding your workout... 🧠"):
                workflow_state = start_workout_log(workout_input)

            # Store the raw input for potential editing
            st.session_state.raw_workout_input = workout_input

            # Clear cached transcription
            if 'cached_transcription' in st.session_state:
                del st.session_state.cached_transcription

            st.session_state.log_workflow_state = workflow_state
            st.session_state.log_state = 'preview'
            st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to parse workout: {str(e)}")
            st.caption("Please try again or use the text input below to correct it")


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
            # Reset audio recorder for fresh recording
            if 'audio_recorder_key' not in st.session_state:
                st.session_state.audio_recorder_key = 0
            st.session_state.audio_recorder_key += 1
            reset_log_workflow()
            st.rerun()

    with col4:
        if st.button("❌ Cancel", key="cancel"):
            cancel_workflow()

    # Edit mode - show raw text for editing
    if st.session_state.get('edit_mode'):
        st.divider()
        st.subheader("✏️ Edit Your Workout Text")
        st.caption("Fix the text below and we'll re-parse it")

        # Show the original raw input for editing
        raw_input = st.session_state.get('raw_workout_input', '')
        edited_text = st.text_area(
            "Workout text",
            value=raw_input,
            height=150,
            help="Edit the text and click Apply to re-parse"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply Changes", type="primary", key="apply_changes_btn"):
                try:
                    with st.spinner("Re-parsing your workout... 🧠"):
                        workflow_state = start_workout_log(edited_text)

                    # Update stored raw input
                    st.session_state.raw_workout_input = edited_text
                    st.session_state.log_workflow_state = workflow_state
                    st.session_state.edit_mode = False
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Failed to parse: {str(e)}")

        with col2:
            if st.button("Cancel Edit", key="cancel_edit_btn"):
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
        with st.spinner("Saving your workout... 💾"):
            final_state = continue_workout_log(
                state=st.session_state.log_workflow_state,
                user_choice=choice,
                edit_instructions=edit_instructions
            )

        st.session_state.log_workflow_state = final_state

        if choice == "approve" or (choice == "edit" and final_state.get('saved')):
            st.session_state.log_state = 'saved'
        else:
            # Re-parse if edited
            st.session_state.log_state = 'preview'

        st.session_state.edit_mode = False
        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to save: {str(e)}")
        st.caption("Please try again")


def cancel_workflow():
    """Cancel and reset"""
    reset_log_workflow()
    st.rerun()


# ============================================================================
# Session Mode Functions (NEW)
# ============================================================================

def render_session_start_state():
    """Render session start screen with AI suggestion."""
    from src.ui.session_components import render_session_start
    render_session_start()


def render_session_active_state():
    """Render exercise recording screen for session mode."""
    from src.ui.session_components import render_session_progress

    st.title("🎙️ Record Exercise")

    # Show session progress
    if st.session_state.workout_session:
        render_session_progress(st.session_state.workout_session)

    st.divider()

    # Record exercise input
    workout_input = combined_input()

    # CRITICAL: Force break from column context (Risk Mitigation #1)
    st.container()

    # Auto-parse when input provided
    if workout_input:
        try:
            from src.agents.session_graph import add_exercise_to_session

            with st.spinner("Parsing exercise..."):
                # Parse and add to session
                updated_session = add_exercise_to_session(
                    st.session_state.workout_session,
                    workout_input
                )

            # Store raw input for potential editing
            st.session_state.raw_exercise_input = workout_input

            # Clear cached transcription
            if 'cached_transcription' in st.session_state:
                del st.session_state.cached_transcription

            # Update session state
            st.session_state.workout_session = updated_session

            # Check if parsing succeeded
            if updated_session.get('current_parsed_exercise'):
                # Move to preview state
                st.session_state.log_state = 'session_exercise_preview'
                st.rerun()
            else:
                # Parsing failed - show helpful error
                error_msg = updated_session.get('response', 'Could not parse exercise')
                st.error(f"❌ {error_msg}")

                # Show example if exercise name was missing
                if "exercise name" in error_msg.lower():
                    st.info("💡 **Example:** Say 'Bench press, 3 sets of 10 reps at 135 pounds' or use the text box below")

        except Exception as e:
            st.error(f"❌ Failed to parse exercise: {str(e)}")
            st.caption("Please try again or use the text input below to correct it")

    # Cancel session button
    st.divider()
    if st.button("❌ Cancel Session", key="cancel_session_btn"):
        from src.ui.session import reset_workout_session
        reset_workout_session()
        st.rerun()


def render_session_exercise_preview():
    """Show exercise preview with action buttons."""
    from src.ui.session_components import render_exercise_preview

    st.title("✅ Exercise Added")

    # Show parsed exercise
    session = st.session_state.workout_session
    if session and session.get('current_parsed_exercise'):
        render_exercise_preview(session['current_parsed_exercise'])

    st.divider()

    # Action buttons - CRITICAL: Use container break and direct column attachment
    st.container()  # Force break from any previous column context

    btn_col1, btn_col2 = st.columns(2)

    # Record Next button
    record_next_clicked = btn_col1.button(
        "🎙️ Record Next Exercise",
        type="primary",
        key="record_next_btn",
        use_container_width=True
    )

    # Finish Workout button
    finish_clicked = btn_col2.button(
        "✅ Finish Workout",
        key="finish_workout_btn",
        use_container_width=True
    )

    # Handle button clicks
    if record_next_clicked:
        from src.agents.session_graph import accumulate_exercise

        # Accumulate current exercise
        session['user_action'] = 'add_another'
        updated_session = accumulate_exercise(session)

        # CRITICAL FIX: Clear user_action so next parse doesn't auto-accumulate
        updated_session['user_action'] = None
        updated_session['response'] = None  # Also clear response to avoid confusion

        st.session_state.workout_session = updated_session

        # Clear cached transcription
        if 'cached_transcription' in st.session_state:
            del st.session_state.cached_transcription

        # Reset audio recorder for next exercise
        if 'audio_recorder_key' not in st.session_state:
            st.session_state.audio_recorder_key = 0
        st.session_state.audio_recorder_key += 1

        # Go back to active state
        st.session_state.log_state = 'session_active'
        st.rerun()

    if finish_clicked:
        from src.agents.session_graph import accumulate_exercise

        # Accumulate current exercise first
        session['user_action'] = 'add_another'
        updated_session = accumulate_exercise(session)

        # Clear user_action before transitioning
        updated_session['user_action'] = None

        st.session_state.workout_session = updated_session

        # Move to review state
        st.session_state.log_state = 'session_workout_review'
        st.rerun()


def render_session_workout_review():
    """Review full workout before saving."""
    from src.ui.session_components import render_workout_review

    # Render review
    session = st.session_state.workout_session
    if session:
        render_workout_review(session)

    st.divider()

    # Save button
    if st.button("💾 Save Workout", type="primary", use_container_width=True):
        try:
            from src.agents.session_graph import finish_session

            with st.spinner("Saving workout..."):
                # Finish and save session
                final_session = finish_session(session)

            st.session_state.workout_session = final_session

            if final_session.get('saved'):
                # Success - move to saved state
                st.session_state.log_workflow_state = {
                    'workout_id': final_session.get('workout_id'),
                    'saved': True
                }
                st.session_state.log_state = 'saved'
                st.rerun()
            else:
                st.error(f"❌ {final_session.get('response', 'Failed to save')}")

        except Exception as e:
            st.error(f"❌ Error saving workout: {str(e)}")


# ============================================================================
# Main State Machine
# ============================================================================

if st.session_state.log_state == 'planning_chat':
    render_planning_chat_state()
elif st.session_state.log_state == 'ready':
    # DEPRECATED: Old single-shot mode - redirects to planning
    st.session_state.log_state = 'planning_chat'
    st.rerun()
elif st.session_state.log_state == 'session_active':
    render_session_active_state()
elif st.session_state.log_state == 'session_exercise_preview':
    render_session_exercise_preview()
elif st.session_state.log_state == 'session_workout_review':
    render_session_workout_review()
elif st.session_state.log_state == 'preview':
    render_preview_state()
elif st.session_state.log_state == 'saved':
    render_saved_state()
else:
    # Fallback - reset to planning chat
    st.session_state.log_state = 'planning_chat'
    st.rerun()
