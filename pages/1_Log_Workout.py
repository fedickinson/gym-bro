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

    st.divider()

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

    # Show AI-generated workout summary (after plan, before modify)
    workout_summary = session.get('workout_summary')
    if workout_summary:
        st.divider()
        st.markdown("### 💪 Workout Breakdown")

        # Parse and format the summary with better visual structure
        lines = workout_summary.split('\n')
        focus_statement = None
        exercise_bullets = []
        recovery_note = []

        in_exercises = False
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # First bold line is focus statement
            if line.startswith('**') and not focus_statement:
                focus_statement = line
            # Bullet points are exercises
            elif line.startswith('•'):
                exercise_bullets.append(line)
                in_exercises = True
            # Everything after bullets is recovery
            elif in_exercises and not line.startswith('•'):
                recovery_note.append(line)
            elif not in_exercises and not line.startswith('**'):
                recovery_note.append(line)

        # Render with custom styling
        st.markdown("""
        <style>
        .workout-focus {
            font-size: 1.3rem;
            font-weight: 600;
            color: #4CAF50;
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }
        .workout-focus strong {
            font-weight: 700;
        }
        .exercise-list {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        .exercise-item {
            font-size: 1.1rem;
            line-height: 1.8;
            margin-bottom: 1.2rem;
            padding-left: 0.5rem;
        }
        .exercise-item strong {
            font-weight: 700;
            font-size: 1.15rem;
            color: #FFA726;
        }
        .exercise-item:last-child {
            margin-bottom: 0;
        }
        .recovery-note {
            font-size: 1.05rem;
            line-height: 1.7;
            margin-top: 1.5rem;
            padding: 1rem;
            background: rgba(100, 149, 237, 0.1);
            border-left: 3px solid #6495ED;
            border-radius: 4px;
        }
        .recovery-note strong {
            font-weight: 700;
        }
        </style>
        """, unsafe_allow_html=True)

        # Helper function to convert markdown bold to HTML
        def convert_bold(text):
            import re
            # Replace **text** with <strong>text</strong>
            return re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

        # Render focus statement
        if focus_statement:
            focus_html = convert_bold(focus_statement)
            st.markdown(f'<div class="workout-focus">{focus_html}</div>', unsafe_allow_html=True)

        # Render exercise list
        if exercise_bullets:
            exercises_html = '<div class="exercise-list">'
            for bullet in exercise_bullets:
                # Remove the bullet character and convert markdown
                exercise_text = bullet.replace('•', '').strip()
                exercise_html = convert_bold(exercise_text)
                exercises_html += f'<div class="exercise-item">• {exercise_html}</div>'
            exercises_html += '</div>'
            st.markdown(exercises_html, unsafe_allow_html=True)

        # Render recovery note
        if recovery_note:
            recovery_text = ' '.join(recovery_note)
            recovery_html = '<div class="recovery-note">' + convert_bold(recovery_text) + '</div>'
            st.markdown(recovery_html, unsafe_allow_html=True)

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
        st.session_state.recording_mode = None  # Reset recording mode for first exercise
        st.session_state.log_state = 'session_active'
        st.rerun()


# ============================================================================
# Session Mode Functions
# ============================================================================

def render_session_start_state():
    """Render session start screen with AI suggestion."""
    from src.ui.session_components import render_session_start
    render_session_start()


