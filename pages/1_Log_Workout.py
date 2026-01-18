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
from src.ui.shared_components import render_sidebar
from src.ui.audio_recorder import combined_input
from src.agents.log_graph import start_workout_log, continue_workout_log
from src.tools.recommend_tools import suggest_next_workout, get_workout_template
from src.ui.styles import get_global_styles

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

# ============================================================================
# Sidebar Navigation & Stats
# ============================================================================

with st.sidebar:
    render_sidebar(current_page="Log")

# Apply global design system styles
st.markdown(get_global_styles(), unsafe_allow_html=True)

# ============================================================================
# State Machine Functions
# ============================================================================

def _render_workout_progress():
    """
    Helper function to render workout progress indicator across all states.

    Maps state machine to user-friendly steps:
    - planning_chat → "Plan"
    - session_exercise_intro/active → "Exercise N" (where N is current exercise number)
    - session_workout_review → "Review"
    - saved → Complete
    """
    from src.ui.shared_components import render_workflow_progress

    session = st.session_state.workout_session
    state = st.session_state.log_state

    # Don't show progress on saved state (shows balloons instead)
    if state == 'saved':
        return

    # Build step list based on planned exercises
    steps = ["Plan"]

    if session and session.get('planned_template'):
        exercises = session['planned_template'].get('exercises', [])
        for i in range(len(exercises)):
            steps.append(f"Ex {i+1}")

    steps.append("Review")

    # Determine current step index
    if state == 'planning_chat':
        current_step = 0
    elif state in ['session_exercise_intro', 'session_active', 'session_exercise_preview']:
        # Current exercise index
        current_index = len(session.get('accumulated_exercises', [])) if session else 0
        current_step = current_index + 1  # +1 because step 0 is "Plan"
    elif state == 'session_workout_review':
        current_step = len(steps) - 1  # Last step (Review)
    else:
        current_step = 0

    # Render progress indicator (compact labels for mobile)
    render_workflow_progress(steps, current_step, show_labels=False)


def render_planning_chat_state():
    """
    Pre-workout planning with AI chat.
    Shows suggested workout type, adaptive template, and chat interface for modifications.
    """
    # Show workout progress
    _render_workout_progress()

    st.title("🤖 Plan Your Workout")

    # Initialize planning if needed
    if not st.session_state.workout_session:
        from src.agents.session_graph import initialize_planning_session
        with st.spinner("Getting AI recommendation... 🧠"):
            st.session_state.workout_session = initialize_planning_session()

    session = st.session_state.workout_session

    # === Weekly Progress Summary (COMPACT for mobile) ===
    from src.ui.planning_components import render_weekly_progress_summary
    render_weekly_progress_summary(compact=True)

    st.divider()

    # === NEW: Combo Mode Detection ===
    combo_mode = session.get('combo_mode', False)
    catch_up_combos = session.get('catch_up_combos', [])

    if combo_mode and catch_up_combos:
        # COMBO MODE: Show structured combos
        from src.ui.planning_components import render_catch_up_suggestion
        render_catch_up_suggestion(catch_up_combos)

        st.divider()

        # Show ALL templates for today's combo
        planned_templates = session.get('planned_templates', [])

        if planned_templates:
            st.markdown("### 📋 Today's Workouts")

            for i, template_info in enumerate(planned_templates):
                workout_type = template_info["type"]
                template = template_info["template"]
                duration = template_info.get("duration_min", 35)

                with st.expander(
                    f"**{i+1}. {workout_type}** (~{duration} min)",
                    expanded=(i == 0)  # First template expanded by default
                ):
                    from src.ui.planning_components import render_template_preview
                    render_template_preview(template, compact=True)

    elif session.get('catch_up_mode', False):
        # OLD-STYLE CATCH-UP (flat list, no combos) - shouldn't happen with new code
        from src.ui.planning_components import render_catch_up_suggestion
        catch_up_combos_fallback = [
            {
                "day": "Today",
                "types": session.get('catch_up_workouts', []),
                "duration_min": len(session.get('catch_up_workouts', [])) * 35,
                "rest_between_min": 5
            }
        ]
        render_catch_up_suggestion(catch_up_combos_fallback)

        st.divider()

        # Show single template
        with st.expander("📋 View Your Plan (tap to expand)", expanded=False):
            from src.ui.planning_components import render_template_preview
            render_template_preview(session.get('planned_template', {}), compact=True)

    else:
        # NORMAL MODE - single suggestion
        st.success(f"**Suggested:** {session.get('suggested_type', 'Push')}")
        st.caption(session.get('suggestion_reason', 'Based on your weekly split'))

        st.divider()

        # Show current template (collapsible, COLLAPSED by default for mobile)
        with st.expander("📋 View Your Plan (tap to expand)", expanded=False):
            from src.ui.planning_components import render_template_preview, render_equipment_constraints
            render_template_preview(session.get('planned_template', {}), compact=True)

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
        st.session_state.log_state = 'session_exercise_intro'  # Show intro for first exercise
        st.rerun()


# ============================================================================
# Session Mode Functions
# ============================================================================

# DEPRECATED: render_session_start_state() removed 2025-12-24
# This state is never reached - all sessions start via planning_chat state
# which uses initialize_planning_session() for proper type tracking


def render_multi_set_choice_dialog(parsed_sets: list[dict]) -> str | None:
    """
    Show dialog when multiple sets detected in user's recording.

    Returns: "first_only" | "all_sets" | "cancel" | None
    """
    st.warning(f"📊 **{len(parsed_sets)} sets detected in your recording**")

    # Show what was detected
    sets_preview = ", ".join([f"{s.get('reps')} reps" for s in parsed_sets[:3]])
    if len(parsed_sets) > 3:
        sets_preview += f" + {len(parsed_sets) - 3} more"
    st.caption(f"Detected: {sets_preview}")

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        first_set = parsed_sets[0]
        weight = first_set.get('weight_lbs')
        reps = first_set.get('reps')
        label = f"📝 First Set Only\n{reps} reps"
        if weight:
            label += f" @ {weight:.0f} lbs"

        if st.button(label, key="multi_choice_first", use_container_width=True):
            return "first_only"

    with col2:
        if st.button(
            f"✅ All {len(parsed_sets)} Sets\nFinish Exercise",
            key="multi_choice_all",
            use_container_width=True,
            type="primary"
        ):
            return "all_sets"

    with col3:
        if st.button(
            "❌ Cancel\nRe-record",
            key="multi_choice_cancel",
            use_container_width=True
        ):
            return "cancel"

    return None


def render_early_finish_confirmation(
    planned_sets: int,
    completed_sets: int,
    confirm_yes_key: str,
    confirm_no_key: str,
    on_confirm_state: str = 'session_exercise_complete'
) -> None:
    """
    Render confirmation dialog for finishing exercise early.

    Args:
        planned_sets: Number of sets originally planned
        completed_sets: Number of sets actually completed
        confirm_yes_key: Unique key for "Yes" button
        confirm_no_key: Unique key for "No" button
        on_confirm_state: State to transition to when confirmed
    """
    st.warning(f"⚠️ **Finish early?**")
    st.caption(f"You planned {planned_sets} sets but completed {completed_sets}.")

    confirm_col1, confirm_col2 = st.columns(2)

    with confirm_col1:
        if st.button("Yes, I'm Done", key=confirm_yes_key, use_container_width=True, type="primary"):
            # Clear confirmation flags
            if 'confirm_early_finish_active' in st.session_state:
                st.session_state.confirm_early_finish_active = False
            if 'confirm_early_finish_preview' in st.session_state:
                st.session_state.confirm_early_finish_preview = False

            # Clear timer
            if 'rest_start_time' in st.session_state:
                del st.session_state.rest_start_time
            if 'rest_duration' in st.session_state:
                del st.session_state.rest_duration

            # Transition to next state
            st.session_state.log_state = on_confirm_state
            print(f"✅ EARLY FINISH CONFIRMED ({completed_sets}/{planned_sets} sets)")
            st.rerun()

    with confirm_col2:
        if st.button("No, Continue", key=confirm_no_key, use_container_width=True):
            # Clear confirmation flags
            if 'confirm_early_finish_active' in st.session_state:
                st.session_state.confirm_early_finish_active = False
            if 'confirm_early_finish_preview' in st.session_state:
                st.session_state.confirm_early_finish_preview = False
            st.rerun()


