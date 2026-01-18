"""
Chat Page - Conversational interface with the AI fitness coach.

Routes questions to Query Agent, Recommend Agent, or Chat Chain based on intent.
"""

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from src.ui.session import init_session_state, add_chat_message, clear_chat_history, get_orchestrator
from src.ui.navigation import render_bottom_nav
from src.ui.shared_components import render_sidebar
from src.ui.styles import get_global_styles

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Chat - Gym Bro",
    page_icon="💬",
    layout="centered"  # Centered for better desktop UX
)

# Initialize session state
init_session_state()

# Render bottom navigation
st.session_state.current_page = 'Chat'
render_bottom_nav('Chat')

# Apply global design system styles
st.markdown(get_global_styles(), unsafe_allow_html=True)

# ============================================================================
# Page Content
# ============================================================================

st.title("💬 Chat with Your Coach")
st.caption("Ask questions about your workouts, get recommendations, or just chat!")

# ============================================================================
# Sidebar Controls
# ============================================================================

with st.sidebar:
    render_sidebar(current_page="Chat")

    st.divider()

    # Chat-specific controls below
    st.subheader("Chat Controls")

    if st.button("🗑️ Clear History", use_container_width=True):
        clear_chat_history()
        st.rerun()

    # Dev Mode: Export Logs
    from src.dev_tools import is_dev_mode, format_chat_logs_as_json, format_chat_logs_as_markdown, generate_filename

    if is_dev_mode():
        st.divider()
        st.subheader("🛠️ Dev Tools")
        st.caption("Debug mode enabled")

        col1, col2 = st.columns(2)

        with col1:
            # Export as JSON
            if len(st.session_state.chat_history) > 0:
                json_data = format_chat_logs_as_json(
                    st.session_state.chat_history,
                    metadata={
                        "session_type": "chat",
                        "total_messages": len(st.session_state.chat_history)
                    }
                )
                st.download_button(
                    label="📥 JSON",
                    data=json_data,
                    file_name=generate_filename("json"),
                    mime="application/json",
                    use_container_width=True
                )

        with col2:
            # Export as Markdown
            if len(st.session_state.chat_history) > 0:
                md_data = format_chat_logs_as_markdown(
                    st.session_state.chat_history,
                    metadata={
                        "session_type": "chat",
                        "total_messages": len(st.session_state.chat_history)
                    }
                )
                st.download_button(
                    label="📥 MD",
                    data=md_data,
                    file_name=generate_filename("md"),
                    mime="text/markdown",
                    use_container_width=True
                )

    st.divider()

    # Example questions
    st.subheader("Try asking:")
    st.caption("• How many workouts did I do this month?")
    st.caption("• What's my bench press progression?")
    st.caption("• What should I do today?")
    st.caption("• Let's do a push workout")
    st.caption("• I want to workout but no barbell today")
    st.caption("• What's progressive overload?")

    st.divider()
    st.caption(f"Total messages: {len(st.session_state.chat_history)}")

    st.divider()
    st.caption("Version 1.0.0")

# ============================================================================
# Chat Display
# ============================================================================

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg['role']):
        st.write(msg['content'])

# ============================================================================
# Workout Session Navigation (if created from chat)
# ============================================================================

if st.session_state.get('workout_session') and st.session_state.get('chat_initiated_workout'):
    # A workout session was created from chat - show navigation
    session = st.session_state.workout_session
    workout_type = session.get('suggested_type', 'Unknown')
    exercise_count = len(session.get('planned_template', {}).get('exercises', []))

    st.divider()

    st.success(f"✅ Your {workout_type} workout is ready!")
    st.caption(f"{exercise_count} exercises planned")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🏋️ Continue to Workout →", type="primary", use_container_width=True, key="nav_to_workout"):
            # Clear the flag so we don't show this button again
            st.session_state.chat_initiated_workout = False
            # Navigate to workout page (session is already in state)
            st.switch_page("pages/1_Log_Workout.py")

    # Option to cancel
    if st.button("❌ Cancel Workout", use_container_width=False):
        from src.ui.session import reset_workout_session
        reset_workout_session()
        st.rerun()

    st.divider()

# ============================================================================
# Chat Input
# ============================================================================

if user_input := st.chat_input("Ask me anything..."):
    # Add user message to history
    add_chat_message("user", user_input)

    # Display user message
    with st.chat_message("user"):
        st.write(user_input)

    # Get AI response from orchestrator
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                orchestrator = get_orchestrator()
                # Use process_message to get full result with session_data
                # Pass chat history for conversation context (excluding current message already added)
                result = orchestrator.process_message(
                    user_input,
                    chat_history=st.session_state.chat_history[:-1]  # Exclude the message we just added
                )

                response = result["response"]
                session_data = result.get("session_data")

                # Display response
                st.write(response)

                # If a workout session was created, store it in session state
                if session_data:
                    st.session_state.workout_session = session_data
                    st.session_state.chat_initiated_workout = True
                    st.session_state.log_state = 'planning_chat'  # Set to planning state

                # Add assistant message to history with metadata
                add_chat_message("assistant", response,
                                agent=result.get("handler", "orchestrator"),
                                intent=result.get("intent"))

            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                add_chat_message("assistant", error_msg, error=str(e))

    # Rerun to update display
    st.rerun()

# ============================================================================
# Initial Welcome Message
# ============================================================================

if not st.session_state.chat_history:
    with st.chat_message("assistant"):
        st.write("""
        👋 Hey there! I'm your AI fitness coach.

        I can help you:
        - **Track your progress** ("How's my bench press looking?")
        - **Answer questions** ("How many leg workouts did I do this month?")
        - **Give recommendations** ("What should I do today?")
        - **Start workouts** ("Let's do a push workout" or "I want to workout but no barbell")
        - **Chat about fitness** ("Tell me about progressive overload")

        What would you like to know?
        """)