def render_session_active_state():
    """Render exercise recording screen for session mode."""
    from src.ui.session_components import render_session_progress
    from src.ui.suggestion_components import render_next_suggestion

    st.title("🎙️ Record Exercise")

    # Show session progress
    if st.session_state.workout_session:
        render_session_progress(st.session_state.workout_session)

    st.divider()

    # Check if plan is complete
    session = st.session_state.workout_session
    num_accumulated = len(session.get('accumulated_exercises', []))
    planned_count = len(session.get('planned_template', {}).get('exercises', []))
    plan_is_complete = planned_count > 0 and num_accumulated >= planned_count

    # If plan is complete, offer to finish OR continue
    if plan_is_complete and not st.session_state.get('continue_after_plan'):
        st.success("🎉 You've completed your planned workout!")
        st.caption(f"All {planned_count} exercises done. Great work!")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Finish Workout", key="finish_plan_btn", use_container_width=True, type="primary"):
                # Go straight to review
                st.session_state.log_state = 'session_workout_review'
                st.rerun()

        with col2:
            if st.button("💪 Add More Exercises", key="continue_plan_btn", use_container_width=True):
                # Set flag to continue adding
                st.session_state.continue_after_plan = True
                st.rerun()

        st.divider()
        st.caption("Tip: Additional exercises will be marked as bonus exercises")

    else:
        # Show next exercise suggestion (normal flow)
        next_suggestion = session.get('next_suggestion')

        if next_suggestion and next_suggestion.get('exercise_name'):
            # We have a suggestion - show it
            render_next_suggestion(next_suggestion)
            st.divider()

            # Check if we have complete data for "exact" mode
            suggested_weight = next_suggestion.get('suggested_weight_lbs')
            has_complete_data = suggested_weight is not None

            # Show three-button flow: Primary + Secondary
            st.subheader("How would you like to record?")

            if has_complete_data:
                # Primary button - happy path (only show if we have weight)
                if st.button("✅ Yes, I Did This Exactly", key="did_exact_btn", use_container_width=True, type="primary"):
                    st.session_state.recording_mode = 'exact'
                    st.rerun()

                st.caption("or")
            else:
                # No weight suggested - can't use "exact" mode
                st.info("💡 **Weight not specified** - please tell me what weight you used")

            # Secondary buttons (always available)
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📝 With Modifications", key="did_modified_btn", use_container_width=True, type="primary" if not has_complete_data else "secondary"):
                    st.session_state.recording_mode = 'modified'
                    st.rerun()

            with col2:
                if st.button("🔄 Different Exercise", key="did_different_btn", use_container_width=True):
                    st.session_state.recording_mode = 'different'
                    st.rerun()

        else:
            # No suggestion available - skip straight to 'different' mode
            if st.session_state.recording_mode is None:
                st.session_state.recording_mode = 'different'

    # Show recorder if mode is selected
    if st.session_state.recording_mode:
        st.divider()

        # Handle 'exact' mode - auto-fill from suggestion
        if st.session_state.recording_mode == 'exact' and next_suggestion:
            # Auto-create exercise from suggestion
            suggested_name = next_suggestion.get('exercise_name')
            suggested_sets = next_suggestion.get('target_sets', 3)
            suggested_reps = next_suggestion.get('target_reps', 10)
            suggested_weight = next_suggestion.get('suggested_weight_lbs')

            # Build exercise from suggestion
            sets_data = []
            for i in range(suggested_sets):
                set_dict = {"reps": suggested_reps}
                if suggested_weight:
                    set_dict["weight_lbs"] = suggested_weight
                sets_data.append(set_dict)

            exact_exercise = {
                "name": suggested_name,
                "sets": sets_data
            }

            # Add directly to session
            st.session_state.workout_session['current_parsed_exercise'] = exact_exercise
            st.session_state.recording_mode = None

            # Move to preview
            st.session_state.log_state = 'session_exercise_preview'
            st.rerun()

        # Handle 'modified' and 'different' modes - need user input
        if st.session_state.recording_mode in ['modified', 'different']:
            # Show appropriate prompt based on mode
            if st.session_state.recording_mode == 'modified' and next_suggestion:
                suggested_name = next_suggestion.get('exercise_name')
                st.info(f"💡 Recording **{suggested_name}** - just say the sets, reps, and weights")
                st.caption("Example: '135 for 10, 8, 7' or '3 sets of 10 at 135'")
            else:
                st.info("💡 Describe the full exercise with name, sets, reps, and weight")
                st.caption("Example: 'Dumbbell press, 3 sets of 10 at 50 pounds'")

            # Record exercise input
            workout_input = combined_input()

            # CRITICAL: Force break from column context
            st.container()

            # Auto-parse when input provided
            if workout_input:
                try:
                    from src.agents.session_graph import add_exercise_to_session

                    with st.spinner("Parsing exercise..."):
                        # Build context for parser
                        parse_context = {}
                        if st.session_state.recording_mode == 'modified' and next_suggestion:
                            parse_context['suggested_exercise'] = next_suggestion.get('exercise_name')

                        # Parse and add to session
                        updated_session = add_exercise_to_session(
                            st.session_state.workout_session,
                            workout_input,
                            context=parse_context
                        )

                    # Update session state first
                    st.session_state.workout_session = updated_session

                    # Check if parsing succeeded
                    if updated_session.get('current_parsed_exercise'):
                        # SUCCESS - Clear state and move to preview

                        # Store raw input for potential editing
                        st.session_state.raw_exercise_input = workout_input

                        # Clear cached transcription
                        if 'cached_transcription' in st.session_state:
                            del st.session_state.cached_transcription

                        # Reset recording mode for next exercise
                        st.session_state.recording_mode = None

                        # Move to preview state
                        st.session_state.log_state = 'session_exercise_preview'
                        st.rerun()
                    else:
                        # PARSING FAILED - Keep recording mode active so they can retry
                        error_msg = updated_session.get('response', 'Could not parse exercise')
                        st.error(f"❌ {error_msg}")

                        # Show example if exercise name was missing
                        if "exercise name" in error_msg.lower():
                            st.info("💡 **Example:** Say 'Bench press, 3 sets of 10 reps at 135 pounds'")

                        st.warning("👆 Try again above, or click 'Back to Options' below to choose a different mode")

                except Exception as e:
                    # EXCEPTION - Keep recording mode active
                    st.error(f"❌ Failed to parse exercise: {str(e)}")
                    st.caption("Please try again above or click 'Back to Options' below")

            # Add "Back to Options" button for retry/cancel
            st.divider()
            col1, col2 = st.columns([2, 1])
            with col2:
                if st.button("⬅️ Back to Options", key="back_to_options_btn", use_container_width=True):
                    st.session_state.recording_mode = None
                    # Clear any cached transcription
                    if 'cached_transcription' in st.session_state:
                        del st.session_state.cached_transcription
                    st.rerun()

    # Cancel session button
    st.divider()
    if st.button("❌ Cancel Session", key="cancel_session_btn"):
        from src.ui.session import reset_workout_session
        reset_workout_session()
        # Navigate to home instead of staying on this page
        st.switch_page("app.py")