def render_session_exercise_intro():
    """
    Render exercise introduction screen before Set 1.

    Shows:
    - Exercise name prominently
    - Exercise info (muscle groups, equipment, category)
    - Plan details (sets, reps, weight, rest)
    - Beginner guidance (if first time doing this exercise)
    - Options: Start / Different / Skip / Cancel
    """
    from src.ui.session_components import render_session_progress
    from src.agents.session_graph import generate_next_set_suggestion
    from src.agents.suggestion_engine import get_exercise_info

    # Show workout progress
    _render_workout_progress()

    st.title("💪 Next Exercise")

    session = st.session_state.workout_session

    # Show session progress
    if session:
        render_session_progress(session)

    st.divider()

    # Get suggestion for Set 1 of this exercise
    set_suggestion = generate_next_set_suggestion(session)

    if not set_suggestion:
        # No more exercises
        st.warning("No more exercises in your plan!")
        if st.button("Finish Workout", type="primary"):
            st.session_state.log_state = 'session_workout_review'
            st.rerun()
        return

    # Extract exercise details
    exercise_name = set_suggestion.get('exercise_name', 'Unknown')
    target_reps = set_suggestion.get('target_reps', 10)
    suggested_weight = set_suggestion.get('suggested_weight_lbs')
    rest_seconds = set_suggestion.get('rest_seconds', 90)

    # Get target_sets from planned template
    current_index = session.get('current_exercise_index', 0)
    planned_exercises = session.get('planned_template', {}).get('exercises', [])
    if current_index < len(planned_exercises):
        target_sets = planned_exercises[current_index].get('target_sets', 4)
    else:
        target_sets = 4

    # Get exercise information from catalog
    exercise_info = get_exercise_info(exercise_name)

    # Large exercise name display (using green theme)
    st.markdown(f"""
    <div class="exercise-banner">
        <div class="exercise-name">
            {exercise_info.get('canonical_name', exercise_name)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Exercise information (muscle groups, equipment, category) - Phase 2: larger text
    if exercise_info.get('found_in_catalog'):
        st.markdown("### 🎯 Exercise Details")

        info_col1, info_col2 = st.columns(2)

        with info_col1:
            muscle_groups = exercise_info.get('muscle_groups', [])
            if muscle_groups:
                st.markdown("**Targets:**")
                for muscle in muscle_groups:
                    st.markdown(f"• {muscle}")

        with info_col2:
            equipment = exercise_info.get('equipment', [])
            category = exercise_info.get('category', '').title()

            if equipment:
                st.markdown("**Equipment:**")
                st.markdown(", ".join(equipment))

            if category:
                st.markdown("**Type:**")
                st.markdown(f"{category}")

        # First-time beginner guidance
        if exercise_info.get('is_first_time'):
            weight_reasoning = exercise_info.get('weight_reasoning', '')
            if weight_reasoning:
                st.info(f"💡 **First time?** {weight_reasoning}")

        st.divider()

    # Plan summary
    st.subheader("📋 Workout Plan")

    plan_col1, plan_col2 = st.columns(2)

    with plan_col1:
        st.metric("Sets", f"{target_sets} sets")
        st.metric("Reps per Set", f"{target_reps} reps")

    with plan_col2:
        if suggested_weight:
            st.metric("Suggested Weight", f"{suggested_weight:.0f} lbs")
        else:
            st.metric("Weight", "Choose your weight")
        st.metric("Rest Between Sets", f"{rest_seconds}s")

    st.divider()

    # Primary action: Start Exercise
    if st.button(
        "▶️  Start Exercise",
        key="start_exercise_btn",
        use_container_width=True,
        type="primary",
        help="Begin recording Set 1"
    ):
        # Transition to session_active for Set 1 recording
        st.session_state.log_state = 'session_active'
        print(f"▶️ STARTING EXERCISE: {exercise_name}")
        st.rerun()

    st.divider()
    st.caption("Other Options:")

    # Secondary options (3 columns)
    opt_col1, opt_col2, opt_col3 = st.columns(3)

    with opt_col1:
        if st.button("🔄 Different Exercise", key="intro_different_btn", use_container_width=True):
            # Go to different exercise mode
            st.session_state.recording_mode = 'different'
            st.session_state.log_state = 'session_active'
            print(f"🔄 CHOOSING DIFFERENT EXERCISE (was: {exercise_name})")
            st.rerun()

    with opt_col2:
        if st.button("⏭️ Skip Exercise", key="intro_skip_btn", use_container_width=True):
            # Ask for confirmation
            st.session_state.confirm_skip_exercise = True
            st.rerun()

    with opt_col3:
        if st.button("❌ Cancel Session", key="intro_cancel_btn", use_container_width=True):
            # Cancel the entire workout
            if st.session_state.get('confirm_cancel_session'):
                # Confirmed - actually cancel
                st.session_state.workout_session = None
                st.session_state.log_state = 'idle'
                st.session_state.confirm_cancel_session = False
                print("❌ SESSION CANCELLED")
                st.rerun()
            else:
                # Ask for confirmation
                st.session_state.confirm_cancel_session = True
                st.rerun()

    # Show skip confirmation if flag is set
    if st.session_state.get('confirm_skip_exercise'):
        st.divider()
        st.warning(f"⚠️ **Skip {exercise_name}?**")
        st.caption("This exercise will not be logged.")

        skip_col1, skip_col2 = st.columns(2)
        with skip_col1:
            if st.button("Yes, Skip It", key="confirm_skip_yes", type="primary", use_container_width=True):
                # Skip this exercise and show intro for next
                print(f"⏭️ SKIP EXERCISE (from intro): {exercise_name}")

                # Clear state
                st.session_state.workout_session['in_progress_exercise'] = None
                st.session_state.workout_session['current_set_number'] = 0
                st.session_state.workout_session['target_sets'] = 0
                st.session_state.workout_session['current_set_suggestion'] = None
                st.session_state.workout_session['next_suggestion'] = None

                # Increment exercise index
                current_index = session.get('current_exercise_index', 0)
                st.session_state.workout_session['current_exercise_index'] = current_index + 1

                # Clear confirmation flag
                st.session_state.confirm_skip_exercise = False

                print(f"   Moving to exercise index {current_index + 1}")
                # Stay in session_exercise_intro to show next exercise
                st.rerun()
        with skip_col2:
            if st.button("No, Do This Exercise", key="confirm_skip_no", use_container_width=True):
                st.session_state.confirm_skip_exercise = False
                st.rerun()

    # Show cancel confirmation if flag is set
    if st.session_state.get('confirm_cancel_session'):
        st.divider()
        st.warning("⚠️ **Cancel entire workout session?**")
        st.caption("All progress will be lost.")

        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button("Yes, Cancel Session", key="confirm_cancel_yes", type="primary", use_container_width=True):
                st.session_state.workout_session = None
                st.session_state.log_state = 'idle'
                st.session_state.confirm_cancel_session = False
                st.rerun()
        with conf_col2:
            if st.button("No, Continue", key="confirm_cancel_no", use_container_width=True):
                st.session_state.confirm_cancel_session = False
                st.rerun()


def render_session_active_state():
    """Render SET recording screen for session mode (set-by-set flow)."""
    from src.ui.session_components import render_session_progress
    from src.ui.suggestion_components import render_next_suggestion
    from src.agents.session_graph import generate_next_set_suggestion

    # Show workout progress
    _render_workout_progress()

    st.title("🎙️ Record Set")

    # Show session progress
    if st.session_state.workout_session:
        render_session_progress(st.session_state.workout_session)

    st.divider()

    # Check if plan is complete
    session = st.session_state.workout_session
    num_accumulated = len(session.get('accumulated_exercises', []))
    planned_count = len(session.get('planned_template', {}).get('exercises', []))
    plan_is_complete = planned_count > 0 and num_accumulated >= planned_count

    # Generate set suggestion for this specific set
    set_suggestion = generate_next_set_suggestion(session)

    # DEBUG: Log suggestion details
    if set_suggestion:
        print(f"🟢 Generated suggestion for: {set_suggestion.get('exercise_name')} - Set {set_suggestion.get('set_number')}")
        print(f"   Exercise index: {session.get('current_exercise_index')}")
        print(f"   In progress: {session.get('in_progress_exercise', {}).get('name') if session.get('in_progress_exercise') else 'None'}")

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
        # Show next SET suggestion (set-by-set flow)
        if set_suggestion:
            # We have a set suggestion - show it prominently
            exercise_name = set_suggestion.get('exercise_name', 'Unknown')
            set_number = set_suggestion.get('set_number', 1)
            target_reps = set_suggestion.get('target_reps', 10)
            suggested_weight = set_suggestion.get('suggested_weight_lbs')
            rest_seconds = set_suggestion.get('rest_seconds', 90)

            # Check if this is a new exercise or continuing set
            in_progress = session.get('in_progress_exercise')
            target_sets = session.get('target_sets', 0)

            # Show set header
            st.success(f"🎯 **{exercise_name}**")

            # Show set number prominently (LARGE for gym visibility)
            if target_sets > 0:
                st.markdown(f'<div class="set-number-display">SET {set_number} OF {target_sets}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="set-number-display">SET {set_number}</div>', unsafe_allow_html=True)

            # Show target for this specific set - Phase 2: larger, more prominent
            if suggested_weight:
                st.markdown(f'<div class="set-target">Target: {target_reps} reps @ {suggested_weight:.0f} lbs</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="set-target">Target: {target_reps} reps (choose your weight)</div>', unsafe_allow_html=True)

            st.caption(f"Rest after: {rest_seconds} seconds")

            # Check if we have complete data for "exact" mode
            has_complete_data = suggested_weight is not None

            st.divider()
            st.subheader("Record What You Did")
            st.caption("Complete this set, then record your results:")

            # Always show recording interface - let user choose after doing set
            if st.session_state.recording_mode is None:
                if has_complete_data:
                    # Primary button - happy path (only show if we have weight)
                    if st.button("✅ I Did This Set As Suggested", key="did_exact_btn", use_container_width=True, type="primary"):
                        st.session_state.recording_mode = 'exact'
                        st.session_state.set_suggestion_cache = set_suggestion  # Cache for exact mode
                        st.rerun()

                    st.caption("or tell me what you actually did:")
                else:
                    # No weight suggested - can't use "exact" mode
                    st.caption("Tell me what you did for this set:")

                # Secondary buttons (always available)
                # Use 3 columns for Set 1, 2 columns for later sets
                if set_number == 1:
                    col1, col2, col3 = st.columns(3)
                else:
                    col1, col2 = st.columns(2)

                with col1:
                    if st.button("🎙️ Record This Set", key="did_modified_btn", use_container_width=True, type="primary" if not has_complete_data else "secondary"):
                        st.session_state.recording_mode = 'modified'
                        st.session_state.set_suggestion_cache = set_suggestion  # Cache for modified mode
                        st.rerun()

                with col2:
                    # Only show "Different Exercise" if this is the first set
                    if set_number == 1:
                        if st.button("🔄 Different Exercise", key="did_different_btn", use_container_width=True):
                            st.session_state.recording_mode = 'different'
                            st.rerun()
                    else:
                        # Mid-exercise - offer to finish early with confirmation
                        if st.session_state.get('confirm_early_finish_active'):
                            # Show confirmation dialog
                            render_early_finish_confirmation(
                                planned_sets=target_sets,
                                completed_sets=set_number - 1,  # -1 because we haven't done this set yet
                                confirm_yes_key="confirm_active_yes",
                                confirm_no_key="confirm_active_no"
                            )
                        else:
                            # Show initial finish button
                            finish_key = f"finish_early_btn_{set_number}"
                            if st.button("✅ Finish Exercise", key=finish_key, use_container_width=True):
                                # DEBUG
                                print(f"🔵 FINISH EXERCISE CLICKED (Set {set_number})")
                                print(f"   Current state: {st.session_state.log_state}")
                                print(f"   Current set: {session.get('current_set_number')}/{session.get('target_sets')}")
                                print(f"   In progress exercise: {session.get('in_progress_exercise', {}).get('name')}")

                                # Set confirmation flag
                                st.session_state.confirm_early_finish_active = True
                                st.rerun()

                # Skip Exercise button (only on Set 1)
                if set_number == 1:
                    with col3:
                        if st.button("⏭️ Skip Exercise", key="skip_exercise_btn", use_container_width=True):
                            # Ask for confirmation
                            st.session_state.confirm_skip_exercise_active = True
                            st.rerun()

        else:
            # No suggestion available - skip straight to 'different' mode
            st.subheader("Record What You Did")
            if st.session_state.recording_mode is None:
                st.session_state.recording_mode = 'different'

    # Show recorder if mode is selected
    if st.session_state.recording_mode:
        st.divider()

        # Handle 'exact' mode - auto-create single set from suggestion
        if st.session_state.recording_mode == 'exact':
            cached_suggestion = st.session_state.get('set_suggestion_cache', {})
            if cached_suggestion:
                # Auto-create SINGLE set from suggestion
                suggested_reps = cached_suggestion.get('target_reps', 10)
                suggested_weight = cached_suggestion.get('suggested_weight_lbs')
                set_number = cached_suggestion.get('set_number', 1)
                exercise_name = cached_suggestion.get('exercise_name')

                # Build single set
                set_data = {"reps": suggested_reps}
                if suggested_weight:
                    set_data["weight_lbs"] = suggested_weight

                # Update or create in_progress_exercise
                in_progress = session.get('in_progress_exercise')
                if in_progress is None:
                    # First set of new exercise - initialize in_progress_exercise
                    # Get target sets from next_suggestion or default
                    next_sug = session.get('next_suggestion') or {}
                    target_sets = next_sug.get('target_sets', 4)

                    in_progress = {
                        "name": exercise_name,
                        "sets": [set_data],
                        "target_sets": target_sets,
                        "target_reps": suggested_reps,
                        "suggested_weight_lbs": suggested_weight,
                        "rest_seconds": cached_suggestion.get('rest_seconds', 90)
                    }

                    # Update session state
                    st.session_state.workout_session['in_progress_exercise'] = in_progress
                    st.session_state.workout_session['current_exercise_name'] = exercise_name
                    st.session_state.workout_session['target_sets'] = target_sets
                    st.session_state.workout_session['current_set_number'] = 1
                    st.session_state.workout_session['current_exercise_sets_completed'] = [set_data]
                else:
                    # Add set to existing in_progress_exercise
                    in_progress['sets'].append(set_data)
                    st.session_state.workout_session['in_progress_exercise'] = in_progress
                    st.session_state.workout_session['current_set_number'] = set_number
                    st.session_state.workout_session['current_exercise_sets_completed'].append(set_data)

                # Clear recording mode
                st.session_state.recording_mode = None
                if 'set_suggestion_cache' in st.session_state:
                    del st.session_state.set_suggestion_cache

                # Move to set preview state
                st.session_state.log_state = 'session_set_preview'
                st.rerun()

        # Handle 'modified' and 'different' modes - need user input
        if st.session_state.recording_mode in ['modified', 'different']:
            # Get cached suggestion for context
            cached_suggestion = st.session_state.get('set_suggestion_cache', {})

            # Show appropriate prompt based on mode
            if st.session_state.recording_mode == 'modified' and cached_suggestion:
                suggested_name = cached_suggestion.get('exercise_name')
                st.info(f"💡 Recording **{suggested_name}** - just say the weight and reps for THIS set")
                st.caption("Example: '135 for 10' or '10 reps at 135'")
            else:
                st.info("💡 Describe the exercise and this set")
                st.caption("Example: 'Dumbbell press, 135 for 10'")

            # Record exercise input
            workout_input = combined_input()

            # CRITICAL: Force break from column context
            st.container()

            # Auto-parse when input provided
            if workout_input:
                try:
                    from src.agents.session_graph import add_exercise_to_session

                    with st.spinner("Parsing set..."):
                        # Build context for parser
                        parse_context = {}
                        if st.session_state.recording_mode == 'modified' and cached_suggestion:
                            parse_context['suggested_exercise'] = cached_suggestion.get('exercise_name')

                        # Parse the input (might get multiple sets, we'll take first)
                        updated_session = add_exercise_to_session(
                            st.session_state.workout_session,
                            workout_input,
                            context=parse_context
                        )

                    # Update session state first
                    st.session_state.workout_session = updated_session

                    # Check if parsing succeeded
                    if updated_session.get('current_parsed_exercise'):
                        # SUCCESS - Check for multiple sets
                        parsed_exercise = updated_session['current_parsed_exercise']
                        exercise_name = parsed_exercise.get('name')
                        all_sets = parsed_exercise.get('sets', [])

                        if not all_sets:
                            st.error("❌ No sets found in your recording")
                            st.caption("Please try again above")
                        elif len(all_sets) > 1:
                            # MULTI-SET DETECTED - Show dialog
                            st.divider()

                            # Store parsed data in session state for dialog handling
                            if 'multi_set_pending' not in st.session_state:
                                st.session_state.multi_set_pending = {
                                    'exercise_name': exercise_name,
                                    'all_sets': all_sets,
                                    'cached_suggestion': cached_suggestion
                                }

                            # Show dialog and get user choice
                            user_choice = render_multi_set_choice_dialog(all_sets)

                            if user_choice == "first_only":
                                # Take first set only
                                first_set = all_sets[0]

                                # Update or create in_progress_exercise
                                in_progress = session.get('in_progress_exercise')
                                if in_progress is None:
                                    next_sug = session.get('next_suggestion') or {}
                                    target_sets = next_sug.get('target_sets', 4)

                                    in_progress = {
                                        "name": exercise_name,
                                        "sets": [first_set],
                                        "target_sets": target_sets,
                                        "target_reps": first_set.get('reps', 10),
                                        "suggested_weight_lbs": first_set.get('weight_lbs'),
                                        "rest_seconds": cached_suggestion.get('rest_seconds', 90) if cached_suggestion else 90
                                    }

                                    st.session_state.workout_session['in_progress_exercise'] = in_progress
                                    st.session_state.workout_session['current_exercise_name'] = exercise_name
                                    st.session_state.workout_session['target_sets'] = target_sets
                                    st.session_state.workout_session['current_set_number'] = 1
                                    st.session_state.workout_session['current_exercise_sets_completed'] = [first_set]
                                else:
                                    in_progress['sets'].append(first_set)
                                    current_set_num = len(in_progress['sets'])
                                    st.session_state.workout_session['in_progress_exercise'] = in_progress
                                    st.session_state.workout_session['current_set_number'] = current_set_num
                                    st.session_state.workout_session['current_exercise_sets_completed'].append(first_set)

                                # Clear state
                                if 'cached_transcription' in st.session_state:
                                    del st.session_state.cached_transcription
                                if 'set_suggestion_cache' in st.session_state:
                                    del st.session_state.set_suggestion_cache
                                if 'multi_set_pending' in st.session_state:
                                    del st.session_state.multi_set_pending

                                st.session_state.recording_mode = None
                                st.session_state.log_state = 'session_set_preview'
                                st.rerun()

                            elif user_choice == "all_sets":
                                # Record all sets and finish exercise
                                in_progress = session.get('in_progress_exercise')
                                if in_progress is None:
                                    # Create new exercise with all sets
                                    in_progress = {
                                        "name": exercise_name,
                                        "sets": all_sets,
                                        "target_sets": len(all_sets),
                                        "target_reps": all_sets[0].get('reps', 10),
                                        "suggested_weight_lbs": all_sets[0].get('weight_lbs'),
                                        "rest_seconds": cached_suggestion.get('rest_seconds', 90) if cached_suggestion else 90
                                    }

                                    st.session_state.workout_session['in_progress_exercise'] = in_progress
                                    st.session_state.workout_session['current_exercise_name'] = exercise_name
                                    st.session_state.workout_session['target_sets'] = len(all_sets)
                                    st.session_state.workout_session['current_set_number'] = len(all_sets)
                                    st.session_state.workout_session['current_exercise_sets_completed'] = all_sets
                                else:
                                    # Add all sets to existing exercise
                                    in_progress['sets'].extend(all_sets)
                                    st.session_state.workout_session['in_progress_exercise'] = in_progress
                                    st.session_state.workout_session['current_set_number'] = len(in_progress['sets'])
                                    st.session_state.workout_session['current_exercise_sets_completed'].extend(all_sets)
                                    st.session_state.workout_session['target_sets'] = len(in_progress['sets'])

                                # Clear state
                                if 'cached_transcription' in st.session_state:
                                    del st.session_state.cached_transcription
                                if 'set_suggestion_cache' in st.session_state:
                                    del st.session_state.set_suggestion_cache
                                if 'multi_set_pending' in st.session_state:
                                    del st.session_state.multi_set_pending

                                st.session_state.recording_mode = None
                                # Go straight to exercise complete
                                st.session_state.log_state = 'session_exercise_complete'
                                st.rerun()

                            elif user_choice == "cancel":
                                # Cancel and let them re-record
                                if 'multi_set_pending' in st.session_state:
                                    del st.session_state.multi_set_pending
                                if 'cached_transcription' in st.session_state:
                                    del st.session_state.cached_transcription
                                st.toast("Recording cancelled - try again", icon="ℹ️")
                                st.rerun()

                        else:
                            # Single set - normal flow
                            first_set = all_sets[0]

                            # Update or create in_progress_exercise
                            in_progress = session.get('in_progress_exercise')
                            if in_progress is None:
                                # First set of new exercise
                                next_sug = session.get('next_suggestion') or {}
                                target_sets = next_sug.get('target_sets', 4)

                                in_progress = {
                                    "name": exercise_name,
                                    "sets": [first_set],
                                    "target_sets": target_sets,
                                    "target_reps": first_set.get('reps', 10),
                                    "suggested_weight_lbs": first_set.get('weight_lbs'),
                                    "rest_seconds": cached_suggestion.get('rest_seconds', 90) if cached_suggestion else 90
                                }

                                st.session_state.workout_session['in_progress_exercise'] = in_progress
                                st.session_state.workout_session['current_exercise_name'] = exercise_name
                                st.session_state.workout_session['target_sets'] = target_sets
                                st.session_state.workout_session['current_set_number'] = 1
                                st.session_state.workout_session['current_exercise_sets_completed'] = [first_set]
                            else:
                                # Add to existing exercise
                                in_progress['sets'].append(first_set)
                                current_set_num = len(in_progress['sets'])
                                st.session_state.workout_session['in_progress_exercise'] = in_progress
                                st.session_state.workout_session['current_set_number'] = current_set_num
                                st.session_state.workout_session['current_exercise_sets_completed'].append(first_set)

                            # Clear state
                            if 'cached_transcription' in st.session_state:
                                del st.session_state.cached_transcription
                            if 'set_suggestion_cache' in st.session_state:
                                del st.session_state.set_suggestion_cache

                            st.session_state.recording_mode = None

                            # Move to set preview
                            st.session_state.log_state = 'session_set_preview'
                            st.rerun()

                    else:
                        # PARSING FAILED
                        error_msg = updated_session.get('response', 'Could not parse set')
                        st.error(f"❌ {error_msg}")

                        if "exercise name" in error_msg.lower():
                            st.info("💡 **Example:** Say 'Bench press, 135 for 10'")

                        st.warning("👆 Try again above, or click 'Back to Options' below")

                except Exception as e:
                    st.error(f"❌ Failed to parse set: {str(e)}")
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

    # Show skip exercise confirmation if flag is set
    if st.session_state.get('confirm_skip_exercise_active'):
        st.divider()

        # Get current exercise name for the confirmation message
        session = st.session_state.workout_session
        set_suggestion = generate_next_set_suggestion(session)
        exercise_name = set_suggestion.get('exercise_name', 'this exercise') if set_suggestion else 'this exercise'

        st.warning(f"⚠️ **Skip {exercise_name}?**")
        st.caption("This exercise will not be logged.")

        skip_col1, skip_col2 = st.columns(2)
        with skip_col1:
            if st.button("Yes, Skip It", key="confirm_skip_active_yes", type="primary", use_container_width=True):
                # Skip this exercise entirely and move to next
                print(f"⏭️ SKIP EXERCISE: {exercise_name}")

                # Clear any in-progress exercise state
                st.session_state.workout_session['in_progress_exercise'] = None
                st.session_state.workout_session['current_set_number'] = 0
                st.session_state.workout_session['target_sets'] = 0
                st.session_state.workout_session['current_set_suggestion'] = None
                st.session_state.workout_session['next_suggestion'] = None  # Clear AI suggestion cache

                # Increment exercise index to move to next exercise
                current_index = session.get('current_exercise_index', 0)
                st.session_state.workout_session['current_exercise_index'] = current_index + 1

                # Clear recording mode and suggestion cache
                st.session_state.recording_mode = None
                if 'set_suggestion_cache' in st.session_state:
                    del st.session_state.set_suggestion_cache

                # Clear confirmation flag
                st.session_state.confirm_skip_exercise_active = False

                # Go to intro screen for next exercise
                st.session_state.log_state = 'session_exercise_intro'
                print(f"   Moving to exercise index {current_index + 1}")
                st.rerun()
        with skip_col2:
            if st.button("No, Do This Exercise", key="confirm_skip_active_no", use_container_width=True):
                st.session_state.confirm_skip_exercise_active = False
                st.rerun()

    # Cancel session button
    st.divider()
    if st.button("❌ Cancel Session", key="cancel_session_btn"):
        from src.ui.session import reset_workout_session
        reset_workout_session()
        # Navigate to home instead of staying on this page
        st.switch_page("app.py")


def render_session_set_preview():
    """Show set preview with rest timer and options (set-by-set flow)."""
    import time

    st.title("✅ Set Recorded")

    session = st.session_state.workout_session
    if not session:
        st.error("No session found")
        return

    # Get in_progress_exercise details
    in_progress = session.get('in_progress_exercise')
    if not in_progress:
        st.error("No exercise in progress")
        return

    exercise_name = in_progress.get('name', 'Unknown')
    all_sets = in_progress.get('sets', [])
    current_set_number = session.get('current_set_number', 1)
    target_sets = session.get('target_sets', 0)

    if not all_sets:
        st.error("No sets recorded yet")
        return

    # Get the set just recorded (last set in list)
    last_set = all_sets[-1]
    weight = last_set.get('weight_lbs')
    reps = last_set.get('reps')

    # Show set info
    st.success(f"**{exercise_name}**")

    # Show set number prominently (LARGE for gym visibility)
    if target_sets > 0:
        st.markdown(f'<div class="set-number-display">SET {current_set_number} OF {target_sets}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="set-number-display">SET {current_set_number}</div>', unsafe_allow_html=True)

    # Show set details
    if weight:
        st.info(f"**{reps} reps @ {weight:.0f} lbs**")
    else:
        st.info(f"**{reps} reps** (bodyweight)")

    st.divider()

    # Edit this set (expandable)
    if 'editing_set' not in st.session_state:
        st.session_state.editing_set = False

    with st.expander("✏️ Edit This Set (optional)", expanded=st.session_state.editing_set):
        col1, col2 = st.columns(2)

        with col1:
            edited_weight = st.number_input(
                "Weight (lbs):",
                value=float(weight) if weight else 0.0,
                step=2.5,
                key="edit_set_weight"
            )

        with col2:
            edited_reps = st.number_input(
                "Reps:",
                value=int(reps),
                min_value=1,
                max_value=100,
                key="edit_set_reps"
            )

        if st.button("💾 Save Changes", key="save_set_edit", type="primary"):
            # Update the last set in in_progress_exercise
            updated_set = {"reps": edited_reps}
            if edited_weight > 0:
                updated_set["weight_lbs"] = edited_weight

            in_progress['sets'][-1] = updated_set
            st.session_state.workout_session['in_progress_exercise'] = in_progress
            st.session_state.editing_set = False
            st.toast("✅ Set updated!", icon="✅")
            st.rerun()

    st.divider()

    # Check if this is the last set
    is_last_set = current_set_number >= target_sets

    # Rest timer (unless last set)
    if is_last_set:
        # Last set - show completion message
        st.success("🎉 All planned sets complete!")
        st.caption(f"You completed {current_set_number} of {target_sets} sets")

        st.divider()

        # Action buttons for last set
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Finish Exercise", key="complete_exercise_btn", use_container_width=True, type="primary"):
                # Move to exercise complete state
                st.session_state.log_state = 'session_exercise_complete'
                st.rerun()

        with col2:
            if st.button("➕ Add Bonus Set", key="add_bonus_set_btn", use_container_width=True):
                # Increment target sets and go back to active state
                st.session_state.workout_session['target_sets'] = target_sets + 1
                st.session_state.log_state = 'session_active'
                st.rerun()

    else:
        # Not last set - show rest timer
        rest_seconds = in_progress.get('rest_seconds', 90)

        st.markdown(f"### ⏸️ Rest Before Set {current_set_number + 1}")

        # Initialize rest timer
        if 'rest_start_time' not in st.session_state:
            st.session_state.rest_start_time = time.time()
            st.session_state.rest_duration = rest_seconds

        # Calculate remaining time
        elapsed = time.time() - st.session_state.rest_start_time
        remaining = max(0, st.session_state.rest_duration - elapsed)

        # Show countdown (VERY LARGE for quick glancing)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        st.markdown(f'<div class="rest-timer-display">⏱️ {mins}:{secs:02d}</div>', unsafe_allow_html=True)

        # Progress bar
        progress = 1.0 - (remaining / st.session_state.rest_duration) if st.session_state.rest_duration > 0 else 1.0
        st.markdown(f'''
        <div class="rest-progress-bar">
            <div class="rest-progress-fill" style="width: {progress * 100}%"></div>
        </div>
        ''', unsafe_allow_html=True)

        # Quick adjust buttons
        st.markdown('<div class="action-button-row">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("30s", key="rest_30s"):
                st.session_state.rest_duration = 30
                st.session_state.rest_start_time = time.time()
                st.rerun()

        with col2:
            if st.button("60s", key="rest_60s"):
                st.session_state.rest_duration = 60
                st.session_state.rest_start_time = time.time()
                st.rerun()

        with col3:
            if st.button("90s", key="rest_90s"):
                st.session_state.rest_duration = 90
                st.session_state.rest_start_time = time.time()
                st.rerun()

        with col4:
            if st.button("Next Set", key="skip_rest_btn", type="primary"):
                # Clear timer and go to next set
                if 'rest_start_time' in st.session_state:
                    del st.session_state.rest_start_time
                if 'rest_duration' in st.session_state:
                    del st.session_state.rest_duration
                st.session_state.log_state = 'session_active'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Auto-advance when timer expires
        if remaining <= 0:
            # Clear timer
            if 'rest_start_time' in st.session_state:
                del st.session_state.rest_start_time
            if 'rest_duration' in st.session_state:
                del st.session_state.rest_duration
            # Move to next set
            st.session_state.log_state = 'session_active'
            st.rerun()

        st.divider()

        # Early finish confirmation dialog
        if st.session_state.get('confirm_early_finish_preview'):
            # Use shared confirmation helper
            render_early_finish_confirmation(
                planned_sets=target_sets,
                completed_sets=current_set_number,
                confirm_yes_key="confirm_preview_yes",
                confirm_no_key="confirm_preview_no"
            )

        else:
            # Action buttons during rest (only show when not confirming)
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Finish Exercise Early", key="finish_exercise_early_btn", use_container_width=True):
                    st.session_state.confirm_early_finish_preview = True
                    st.rerun()

            with col2:
                if st.button("🔄 Redo This Set", key="redo_set_btn", use_container_width=True):
                    # Remove last set and go back to recording
                    in_progress['sets'].pop()
                    st.session_state.workout_session['in_progress_exercise'] = in_progress
                    st.session_state.workout_session['current_set_number'] = max(1, current_set_number - 1)

                    # Clear timer
                    if 'rest_start_time' in st.session_state:
                        del st.session_state.rest_start_time
                    if 'rest_duration' in st.session_state:
                        del st.session_state.rest_duration

                    # Go back to active state
                    st.session_state.log_state = 'session_active'
                    st.rerun()


def render_session_exercise_complete():
    """Show exercise summary and rest timer before next exercise (set-by-set flow)."""
    import time

    # DEBUG
    print(f"🟢 RENDER EXERCISE COMPLETE CALLED")
    session = st.session_state.workout_session
    if session:
        print(f"   In progress: {session.get('in_progress_exercise', {}).get('name')}")
        print(f"   Sets completed: {len(session.get('in_progress_exercise', {}).get('sets', []))}")
        print(f"   Current index: {session.get('current_exercise_index')}")

    # Phase 2: Large, prominent text for exercise details
    st.markdown('<div class="exercise-complete-banner">🎉 EXERCISE COMPLETE</div>', unsafe_allow_html=True)

    if not session:
        st.error("No session found")
        print(f"   ❌ ERROR: No session found")
        return

    # Get in_progress_exercise details
    in_progress = session.get('in_progress_exercise')
    if not in_progress:
        st.error("No exercise in progress")
        print(f"   ❌ ERROR: No in_progress_exercise")
        return

    exercise_name = in_progress.get('name', 'Unknown')
    all_sets = in_progress.get('sets', [])

    # Show exercise summary with larger text
    st.markdown(f'<div class="exercise-title">{exercise_name}</div>', unsafe_allow_html=True)
    st.caption(f"{len(all_sets)} sets completed")

    st.divider()

    # List all sets with larger text
    for i, set_data in enumerate(all_sets, 1):
        weight = set_data.get('weight_lbs')
        reps = set_data.get('reps')

        if weight:
            st.markdown(f'<div class="set-detail">Set {i}: {reps} reps @ {weight:.0f} lbs</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="set-detail">Set {i}: {reps} reps (bodyweight)</div>', unsafe_allow_html=True)

    # Calculate total volume
    total_volume = sum(
        s.get('weight_lbs', 0) * s.get('reps', 0)
        for s in all_sets
    )

    if total_volume > 0:
        st.divider()
        st.markdown(f'<div class="stat-highlight">Total Volume: {total_volume:,.0f} lbs</div>', unsafe_allow_html=True)

    st.divider()

    # Check if there's a next exercise
    planned_template = session.get('planned_template', {})
    current_index = session.get('current_exercise_index', 0)
    plan_exercises = planned_template.get('exercises', [])

    # After accumulating, index will be current_index + 1
    next_index = current_index + 1
    is_last_exercise = next_index >= len(plan_exercises)

    if is_last_exercise:
        # No more exercises - offer to continue or finish
        st.success("🎉 You've completed all planned exercises!")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Finish Workout", key="finish_workout_btn", use_container_width=True, type="primary"):
                # Accumulate current exercise
                from src.agents.session_graph import accumulate_exercise

                # Build complete exercise from in_progress
                complete_exercise = {
                    "name": exercise_name,
                    "sets": all_sets
                }

                # Add to accumulated exercises
                accumulated = session.get('accumulated_exercises', []).copy()
                accumulated.append(complete_exercise)

                st.session_state.workout_session['accumulated_exercises'] = accumulated
                st.session_state.workout_session['in_progress_exercise'] = None
                st.session_state.workout_session['current_exercise_name'] = None
                st.session_state.workout_session['current_set_number'] = 0
                st.session_state.workout_session['target_sets'] = 0
                st.session_state.workout_session['current_exercise_sets_completed'] = []

                # Increment exercise index
                st.session_state.workout_session['current_exercise_index'] = next_index

                # Move to workout review
                st.session_state.log_state = 'session_workout_review'
                st.rerun()

        with col2:
            if st.button("💪 Add More Exercises", key="continue_workout_btn", use_container_width=True):
                # Accumulate current exercise and continue
                complete_exercise = {
                    "name": exercise_name,
                    "sets": all_sets
                }

                accumulated = session.get('accumulated_exercises', []).copy()
                accumulated.append(complete_exercise)

                st.session_state.workout_session['accumulated_exercises'] = accumulated
                st.session_state.workout_session['in_progress_exercise'] = None
                st.session_state.workout_session['current_exercise_name'] = None
                st.session_state.workout_session['current_set_number'] = 0
                st.session_state.workout_session['target_sets'] = 0
                st.session_state.workout_session['current_exercise_sets_completed'] = []
                st.session_state.workout_session['current_exercise_index'] = next_index

                # Set flag to continue
                st.session_state.continue_after_plan = True

                # Move to intro screen for next exercise
                st.session_state.log_state = 'session_exercise_intro'
                st.rerun()

    else:
        # There's a next exercise - show rest timer
        next_exercise = plan_exercises[next_index]
        next_exercise_name = next_exercise.get('name', 'Next exercise')
        rest_seconds = next_exercise.get('rest_seconds', 120)  # Longer rest between exercises

        st.markdown(f"### ⏸️ Rest Before {next_exercise_name}")

        # Initialize rest timer
        if 'exercise_rest_start_time' not in st.session_state:
            st.session_state.exercise_rest_start_time = time.time()
            st.session_state.exercise_rest_duration = rest_seconds

        # Calculate remaining time
        elapsed = time.time() - st.session_state.exercise_rest_start_time
        remaining = max(0, st.session_state.exercise_rest_duration - elapsed)

        # Show countdown
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        st.markdown(f"## ⏱️ {mins}:{secs:02d}")

        # Progress bar
        progress = 1.0 - (remaining / st.session_state.exercise_rest_duration) if st.session_state.exercise_rest_duration > 0 else 1.0
        st.progress(progress)

        # Quick adjust buttons
        st.markdown('<div class="action-button-row">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("30s", key="ex_rest_30s"):
                st.session_state.exercise_rest_duration = 30
                st.session_state.exercise_rest_start_time = time.time()
                st.rerun()

        with col2:
            if st.button("60s", key="ex_rest_60s"):
                st.session_state.exercise_rest_duration = 60
                st.session_state.exercise_rest_start_time = time.time()
                st.rerun()

        with col3:
            if st.button("90s", key="ex_rest_90s"):
                st.session_state.exercise_rest_duration = 90
                st.session_state.exercise_rest_start_time = time.time()
                st.rerun()

        with col4:
            if st.button("Continue", key="skip_ex_rest_btn", type="primary"):
                # Accumulate and move to next exercise
                complete_exercise = {
                    "name": exercise_name,
                    "sets": all_sets
                }

                accumulated = session.get('accumulated_exercises', []).copy()
                accumulated.append(complete_exercise)

                st.session_state.workout_session['accumulated_exercises'] = accumulated
                st.session_state.workout_session['in_progress_exercise'] = None
                st.session_state.workout_session['current_exercise_name'] = None
                st.session_state.workout_session['current_set_number'] = 0
                st.session_state.workout_session['target_sets'] = 0
                st.session_state.workout_session['current_exercise_sets_completed'] = []
                st.session_state.workout_session['current_exercise_index'] = next_index

                # Clear timer
                if 'exercise_rest_start_time' in st.session_state:
                    del st.session_state.exercise_rest_start_time
                if 'exercise_rest_duration' in st.session_state:
                    del st.session_state.exercise_rest_duration

                # Refresh next suggestion for the new exercise
                from src.agents.session_graph import refresh_next_suggestion
                st.session_state.workout_session = refresh_next_suggestion(st.session_state.workout_session)

                # Move to intro screen for next exercise
                st.session_state.log_state = 'session_exercise_intro'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Auto-advance when timer expires
        if remaining <= 0:
            # Accumulate and move to next exercise automatically
            complete_exercise = {
                "name": exercise_name,
                "sets": all_sets
            }

            accumulated = session.get('accumulated_exercises', []).copy()
            accumulated.append(complete_exercise)

            st.session_state.workout_session['accumulated_exercises'] = accumulated
            st.session_state.workout_session['in_progress_exercise'] = None
            st.session_state.workout_session['current_exercise_name'] = None
            st.session_state.workout_session['current_set_number'] = 0
            st.session_state.workout_session['target_sets'] = 0
            st.session_state.workout_session['current_exercise_sets_completed'] = []
            st.session_state.workout_session['current_exercise_index'] = next_index

            # Clear timer
            if 'exercise_rest_start_time' in st.session_state:
                del st.session_state.exercise_rest_start_time
            if 'exercise_rest_duration' in st.session_state:
                del st.session_state.exercise_rest_duration

            # Refresh next suggestion
            from src.agents.session_graph import refresh_next_suggestion
            st.session_state.workout_session = refresh_next_suggestion(st.session_state.workout_session)

            # Move to intro screen for next exercise
            st.session_state.log_state = 'session_exercise_intro'
            st.rerun()

        st.divider()

        # Additional actions
        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Add Another Set", key="add_another_set_btn", use_container_width=True):
                # Increment target sets and go back to active state
                target_sets = session.get('target_sets', 0)
                st.session_state.workout_session['target_sets'] = target_sets + 1

                # Clear timer
                if 'exercise_rest_start_time' in st.session_state:
                    del st.session_state.exercise_rest_start_time
                if 'exercise_rest_duration' in st.session_state:
                    del st.session_state.exercise_rest_duration

                # Go back to active state for bonus set
                st.session_state.log_state = 'session_active'
                st.rerun()

        with col2:
            if st.button("🔄 Redo Exercise", key="redo_exercise_btn", use_container_width=True):
                # Clear in_progress_exercise and start over
                st.session_state.workout_session['in_progress_exercise'] = None
                st.session_state.workout_session['current_exercise_name'] = None
                st.session_state.workout_session['current_set_number'] = 0
                st.session_state.workout_session['target_sets'] = 0
                st.session_state.workout_session['current_exercise_sets_completed'] = []

                # Clear timer
                if 'exercise_rest_start_time' in st.session_state:
                    del st.session_state.exercise_rest_start_time
                if 'exercise_rest_duration' in st.session_state:
                    del st.session_state.exercise_rest_duration

                # Go back to active state
                st.session_state.log_state = 'session_active'
                st.rerun()


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
    """Show exercise preview with rest timer and editing."""
    import time
    from src.ui.session_components import render_exercise_preview
    from src.agents.session_graph import accumulate_exercise, refresh_next_suggestion

    st.title("✅ Exercise Added")

    # Show parsed exercise
    session = st.session_state.workout_session
    if session and session.get('current_parsed_exercise'):
        render_exercise_preview(session['current_parsed_exercise'])

    # Show deviation warning if detected
    deviation = session.get('current_deviation') if session else None
    if deviation and deviation.get('is_deviation'):
        _render_deviation_warning(deviation, session)

    st.divider()
    st.container()  # Force break from column context

    # Check if this is the last exercise in the plan
    planned_template = session.get('planned_template', {})
    current_index = session.get('current_exercise_index', 0)
    plan_exercises = planned_template.get('exercises', [])

    # After accumulating this exercise, index will be current_index + 1
    # So the NEXT exercise will be at current_index + 1
    next_index = current_index + 1
    is_last_exercise = next_index >= len(plan_exercises)

    # Initialize rest timer (unless it's the last exercise)
    if not is_last_exercise:
        # Figure out what the ACTUAL next exercise will be (not the stale suggestion)
        next_planned_exercise = plan_exercises[next_index]
        next_exercise_name = next_planned_exercise.get('name', 'Next exercise')
        next_rest_duration = next_planned_exercise.get('rest_seconds', 90)

        if 'rest_start_time' not in st.session_state:
            st.session_state.rest_start_time = time.time()
            st.session_state.rest_duration = next_rest_duration

        # Show what's next
        st.markdown(f"### ⏸️ Rest Before {next_exercise_name}")

        # Show the exercise being added (for review/editing)
        st.caption("Review your exercise while resting:")

        # Initialize edit mode if needed
        if 'editing_exercise' not in st.session_state:
            st.session_state.editing_exercise = False

        # Show exercise in expandable edit section
        with st.expander("📝 Edit Exercise (optional)", expanded=st.session_state.editing_exercise):
            current_ex = session.get('current_parsed_exercise', {})

            # Convert exercise back to text format for editing
            sets = current_ex.get('sets', [])
            exercise_name = current_ex.get('name', '')

            # Format sets as "weight x reps" strings
            sets_text = []
            for s in sets:
                weight = s.get('weight_lbs')
                reps = s.get('reps')
                if weight:
                    sets_text.append(f"{weight}x{reps}")
                else:
                    sets_text.append(f"{reps} reps")

            formatted_input = f"{exercise_name}: {', '.join(sets_text)}"

            # Editable text area
            edited_text = st.text_area(
                "Edit exercise:",
                value=formatted_input,
                help="Format: Exercise Name: weight x reps, weight x reps\nExample: Bench Press: 135x10, 135x8, 135x6",
                key="edit_exercise_text"
            )

            # Save edits button
            if st.button("💾 Save Edits", key="save_edits", type="primary"):
                # Re-parse the edited text
                from src.agents.session_graph import parse_exercise_input

                try:
                    # Parse the edited text
                    updated_session = parse_exercise_input({
                        **session,
                        'user_message': edited_text
                    })

                    # Update the current parsed exercise
                    st.session_state.workout_session = updated_session
                    st.toast("✅ Exercise updated!", icon="✅")
                    st.session_state.editing_exercise = False
                    st.rerun()

                except Exception as e:
                    st.error(f"Failed to parse edits: {e}")

        st.divider()

        # Rest timer
        elapsed = time.time() - st.session_state.rest_start_time
        remaining = max(0, st.session_state.rest_duration - elapsed)

        # Show rest timer
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        st.markdown(f"## ⏱️ {minutes}:{seconds:02d}")

        progress = 1.0 - (remaining / st.session_state.rest_duration)
        st.progress(progress)

        st.divider()
        st.markdown("**Adjust rest time:**")

        st.markdown('<div class="action-button-row">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        if col1.button("30s", key="rest_30", use_container_width=True):
            st.session_state.rest_duration = 30
            st.session_state.rest_start_time = time.time()
            st.rerun()
        if col2.button("60s", key="rest_60", use_container_width=True):
            st.session_state.rest_duration = 60
            st.session_state.rest_start_time = time.time()
            st.rerun()
        if col3.button("90s", key="rest_90", type="primary", use_container_width=True):
            st.session_state.rest_duration = 90
            st.session_state.rest_start_time = time.time()
            st.rerun()
        if col4.button("Next Exercise", key="skip", type="primary", use_container_width=True):
            # Skip rest and move to next exercise
            _complete_exercise_and_continue(session)
            return
        st.markdown('</div>', unsafe_allow_html=True)

        # Auto-rerun to update timer countdown
        if remaining > 0:
            time.sleep(0.5)
            st.rerun()
        else:
            # Rest complete - auto-advance to next exercise
            _complete_exercise_and_continue(session)
            return

    # Main action buttons (always visible, below timer if present)
    st.divider()

    # Show different message based on whether this is last exercise
    if is_last_exercise:
        st.success("🎉 **This is your last planned exercise!**")
        st.caption("You can finish your workout or add bonus exercises.")
        st.markdown("**Choose an action:**")

        col1, col2 = st.columns(2)
        finish = col1.button("✅ Finish Workout", key="finish", type="primary", use_container_width=True)
        add_more = col2.button("💪 Add More Exercises", key="add_more", use_container_width=True)

        # Redo button below
        if st.button("❌ Redo This Exercise", key="redo", use_container_width=True):
            # Clear and redo
            session['current_parsed_exercise'] = None
            st.session_state.workout_session = session
            if 'cached_transcription' in st.session_state:
                del st.session_state.cached_transcription
            if 'audio_recorder_key' not in st.session_state:
                st.session_state.audio_recorder_key = 0
            st.session_state.audio_recorder_key += 1
            st.session_state.recording_mode = None
            st.session_state.log_state = 'session_active'
            st.rerun()

        if add_more:
            # Accumulate current exercise and continue adding
            session['user_action'] = 'add_another'
            updated_session = accumulate_exercise(session)
            updated_session['user_action'] = None
            updated_session['response'] = None
            updated_session = refresh_next_suggestion(updated_session)
            st.session_state.workout_session = updated_session
            st.session_state.continue_after_plan = True  # Flag to allow bonus exercises

            # Clear recorder
            if 'cached_transcription' in st.session_state:
                del st.session_state.cached_transcription
            if 'audio_recorder_key' not in st.session_state:
                st.session_state.audio_recorder_key = 0
            st.session_state.audio_recorder_key += 1
            st.session_state.recording_mode = None

            st.session_state.log_state = 'session_active'
            st.rerun()
    else:
        # Not last exercise - show standard action buttons
        st.markdown("**Actions:**")

        col1, col2 = st.columns(2)
        finish = col1.button("✅ Finish Workout", key="finish", use_container_width=True)
        redo = col2.button("❌ Redo Exercise", key="redo", use_container_width=True)

        if finish:
            # Accumulate current exercise and finish
            session['user_action'] = 'add_another'
            updated_session = accumulate_exercise(session)
            updated_session['user_action'] = None
            st.session_state.workout_session = updated_session
            st.session_state.log_state = 'session_workout_review'
            # Clean up rest timer state
            if 'rest_start_time' in st.session_state:
                del st.session_state.rest_start_time
            st.rerun()

        if redo:
            # Clear and redo
            session['current_parsed_exercise'] = None
            st.session_state.workout_session = session
            if 'cached_transcription' in st.session_state:
                del st.session_state.cached_transcription
            if 'audio_recorder_key' not in st.session_state:
                st.session_state.audio_recorder_key = 0
            st.session_state.audio_recorder_key += 1
            st.session_state.recording_mode = None
            st.session_state.log_state = 'session_active'
            # Clean up rest timer state
            if 'rest_start_time' in st.session_state:
                del st.session_state.rest_start_time
            st.rerun()


def _complete_exercise_and_continue(session):
    """Helper to accumulate exercise and move to next."""
    from src.agents.session_graph import accumulate_exercise, refresh_next_suggestion

    # Accumulate exercise
    session['user_action'] = 'add_another'
    updated_session = accumulate_exercise(session)
    updated_session['user_action'] = None
    updated_session['response'] = None
    updated_session = refresh_next_suggestion(updated_session)

    st.session_state.workout_session = updated_session

    # Clear transcription and reset recorder
    if 'cached_transcription' in st.session_state:
        del st.session_state.cached_transcription
    if 'audio_recorder_key' not in st.session_state:
        st.session_state.audio_recorder_key = 0
    st.session_state.audio_recorder_key += 1

    # Reset states
    st.session_state.recording_mode = None
    st.session_state.editing_exercise = False
    if 'rest_start_time' in st.session_state:
        del st.session_state.rest_start_time

    # Move to next exercise
    st.session_state.log_state = 'session_active'
    st.rerun()


def render_abs_exercise_complete():
    """Show abs exercise summary and move to next or finish."""
    st.title("✅ Exercise Complete")

    session = st.session_state.workout_session
    in_progress = session.get('abs_in_progress_exercise')

    if not in_progress:
        st.error("No abs exercise in progress")
        return

    exercise_name = in_progress.get('name', 'Unknown')
    all_sets = in_progress.get('sets', [])

    # Show exercise summary
    st.success(f"**{exercise_name}**")
    st.caption(f"Completed {len(all_sets)} sets")

    st.divider()

    # Show all sets
    st.subheader("Sets Completed")
    for i, set_data in enumerate(all_sets, 1):
        reps = set_data.get('reps')
        notes = set_data.get('notes', '')
        if notes:
            st.caption(f"Set {i}: {reps} reps - {notes}")
        else:
            st.caption(f"Set {i}: {reps} reps")

    st.divider()

    # Move exercise to accumulated
    abs_accumulated = session.get('abs_accumulated_exercises', [])
    abs_accumulated.append({
        'name': exercise_name,
        'sets': all_sets
    })
    session['abs_accumulated_exercises'] = abs_accumulated

    # Clear in-progress state
    session['abs_in_progress_exercise'] = None
    session['abs_current_set_number'] = 0

    # Increment exercise index
    current_index = session.get('abs_current_exercise_index', 0)
    session['abs_current_exercise_index'] = current_index + 1

    st.session_state.workout_session = session

    # Check if more exercises
    abs_template = session.get('abs_planned_template', {})
    total_exercises = len(abs_template.get('exercises', []))
    exercises_done = len(abs_accumulated)

    if exercises_done >= total_exercises:
        # All abs exercises complete
        st.success("🎉 All abs exercises complete!")

        if st.button("Review Abs Session", key="abs_all_complete", type="primary", use_container_width=True):
            st.session_state.log_state = 'abs_workout_review'
            st.rerun()
    else:
        # More exercises remaining
        st.info(f"✅ Exercise {exercises_done} of {total_exercises} complete")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ Next Exercise", key="abs_next_exercise", type="primary", use_container_width=True):
                st.session_state.log_state = 'abs_exercise_intro'
                st.rerun()

        with col2:
            if st.button("✅ Finish Abs", key="abs_finish_early", use_container_width=True):
                st.session_state.log_state = 'abs_workout_review'
                st.rerun()


def render_abs_set_preview():
    """Show abs set preview with rest timer."""
    import time

    st.title("✅ Set Recorded")

    session = st.session_state.workout_session

    # Show overall abs progress
    abs_accumulated = session.get('abs_accumulated_exercises', [])
    abs_template = session.get('abs_planned_template', {})
    total_abs_exercises = len(abs_template.get('exercises', []))
    current_exercise_num = len(abs_accumulated) + 1

    st.caption(f"💪 Abs Exercise {current_exercise_num} of {total_abs_exercises}")

    in_progress = session.get('abs_in_progress_exercise')

    if not in_progress:
        st.error("No abs exercise in progress")
        return

    exercise_name = in_progress.get('name', 'Unknown')
    all_sets = in_progress.get('sets', [])
    current_set_number = session.get('abs_current_set_number', 1)
    target_sets = session.get('abs_target_sets', 0)
    rest_seconds = in_progress.get('rest_seconds', 45)

    if not all_sets:
        st.error("No sets recorded yet")
        return

    # Get the set just recorded (last set)
    last_set = all_sets[-1]
    reps = last_set.get('reps')
    notes = last_set.get('notes', '')

    # Show set info
    st.success(f"**{exercise_name}**")
    st.subheader(f"Set {current_set_number - 1} of {target_sets}")  # -1 because we already incremented

    # Show set details
    if notes:
        st.info(f"**{reps} reps** - {notes}")
    else:
        st.info(f"**{reps} reps**")

    st.divider()

    # Check if more sets needed
    is_last_set = current_set_number > target_sets

    if is_last_set:
        # Exercise complete
        st.success("🎉 Exercise complete!")

        st.divider()

        if st.button("✅ Continue", key="abs_continue_after_last", type="primary", use_container_width=True):
            st.session_state.log_state = 'abs_exercise_complete'
            st.rerun()
    else:
        # Rest timer
        st.subheader("⏱️ Rest Timer")

        # Initialize rest timer state
        if 'abs_rest_timer_start' not in st.session_state:
            st.session_state.abs_rest_timer_start = time.time()

        elapsed = int(time.time() - st.session_state.abs_rest_timer_start)
        remaining = max(0, rest_seconds - elapsed)

        # Show countdown
        if remaining > 0:
            st.metric("Time Remaining", f"{remaining}s")
            progress = (rest_seconds - remaining) / rest_seconds
            st.progress(progress)

            # Quick rest presets
            st.caption("Quick adjust:")
            preset_col1, preset_col2, preset_col3 = st.columns(3)
            with preset_col1:
                if st.button("30s", key="abs_rest_30"):
                    st.session_state.abs_rest_timer_start = time.time() - (rest_seconds - 30)
                    st.rerun()
            with preset_col2:
                if st.button("45s", key="abs_rest_45"):
                    st.session_state.abs_rest_timer_start = time.time() - (rest_seconds - 45)
                    st.rerun()
            with preset_col3:
                if st.button("60s", key="abs_rest_60"):
                    st.session_state.abs_rest_timer_start = time.time() - (rest_seconds - 60)
                    st.rerun()

            # Auto-advance when timer expires
            if remaining == 0:
                del st.session_state.abs_rest_timer_start
                st.session_state.log_state = 'abs_active'
                st.rerun()
        else:
            st.success("✅ Rest complete!")

        st.divider()

        # Action buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ Next Set", key="abs_next_set", type="primary", use_container_width=True):
                # Clear rest timer and go to next set
                if 'abs_rest_timer_start' in st.session_state:
                    del st.session_state.abs_rest_timer_start
                st.session_state.log_state = 'abs_active'
                st.rerun()

        with col2:
            if st.button("✅ Finish Exercise", key="abs_finish_from_preview", use_container_width=True):
                # Move to exercise complete
                if 'abs_rest_timer_start' in st.session_state:
                    del st.session_state.abs_rest_timer_start
                st.session_state.log_state = 'abs_exercise_complete'
                st.rerun()


def render_abs_active():
    """Render SET recording screen for abs exercises (simplified version)."""
    from src.ui.audio_recorder import combined_input
    from src.agents.session_graph import add_exercise_to_session

    st.title("🎙️ Record Abs Set")

    session = st.session_state.workout_session

    # Show overall abs progress
    abs_accumulated = session.get('abs_accumulated_exercises', [])
    abs_template = session.get('abs_planned_template', {})
    total_abs_exercises = len(abs_template.get('exercises', []))
    current_exercise_num = len(abs_accumulated) + 1

    st.caption(f"💪 Abs Exercise {current_exercise_num} of {total_abs_exercises}")

    # Get current abs exercise state
    in_progress = session.get('abs_in_progress_exercise')
    if not in_progress:
        st.error("No abs exercise in progress!")
        if st.button("Back"):
            st.session_state.log_state = 'abs_exercise_intro'
            st.rerun()
        return

    exercise_name = in_progress.get('name', 'Unknown')
    current_set = session.get('abs_current_set_number', 1)
    target_sets = session.get('abs_target_sets', 3)
    target_reps = in_progress.get('target_reps', 10)

    # Show exercise and set info
    st.success(f"🎯 **{exercise_name}**")
    st.subheader(f"Set {current_set} of {target_sets}")
    st.info(f"**Target:** {target_reps} reps")

    st.divider()
    st.subheader("Record What You Did")
    st.caption("Complete this set, then record your results:")

    # Recording interface
    user_input = combined_input(
        placeholder=f"e.g., '{target_reps} reps' or '45 seconds'",
        key=f"abs_set_input_{current_set}"
    )

    if user_input and user_input.strip():
        with st.spinner("Recording set..."):
            try:
                # Parse the input using add_exercise_to_session
                # Format as single exercise input
                exercise_input = f"{exercise_name}: {user_input}"

                # Parse using existing logic
                result = add_exercise_to_session(session, exercise_input)

                if result.get('success'):
                    # Extract the parsed set data
                    parsed_ex = result.get('parsed_exercise', {})
                    sets = parsed_ex.get('sets', [])

                    if sets:
                        # Add the set(s) to in_progress_exercise
                        in_progress['sets'].extend(sets)
                        session['abs_in_progress_exercise'] = in_progress

                        # Increment set number
                        new_set_num = current_set + len(sets)
                        session['abs_current_set_number'] = new_set_num

                        st.session_state.workout_session = session

                        # Move to set preview (rest timer)
                        st.session_state.log_state = 'abs_set_preview'
                        st.rerun()
                    else:
                        st.error("Could not parse set data. Try again.")
                else:
                    st.error(f"Could not parse: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error recording set: {str(e)}")

    st.divider()

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        # Finish exercise early
        if current_set > 1:
            if st.button("✅ Finish Exercise", key="abs_finish_exercise", use_container_width=True):
                # Move to exercise complete
                st.session_state.log_state = 'abs_exercise_complete'
                st.rerun()

    with col2:
        if st.button("❌ Cancel Abs", key="abs_cancel_from_active", use_container_width=True):
            st.session_state.confirm_cancel_abs = True
            st.rerun()

    # Cancel confirmation
    if st.session_state.get('confirm_cancel_abs'):
        st.divider()
        st.warning("⚠️ **Cancel abs session?**")

        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button("Yes, Cancel", key="abs_active_cancel_yes", type="primary", use_container_width=True):
                st.session_state.add_abs_to_workout = False
                if 'abs_recommendation' in st.session_state:
                    del st.session_state.abs_recommendation
                st.session_state.confirm_cancel_abs = False
                st.session_state.log_state = 'session_workout_review'
                st.rerun()
        with conf_col2:
            if st.button("No, Continue", key="abs_active_cancel_no", use_container_width=True):
                st.session_state.confirm_cancel_abs = False
                st.rerun()


def render_abs_exercise_intro():
    """
    Render abs exercise introduction screen before Set 1.

    Shows:
    - Exercise name prominently
    - Plan details (sets, reps, rest, notes)
    - Options: Start / Skip / Cancel
    """
    from src.agents.session_graph import generate_next_set_suggestion

    st.title("💪 Abs Exercise")

    session = st.session_state.workout_session

    # Show progress
    abs_accumulated = session.get('abs_accumulated_exercises', [])
    abs_template = session.get('abs_planned_template', {})
    total_abs_exercises = len(abs_template.get('exercises', []))

    st.caption(f"Exercise {len(abs_accumulated) + 1} of {total_abs_exercises}")

    st.divider()

    # Get current abs exercise from template
    current_index = session.get('abs_current_exercise_index', 0)
    planned_exercises = abs_template.get('exercises', [])

    if current_index >= len(planned_exercises):
        # No more abs exercises
        st.success("✅ All abs exercises complete!")
        if st.button("Review Abs Session", type="primary"):
            st.session_state.log_state = 'abs_workout_review'
            st.rerun()
        return

    exercise = planned_exercises[current_index]
    exercise_name = exercise.get('name', 'Unknown')
    target_sets = exercise.get('target_sets', 3)
    target_reps = exercise.get('target_reps', 10)
    rest_seconds = exercise.get('rest_seconds', 45)
    notes = exercise.get('notes', '')

    # Large exercise name display
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        margin: 20px 0;
    ">
        <h1 style="color: white; margin: 0; font-size: 2.5em;">
            {exercise_name}
        </h1>
    </div>
    """, unsafe_allow_html=True)

    # Exercise notes/form tips
    if notes:
        st.info(f"💡 **Form Tip:** {notes}")

    st.divider()

    # Plan summary
    st.subheader("📋 Plan")

    plan_col1, plan_col2 = st.columns(2)

    with plan_col1:
        st.metric("Sets", f"{target_sets} sets")
        st.metric("Reps per Set", f"{target_reps}")

    with plan_col2:
        st.metric("Rest Between Sets", f"{rest_seconds}s")

    st.divider()

    # Primary action: Start Exercise
    if st.button(
        "▶️  Start Exercise",
        key="start_abs_exercise_btn",
        use_container_width=True,
        type="primary",
        help="Begin recording Set 1"
    ):
        # Initialize abs exercise state
        session['abs_in_progress_exercise'] = {
            'name': exercise_name,
            'sets': [],
            'target_sets': target_sets,
            'target_reps': target_reps,
            'rest_seconds': rest_seconds
        }
        session['abs_current_set_number'] = 1
        session['abs_target_sets'] = target_sets
        session['abs_current_set_suggestion'] = {
            'set_number': 1,
            'target_reps': target_reps,
            'rest_seconds': rest_seconds
        }

        st.session_state.workout_session = session
        st.session_state.log_state = 'abs_active'
        st.rerun()

    st.divider()
    st.caption("Other Options:")

    # Secondary options
    opt_col1, opt_col2 = st.columns(2)

    with opt_col1:
        if st.button("⏭️ Skip Exercise", key="abs_intro_skip_btn", use_container_width=True):
            st.session_state.confirm_skip_abs_exercise = True
            st.rerun()

    with opt_col2:
        if st.button("❌ Cancel Abs", key="abs_intro_cancel_btn", use_container_width=True):
            st.session_state.confirm_cancel_abs = True
            st.rerun()

    # Show skip confirmation
    if st.session_state.get('confirm_skip_abs_exercise'):
        st.divider()
        st.warning(f"⚠️ **Skip {exercise_name}?**")

        skip_col1, skip_col2 = st.columns(2)
        with skip_col1:
            if st.button("Yes, Skip It", key="abs_confirm_skip_yes", type="primary", use_container_width=True):
                # Move to next abs exercise
                session['abs_current_exercise_index'] = current_index + 1
                st.session_state.workout_session = session
                st.session_state.confirm_skip_abs_exercise = False
                st.rerun()
        with skip_col2:
            if st.button("No, Do It", key="abs_confirm_skip_no", use_container_width=True):
                st.session_state.confirm_skip_abs_exercise = False
                st.rerun()

    # Show cancel confirmation
    if st.session_state.get('confirm_cancel_abs'):
        st.divider()
        st.warning("⚠️ **Cancel abs session?**")
        st.caption("Your main workout will still be saved.")

        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button("Yes, Cancel Abs", key="abs_confirm_cancel_yes", type="primary", use_container_width=True):
                # Back to workout review without abs
                st.session_state.add_abs_to_workout = False
                if 'abs_recommendation' in st.session_state:
                    del st.session_state.abs_recommendation
                st.session_state.confirm_cancel_abs = False
                st.session_state.log_state = 'session_workout_review'
                st.rerun()
        with conf_col2:
            if st.button("No, Continue", key="abs_confirm_cancel_no", use_container_width=True):
                st.session_state.confirm_cancel_abs = False
                st.rerun()


