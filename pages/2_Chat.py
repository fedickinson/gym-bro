"""
Chat Page - Conversational interface with the AI fitness coach.

Routes questions to Query Agent, Recommend Agent, or Chat Chain based on intent.
"""

import streamlit as st
from src.ui.session import init_session_state, add_chat_message, clear_chat_history, get_orchestrator
from src.ui.navigation import render_bottom_nav

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
# Page Content
# ============================================================================

st.title("💬 Chat with Your Coach")
st.caption("Ask questions about your workouts, get recommendations, or just chat!")

# ============================================================================
# Sidebar Controls
# ============================================================================

with st.sidebar:
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
    st.caption("• Am I balanced in my training?")
    st.caption("• What's progressive overload?")

    st.divider()
    st.caption(f"Total messages: {len(st.session_state.chat_history)}")

# ============================================================================
# Chat Display
# ============================================================================

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg['role']):
        st.write(msg['content'])

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
                response = orchestrator.chat(user_input)

                # Display response
                st.write(response)

                # Add assistant message to history with metadata
                # (orchestrator.chat doesn't return agent info, but we can add it later if needed)
                add_chat_message("assistant", response, agent="orchestrator")

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
        - **Chat about fitness** ("Tell me about progressive overload")

        What would you like to know?
        """)