def _render_deviation_warning(deviation: dict, session: dict):
    """
    Render deviation warning when user goes off-plan.

    Args:
        deviation: Deviation analysis dict
        session: Current session state
    """
    severity = deviation.get('severity', 'none')
    impact = deviation.get('impact_description', 'Deviation detected')
    changes_type = deviation.get('changes_workout_type', False)

    # Show warning based on severity
    if severity == "major_deviation":
        st.warning(f"⚠️ **Off-Plan:** {impact}")

        # If workout type changed, offer to adapt (Phase 4)
        if changes_type:
            st.info("💡 Choose how to proceed:")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔄 Adapt Rest of Plan", key="adapt_plan_btn", use_container_width=True, type="primary"):
                    from src.agents.session_graph import adapt_plan
                    # Adapt the plan to match new direction
                    updated_session = adapt_plan(session)
                    st.session_state.workout_session = updated_session
                    st.success(f"✅ Plan adapted! {updated_session.get('response', '')}")
                    st.rerun()

            with col2:
                if st.button("➡️ Continue with Original", key="continue_original_btn", use_container_width=True):
                    # User chooses to ignore deviation and stick with plan
                    # Clear deviation warning by not showing it again
                    st.info("Continuing with original plan")

    elif severity == "minor_variation":
        st.info(f"ℹ️ **Minor Variation:** {impact}")