def render_abs_intro():
    """
    Abs introduction screen with AI template recommendation.

    Shows:
    - AI-recommended abs template with reasoning
    - Template exercises preview
    - Options: Start / Skip
    """
    st.title("💪 Add Abs Session")

    session = st.session_state.workout_session

    # Get abs recommendation (only call once, cache in session state)
    if 'abs_recommendation' not in st.session_state:
        from src.agents.abs_recommender import recommend_abs_template

        with st.spinner("Getting abs recommendation..."):
            try:
                # Get recommendation from AI
                recommendation = recommend_abs_template(time_available=15)
                st.session_state.abs_recommendation = recommendation
            except Exception as e:
                st.error(f"Error getting recommendation: {str(e)}")
                # Provide a fallback
                st.session_state.abs_recommendation = {
                    "template_id": None,
                    "template": None,
                    "reason": "Could not load recommendation",
                    "modifications": []
                }

    recommendation = st.session_state.abs_recommendation
    template = recommendation.get('template')

    if not template:
        st.error("❌ No abs templates available. Please check abs_templates.json")
        if st.button("⬅️ Back to Workout Review"):
            st.session_state.add_abs_to_workout = False
            if 'abs_recommendation' in st.session_state:
                del st.session_state.abs_recommendation
            st.session_state.log_state = 'session_workout_review'
            st.rerun()
        return

    # Show recommendation
    st.success(f"**Recommended:** {template['name']}")
    st.caption(recommendation['reason'])

    st.divider()

    # Show template preview
    st.markdown("### Exercises")
    for i, ex in enumerate(template.get('exercises', []), 1):
        reps_display = ex.get('target_reps', '?')
        sets_display = ex.get('target_sets', '?')
        st.caption(f"{i}. **{ex['name']}** - {sets_display} sets × {reps_display} reps")
        if ex.get('notes'):
            st.caption(f"   _{ex['notes']}_")

    st.caption(f"⏱️ Estimated time: ~{template.get('estimated_duration_min', 15)} minutes")

    st.divider()

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Start Abs Workout", type="primary", use_container_width=True):
            # Initialize abs session state
            session['abs_planned_template'] = template
            session['abs_accumulated_exercises'] = []
            session['abs_current_exercise_index'] = 0
            session['abs_in_progress_exercise'] = None
            session['abs_current_set_number'] = 0
            session['abs_target_sets'] = 0
            session['abs_current_set_suggestion'] = None

            st.session_state.workout_session = session
            st.session_state.log_state = 'abs_exercise_intro'
            st.rerun()

    with col2:
        if st.button("⏭️ Skip Abs", use_container_width=True):
            # Back to main workout review (without abs)
            st.session_state.add_abs_to_workout = False
            if 'abs_recommendation' in st.session_state:
                del st.session_state.abs_recommendation
            st.session_state.log_state = 'session_workout_review'
            st.rerun()


