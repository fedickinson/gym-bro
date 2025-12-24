"""
Suggestion UI Components - Display next exercise suggestions.

Shows AI-powered suggestions for the next exercise with:
- Clear differentiation between plan-based vs adaptive suggestions
- Weight/reps/sets display
- Reasoning for the suggestion
"""

import streamlit as st


def render_next_suggestion(suggestion: dict | None):
    """
    Render the next exercise suggestion.

    Args:
        suggestion: Suggestion dict from suggestion_engine, or None
    """
    if not suggestion:
        return

    exercise_name = suggestion.get('exercise_name')
    source = suggestion.get('source', 'adaptive')

    # No suggestion available
    if not exercise_name:
        reasoning = suggestion.get('reasoning', 'Great workout!')
        st.info(f"✅ {reasoning}")
        return

    # Show suggestion with appropriate styling
    if source == "plan":
        _render_plan_suggestion(suggestion)
    else:
        _render_adaptive_suggestion(suggestion)


def _render_plan_suggestion(suggestion: dict):
    """
    Render a plan-based suggestion.

    Args:
        suggestion: Suggestion dict with source="plan"
    """
    st.subheader("📋 Next from Your Plan")

    exercise_name = suggestion.get('exercise_name')
    target_sets = suggestion.get('target_sets', 3)
    target_reps = suggestion.get('target_reps', 10)
    suggested_weight = suggestion.get('suggested_weight_lbs')
    reasoning = suggestion.get('reasoning', '')
    plan_index = suggestion.get('plan_index', 0)

    # Exercise name (large, prominent)
    st.markdown(f"### **{exercise_name}**")

    # Show plan position
    st.caption(f"Exercise #{plan_index + 1} in your plan")

    # Metrics in columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Sets", target_sets)

    with col2:
        st.metric("Reps", target_reps)

    with col3:
        if suggested_weight:
            st.metric("Weight", f"{suggested_weight:.0f} lbs")
        else:
            st.metric("Weight", "⚠️ Your choice")

    # Show reasoning if available
    if reasoning:
        st.caption(f"💡 {reasoning}")

    # Highlight if weight needs to be specified
    if not suggested_weight:
        st.warning("⚠️ You'll need to specify the weight you used")


def _render_adaptive_suggestion(suggestion: dict):
    """
    Render an AI-adaptive suggestion.

    Args:
        suggestion: Suggestion dict with source="adaptive"
    """
    st.subheader("🤖 AI Suggests")

    exercise_name = suggestion.get('exercise_name')
    target_sets = suggestion.get('target_sets', 3)
    target_reps = suggestion.get('target_reps', 10)
    suggested_weight = suggestion.get('suggested_weight_lbs')
    reasoning = suggestion.get('reasoning', '')

    # Exercise name (large, prominent)
    st.markdown(f"### **{exercise_name}**")

    st.caption("Complementary exercise for your workout")

    # Metrics in columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Sets", target_sets)

    with col2:
        st.metric("Reps", target_reps)

    with col3:
        if suggested_weight:
            st.metric("Weight", f"{suggested_weight:.0f} lbs")
        else:
            st.metric("Weight", "⚠️ Your choice")

    # Show reasoning
    if reasoning:
        st.info(f"💡 {reasoning}")

    # Highlight if weight needs to be specified
    if not suggested_weight:
        st.warning("⚠️ You'll need to specify the weight you used")


def render_suggestion_prompt():
    """
    Render prompt text encouraging user to record the suggested exercise.

    Returns:
        None
    """
    st.caption("👇 Record this exercise or speak/type a different one")
    st.divider()


def render_no_suggestion_state():
    """
    Render state when no suggestion is available.

    Used when template is complete and user can choose to add more or finish.
    """
    st.success("✅ You've completed your planned workout!")
    st.info("💪 You can add more exercises or finish your workout.")