def render_session_exercise_preview():
    """Show exercise preview with action buttons."""
    from src.ui.session_components import render_exercise_preview

    st.title("✅ Exercise Added")

    # Show parsed exercise
    session = st.session_state.workout_session
    if session and session.get('current_parsed_exercise'):
        render_exercise_preview(session['current_parsed_exercise'])

    # Phase 3: Show deviation warning if detected
    deviation = session.get('current_deviation') if session else None
    if deviation and deviation.get('is_deviation'):
        _render_deviation_warning(deviation, session)

    st.divider()

    # Action buttons - CRITICAL: Use container break and direct column attachment
    st.container()  # Force break from any previous column context

    # Ask user to confirm before adding
    st.markdown("**Does this look correct?**")

    btn_col1, btn_col2, btn_col3 = st.columns(3)

    # Confirm and Record Next button
    record_next_clicked = btn_col1.button(
        "✅ Yes, Record Next",
        type="primary",
        key="record_next_btn",
        use_container_width=True
    )

    # Finish Workout button
    finish_clicked = btn_col2.button(
        "✅ Yes, Finish",
        key="finish_workout_btn",
        use_container_width=True
    )

    # Redo Recording button
    redo_clicked = btn_col3.button(
        "❌ No, Redo",
        key="redo_recording_btn",
        use_container_width=True
    )

    # Handle button clicks
    if record_next_clicked:
        from src.agents.session_graph import accumulate_exercise, refresh_next_suggestion

        # Accumulate current exercise
        session['user_action'] = 'add_another'
        updated_session = accumulate_exercise(session)

        # CRITICAL FIX: Clear user_action so next parse doesn't auto-accumulate
        updated_session['user_action'] = None
        updated_session['response'] = None  # Also clear response to avoid confusion

        # Phase 2: Refresh next suggestion after accumulating
        updated_session = refresh_next_suggestion(updated_session)

        st.session_state.workout_session = updated_session

        # Clear cached transcription
        if 'cached_transcription' in st.session_state:
            del st.session_state.cached_transcription

        # Reset audio recorder for next exercise
        if 'audio_recorder_key' not in st.session_state:
            st.session_state.audio_recorder_key = 0
        st.session_state.audio_recorder_key += 1

        # Reset recording mode so user sees button options again
        st.session_state.recording_mode = None

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

    if redo_clicked:
        # User doesn't like the parsed result - let them redo

        # Clear the current parsed exercise (don't add it)
        session['current_parsed_exercise'] = None
        st.session_state.workout_session = session

        # Clear cached transcription
        if 'cached_transcription' in st.session_state:
            del st.session_state.cached_transcription

        # Reset audio recorder
        if 'audio_recorder_key' not in st.session_state:
            st.session_state.audio_recorder_key = 0
        st.session_state.audio_recorder_key += 1

        # Reset recording mode so they see button options again
        st.session_state.recording_mode = None

        # Go back to active state to record again
        st.session_state.log_state = 'session_active'
        st.rerun()


def render_session_workout_review():
    """Review full workout before saving."""
    from src.ui.session_components import render_workout_review

    # Render review
    session = st.session_state.workout_session
    if session:
        render_workout_review(session)

    st.divider()

    # Save and cancel buttons
    col1, col2 = st.columns([2, 1])

    with col1:
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

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            from src.ui.session import reset_workout_session
            reset_workout_session()
            # Navigate to home instead of staying on this page
            st.switch_page("app.py")


# ============================================================================
# Main State Machine
# ============================================================================

if st.session_state.log_state == 'planning_chat':
    render_planning_chat_state()
elif st.session_state.log_state in ['ready', 'preview']:
    # DEPRECATED: Old single-shot mode - redirect to session mode
    st.session_state.log_state = 'planning_chat'
    st.rerun()
elif st.session_state.log_state == 'saved':
    # Show saved confirmation (shared between old and new modes)
    st.balloons()
    st.success("✅ Workout Saved!")
    st.title("Great job! 💪")

    # Show what's next
    st.divider()
    st.subheader("What's Next?")

    try:
        suggestion = suggest_next_workout.invoke({})
        st.info(f"**Suggested:** {suggestion.get('suggested_type', 'Unknown')}")
        st.write(suggestion.get('reason', ''))
    except:
        st.caption("Keep up the great work!")

    st.divider()

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

elif st.session_state.log_state == 'session_active':
    render_session_active_state()
elif st.session_state.log_state == 'session_exercise_preview':
    render_session_exercise_preview()
elif st.session_state.log_state == 'session_workout_review':
    render_session_workout_review()
else:
    # Fallback - reset to planning chat
    st.session_state.log_state = 'planning_chat'
    st.rerun()