def _handle_combo_progression():
    """
    Handle progression to next workout in combo.

    After user completes first workout, load next template and continue.
    """
    session = st.session_state.workout_session

    if not session.get('combo_mode'):
        return  # Not in combo mode

    current_idx = session.get('current_template_index', 0)
    planned_templates = session.get('planned_templates', [])

    if current_idx >= len(planned_templates) - 1:
        return  # All templates completed

    # Move to next template
    next_idx = current_idx + 1
    next_template_info = planned_templates[next_idx]
    next_type = next_template_info["type"]
    next_template = next_template_info["template"]

    # Update session for next workout
    session['current_template_index'] = next_idx
    session['suggested_type'] = next_type
    session['actual_workout_type'] = next_type
    session['planned_template'] = next_template
    session['accumulated_exercises'] = []  # Reset for new workout
    session['current_exercise_index'] = 0
    session['in_progress_exercise'] = None
    session['current_set_number'] = 1

    # Reset set-by-set tracking
    session['current_exercise_name'] = None
    session['current_exercise_sets_completed'] = []
    session['target_sets'] = 0
    session['current_set_suggestion'] = None

    st.session_state.workout_session = session
    st.session_state.log_state = 'session_exercise_intro'


def render_session_workout_review():
    """Review full workout before saving."""
    from src.ui.session_components import render_workout_review

    # Show workout progress
    _render_workout_progress()

    # Render review
    session = st.session_state.workout_session
    if session:
        render_workout_review(session)

    st.divider()

    # Supplementary Work Section
    st.subheader("Supplementary Work")

    # Check if abs can be done today
    from src.data import can_do_supplementary_today
    can_do_abs = can_do_supplementary_today("abs")

    # Initialize session state for abs checkbox if not exists
    if 'add_abs_to_workout' not in st.session_state:
        st.session_state.add_abs_to_workout = False

    if can_do_abs["can_do"]:
        add_abs = st.checkbox(
            "Add abs to this workout",
            value=st.session_state.add_abs_to_workout,
            help="You can add an ab session after your main workout",
            key="abs_checkbox"
        )
        st.session_state.add_abs_to_workout = add_abs

        if add_abs:
            st.info("💪 Great! Abs will be logged with this workout.")
    else:
        st.warning(f"⚠️ Abs not recommended today: {can_do_abs['reason']}")
        st.caption("You can still add them if you want, but it's best to follow spacing rules.")

        # Still allow checkbox but with warning
        add_abs = st.checkbox(
            "Add abs anyway (not recommended)",
            value=st.session_state.add_abs_to_workout,
            key="abs_checkbox_override"
        )
        st.session_state.add_abs_to_workout = add_abs

    st.divider()

    # NEW: Check for combo mode - prompt for next workout if more templates remaining
    if session.get('combo_mode'):
        current_idx = session.get('current_template_index', 0)
        planned_templates = session.get('planned_templates', [])
        total_templates = len(planned_templates)

        if current_idx < total_templates - 1:
            # More workouts in combo!
            remaining = total_templates - current_idx - 1
            completed_types = [t["type"] for t in planned_templates[:current_idx + 1]]
            next_template_info = planned_templates[current_idx + 1]
            next_type = next_template_info["type"]
            next_duration = next_template_info.get("duration_min", 35)

            st.warning(f"⚠️ **You have {remaining} more workout(s) in today's combo.**")
            st.success(f"✅ {' ✅ '.join(completed_types)}")
            st.info(f"⏭️ **Next:** {next_type} workout (~{next_duration} min)")

            st.divider()

            # Offer two options
            col1, col2 = st.columns(2)

            with col1:
                if st.button("➡️ Continue to Next", type="primary", use_container_width=True):
                    # Save current workout first
                    from src.agents.session_graph import finish_session

                    with st.spinner("Saving workout..."):
                        final_session = finish_session(session)

                    st.session_state.workout_session = final_session

                    if final_session.get('saved'):
                        # Progress to next template
                        _handle_combo_progression()
                        st.rerun()
                    else:
                        st.error(f"❌ {final_session.get('response', 'Failed to save')}")

            with col2:
                if st.button("✅ Finish for Today", use_container_width=True):
                    # Save only this workout
                    from src.agents.session_graph import finish_session

                    with st.spinner("Saving workout..."):
                        final_session = finish_session(session)

                    st.session_state.workout_session = final_session

                    if final_session.get('saved'):
                        st.session_state.log_workflow_state = {
                            'workout_id': final_session.get('workout_id'),
                            'saved': True
                        }
                        st.session_state.log_state = 'saved'
                        st.rerun()
                    else:
                        st.error(f"❌ {final_session.get('response', 'Failed to save')}")

            # Add cancel button below
            st.divider()
            if st.button("❌ Cancel Workout", use_container_width=False):
                from src.ui.session import reset_workout_session
                reset_workout_session()
                st.switch_page("app.py")

            # Stop here - don't show normal save button
            return

    # Normal save buttons (non-combo or last in combo)
    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("💾 Save Workout", type="primary", use_container_width=True):
            # Check if abs was requested
            if st.session_state.get('add_abs_to_workout', False):
                # START ABS WORKFLOW - transition to abs intro
                st.session_state.log_state = 'abs_intro'
                st.rerun()
            else:
                # Save main workout only (no abs)
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


