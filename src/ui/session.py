"""
Session State Management for Gym Bro Streamlit App.

This module handles all session state initialization and management.
CRITICAL: Orchestrator is initialized ONCE to avoid re-creating agents on every interaction.
"""

import streamlit as st
from src.agents.main import GymBroOrchestrator


def init_session_state():
    """
    Initialize all session state variables.

    Call this at the start of EVERY page to ensure state is initialized.
    Uses st.session_state to persist data across page interactions.
    """

    # ========================================================================
    # Core Orchestrator (Initialize ONCE - most important!)
    # ========================================================================
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = GymBroOrchestrator()

    # ========================================================================
    # Navigation
    # ========================================================================
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'

    # ========================================================================
    # Chat State
    # ========================================================================
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        # Format: [{"role": "user"|"assistant", "content": str}, ...]

    # ========================================================================
    # Log Workflow State (for multi-step workflow)
    # ========================================================================
    if 'log_state' not in st.session_state:
        st.session_state.log_state = 'planning_chat'  # planning_chat | session_active | preview | saved

    if 'log_workflow_state' not in st.session_state:
        st.session_state.log_workflow_state = None  # LangGraph state dict

    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

    if 'audio_transcription' not in st.session_state:
        st.session_state.audio_transcription = None

    # ========================================================================
    # Session-Based Workout Logging (session-only mode)
    # ========================================================================
    if 'workout_session' not in st.session_state:
        st.session_state.workout_session = None  # Current workout session state
        # When active, contains SessionWithPlanState:
        # {
        #     "session_id": str,
        #     "started_at": str,
        #     "suggested_type": str,  # AI recommendation
        #     "planned_template": dict,  # Adaptive template
        #     "plan_adjustments": list[dict],  # Chat modifications
        #     "equipment_unavailable": list[str] | None,
        #     "accumulated_exercises": list[dict],
        #     "actual_workout_type": str,
        #     ...
        # }

    # ========================================================================
    # History Page Filters
    # ========================================================================
    if 'filter_type' not in st.session_state:
        st.session_state.filter_type = 'All'

    if 'filter_days' not in st.session_state:
        st.session_state.filter_days = 30

    if 'filter_exercise' not in st.session_state:
        st.session_state.filter_exercise = ''

    if 'expanded_log_id' not in st.session_state:
        st.session_state.expanded_log_id = None

    # ========================================================================
    # Progress Page State
    # ========================================================================
    if 'selected_exercise' not in st.session_state:
        st.session_state.selected_exercise = 'Bench Press'

    if 'progress_days' not in st.session_state:
        st.session_state.progress_days = 90

    if 'volume_grouping' not in st.session_state:
        st.session_state.volume_grouping = 'week'  # week | month

    # ========================================================================
    # Responsive Design Detection
    # ========================================================================
    if 'viewport_width' not in st.session_state:
        st.session_state.viewport_width = 1024  # Default to desktop


# ============================================================================
# Helper Functions for State Management
# ============================================================================

def reset_log_workflow():
    """Reset all log workflow state to start fresh."""
    st.session_state.log_state = 'planning_chat'
    st.session_state.log_workflow_state = None
    st.session_state.edit_mode = False
    st.session_state.audio_transcription = None
    # Clear cached transcription from audio input
    if 'cached_transcription' in st.session_state:
        del st.session_state.cached_transcription


def reset_workout_session():
    """
    Reset workout session state.

    Use this when canceling a session or after saving.
    """
    st.session_state.workout_session = None
    st.session_state.log_state = 'planning_chat'
    # Also clear cached transcription
    if 'cached_transcription' in st.session_state:
        del st.session_state.cached_transcription


def add_chat_message(role: str, content: str, **metadata):
    """
    Add a message to chat history.

    Args:
        role: "user" or "assistant"
        content: Message content
        **metadata: Optional metadata (agent, tool_calls, error, etc.)
    """
    from datetime import datetime

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }

    # Add any additional metadata
    message.update(metadata)

    st.session_state.chat_history.append(message)


def clear_chat_history():
    """Clear all chat history."""
    st.session_state.chat_history = []


def is_mobile() -> bool:
    """
    Check if the current viewport is mobile-sized.

    Returns:
        True if viewport width < 768px (mobile), False otherwise
    """
    return st.session_state.viewport_width < 768


def get_orchestrator() -> GymBroOrchestrator:
    """
    Get the orchestrator instance (guaranteed to exist).

    Returns:
        GymBroOrchestrator instance
    """
    return st.session_state.orchestrator