def render_abs_workout_review():
    """
    Review all abs exercises before saving with main workout.

    Shows:
    - All abs exercises completed with sets
    - Optional abs notes field
    - Actions: Save Main + Abs / Discard Abs
    """
    st.title("🎯 Abs Session Review")

    session = st.session_state.workout_session
    abs_exercises = session.get('abs_accumulated_exercises', [])

    if not abs_exercises:
        st.warning("⚠️ No abs exercises recorded")
        if st.button("⬅️ Back to Main Review"):
            st.session_state.log_state = 'session_workout_review'
            st.rerun()
        return

    # Show abs exercises summary
    st.subheader(f"✅ Completed {len(abs_exercises)} Exercise{'s' if len(abs_exercises) != 1 else ''}")

    st.divider()

    # Show each exercise with sets - Phase 2: larger text
    for i, ex in enumerate(abs_exercises, 1):
        ex_name = ex.get('name', 'Unknown')
        sets = ex.get('sets', [])

        # Exercise name - large and prominent
        st.markdown(f'<div class="exercise-title">{i}. {ex_name}</div>', unsafe_allow_html=True)
        st.caption(f"{len(sets)} sets")

        # Show sets with larger text
        for j, set_data in enumerate(sets, 1):
            reps = set_data.get('reps')
            weight = set_data.get('weight_lbs')
            notes = set_data.get('notes', '')

            if weight:
                st.markdown(f'<div class="set-detail">Set {j}: {reps} reps @ {weight:.0f} lbs {notes}</div>', unsafe_allow_html=True)
            else:
                if notes:
                    st.markdown(f'<div class="set-detail">Set {j}: {reps} reps - {notes}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="set-detail">Set {j}: {reps} reps</div>', unsafe_allow_html=True)

        # Calculate and show volume
        volume = sum(s.get('reps', 0) * s.get('weight_lbs', 0) for s in sets)
        if volume > 0:
            st.markdown(f'<div class="stat-highlight">Volume: {volume:,.0f} lbs</div>', unsafe_allow_html=True)

        st.divider()

    st.divider()

    # Optional notes for entire abs session
    abs_notes = st.text_area(
        "Abs Session Notes (optional)",
        placeholder="How did the abs session feel?",
        key="abs_session_notes_input"
    )

    st.divider()

    # Action buttons
    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("💾 Save Main Workout + Abs", type="primary", use_container_width=True):
            try:
                from src.agents.session_graph import finish_session

                # Package abs data into supplementary_work format
                abs_template = session.get('abs_planned_template', {})
                abs_work = {
                    "type": "abs",
                    "template_id": abs_template.get('id'),
                    "exercises": [
                        {
                            "name": ex.get('name'),
                            "sets": ex.get('sets', []),
                            "notes": None
                        }
                        for ex in abs_exercises
                    ],
                    "notes": abs_notes if abs_notes else None
                }

                # Add to session
                session['supplementary_work'] = [abs_work]

                with st.spinner("Saving workout with abs..."):
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

                    # Clean up abs state
                    if 'abs_recommendation' in st.session_state:
                        del st.session_state.abs_recommendation
                    if 'abs_rest_timer_start' in st.session_state:
                        del st.session_state.abs_rest_timer_start

                    st.rerun()
                else:
                    st.error(f"❌ {final_session.get('response', 'Failed to save')}")

            except Exception as e:
                st.error(f"❌ Error saving workout: {str(e)}")

    with col2:
        if st.button("❌ Discard Abs", use_container_width=True):
            # Confirmation dialog
            if st.session_state.get('confirm_discard_abs_review'):
                # Actually discard
                session['abs_accumulated_exercises'] = []
                session['abs_planned_template'] = None
                st.session_state.add_abs_to_workout = False
                st.session_state.workout_session = session
                st.session_state.log_state = 'session_workout_review'
                st.session_state.confirm_discard_abs_review = False

                # Clean up
                if 'abs_recommendation' in st.session_state:
                    del st.session_state.abs_recommendation

                st.rerun()
            else:
                st.session_state.confirm_discard_abs_review = True
                st.rerun()

    # Show discard confirmation warning
    if st.session_state.get('confirm_discard_abs_review'):
        st.divider()
        st.warning("⚠️ **Discard abs session?**")
        st.caption("Your main workout will still be saved. Click 'Discard Abs' again to confirm.")


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

    # Show abs summary if abs were included
    session = st.session_state.workout_session
    if session:
        supp_work = session.get('supplementary_work', [])
        if supp_work:
            # Check if abs were done (could be old or new format)
            abs_data = None
            if isinstance(supp_work[0], dict):
                # New format
                for work in supp_work:
                    if work.get('type') == 'abs':
                        abs_data = work
                        break
            elif isinstance(supp_work[0], str) and 'abs' in supp_work:
                # Old format (just a flag)
                abs_data = {'type': 'abs', 'exercises': []}

            if abs_data:
                st.divider()
                abs_exercises = abs_data.get('exercises', [])
                if abs_exercises:
                    st.success(f"🎯 **Plus {len(abs_exercises)} abs exercise{'s' if len(abs_exercises) != 1 else ''}!**")
                    total_abs_sets = sum(len(ex.get('sets', [])) for ex in abs_exercises)
                    st.caption(f"Total abs sets: {total_abs_sets}")
                else:
                    st.success("🎯 **Plus abs!**")

    st.divider()

    # NEW: Check if still in catch-up mode
    from src.tools.recommend_tools import get_weekly_split_status

    status = get_weekly_split_status.invoke({})
    remaining = status.get("remaining", {})
    days_left = status.get("days_left_in_week", 0)
    total_remaining = sum(remaining.values())

    # If still need more workouts today (catch-up mode)
    if total_remaining > 0 and days_left <= 1:
        st.divider()
        st.warning(f"⚡ **Catch-up reminder:** You still have {total_remaining} workout(s) to complete this week!")

        # Get the next needed workout type
        next_needed_types = [t for t, count in remaining.items() if count > 0]
        if next_needed_types:
            next_type = next_needed_types[0]

            # Quick restart button for next workout
            if st.button(
                f"🏋️ Start Next Workout ({next_type})",
                type="primary",
                use_container_width=True,
                key="start_next_catchup"
            ):
                # Reset session and go back to planning
                from src.ui.session import reset_workout_session
                reset_workout_session()
                st.session_state.log_state = 'planning_chat'
                st.rerun()

        st.divider()

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

elif st.session_state.log_state == 'session_exercise_intro':
    print(f"🔴 STATE ROUTER: session_exercise_intro")
    render_session_exercise_intro()
elif st.session_state.log_state == 'session_active':
    print(f"🔴 STATE ROUTER: session_active")
    render_session_active_state()
elif st.session_state.log_state == 'session_set_preview':
    print(f"🔴 STATE ROUTER: session_set_preview")
    render_session_set_preview()
elif st.session_state.log_state == 'session_exercise_complete':
    print(f"🔴 STATE ROUTER: session_exercise_complete")
    render_session_exercise_complete()
elif st.session_state.log_state == 'session_exercise_preview':
    print(f"🔴 STATE ROUTER: session_exercise_preview")
    render_session_exercise_preview()
elif st.session_state.log_state == 'session_workout_review':
    print(f"🔴 STATE ROUTER: session_workout_review")
    render_session_workout_review()
elif st.session_state.log_state == 'abs_intro':
    print(f"🔴 STATE ROUTER: abs_intro")
    render_abs_intro()
elif st.session_state.log_state == 'abs_exercise_intro':
    print(f"🔴 STATE ROUTER: abs_exercise_intro")
    render_abs_exercise_intro()
elif st.session_state.log_state == 'abs_active':
    print(f"🔴 STATE ROUTER: abs_active")
    render_abs_active()
elif st.session_state.log_state == 'abs_set_preview':
    print(f"🔴 STATE ROUTER: abs_set_preview")
    render_abs_set_preview()
elif st.session_state.log_state == 'abs_exercise_complete':
    print(f"🔴 STATE ROUTER: abs_exercise_complete")
    render_abs_exercise_complete()
elif st.session_state.log_state == 'abs_workout_review':
    print(f"🔴 STATE ROUTER: abs_workout_review")
    render_abs_workout_review()
else:
    print(f"🔴 STATE ROUTER: Unknown state '{st.session_state.log_state}' - resetting to planning_chat")
    # Fallback - reset to planning chat
    st.session_state.log_state = 'planning_chat'
    st.rerun()
