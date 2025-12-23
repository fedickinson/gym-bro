"""
Audio Recording and Transcription Component.

Provides audio recording via streamlit-audiorecorder and transcription via Whisper API.
Critical for mobile-first gym logging experience.
"""

import streamlit as st
from audio_recorder_streamlit import audio_recorder
import tempfile
import openai
from pathlib import Path
import os
from src.ui.loading_overlay import show_loading_overlay, hide_loading_overlay


def record_and_transcribe() -> str | None:
    """
    Record audio and transcribe using Whisper API.

    Returns:
        Transcribed text, or None if recording not started/failed
    """
    st.subheader("🎙️ Record Your Workout")
    st.caption("Tap to start, speak your workout, tap again to stop")

    # Display audio recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e74c3c",  # Red during recording
        neutral_color="#4CAF50",    # Green when ready
        icon_name="microphone",
        icon_size="3x",
        pause_threshold=2.0,  # Auto-stop after 2 seconds of silence
    )

    if audio_bytes is None:
        return None

    # Audio was recorded - now transcribe
    return transcribe_audio(audio_bytes)


def transcribe_audio(audio_bytes: bytes) -> str | None:
    """
    Transcribe audio bytes using OpenAI Whisper API.

    Args:
        audio_bytes: Audio data in bytes

    Returns:
        Transcribed text, or None if transcription failed
    """
    # Check if audio is too short
    if len(audio_bytes) < 1000:  # Less than 1KB
        st.error("❌ Audio too short - please try again")
        return None

    # Save to temporary file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        # Transcribe with Whisper API
        # Show loading overlay (Step 1 of 2)
        show_loading_overlay(
            step=1,
            total=2,
            message="Transcribing your audio... 🎙️"
        )

        client = openai.OpenAI()

        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )

        transcribed_text = transcription.text

        # Hide overlay
        hide_loading_overlay()

        # Check if transcription is empty
        if not transcribed_text.strip():
            st.error("❌ Couldn't hear anything - try speaking louder")
            return None

        # Show what was heard
        st.success("✅ Transcription complete!")
        st.info(f"**You said:** {transcribed_text}")

        return transcribed_text

    except openai.APIError as e:
        hide_loading_overlay()
        st.error(f"❌ OpenAI API error: {str(e)}")
        st.warning("💡 Try typing your workout instead (see below)")
        return None

    except Exception as e:
        hide_loading_overlay()
        st.error(f"❌ Transcription failed: {str(e)}")
        st.warning("💡 Try typing your workout instead (see below)")
        return None

    finally:
        # Cleanup temp file
        try:
            if 'tmp_path' in locals():
                Path(tmp_path).unlink(missing_ok=True)
        except:
            pass  # Ignore cleanup errors


def text_input_fallback(placeholder: str = "Example: bench 135x8x3, overhead 95x8x3") -> str:
    """
    Fallback text input if audio fails or user prefers typing.

    Args:
        placeholder: Placeholder text for the input

    Returns:
        User's typed input
    """
    st.subheader("⌨️ Or Type Your Workout")
    return st.text_area(
        "Workout notes",
        placeholder=placeholder,
        height=150,
        help="Enter your exercises with sets, reps, and weights. Natural language works!"
    )


def combined_input() -> str | None:
    """
    Combined audio + text input component.

    Shows both audio recording and text fallback options.
    Returns whichever input method the user provides.

    Returns:
        Transcribed/typed workout text, or None if no input
    """
    col1, col2 = st.columns([1, 1])

    transcription = None
    manual_input = None

    with col1:
        transcription = record_and_transcribe()

        # Cache transcription in session state so it persists across reruns
        if transcription:
            st.session_state.cached_transcription = transcription

    with col2:
        manual_input = text_input_fallback()

    # Return cached transcription if available and no new input
    if transcription:
        return transcription
    elif manual_input and manual_input.strip():
        # Clear cached transcription if user types instead
        if 'cached_transcription' in st.session_state:
            del st.session_state.cached_transcription
        return manual_input
    elif 'cached_transcription' in st.session_state:
        # Return cached transcription from previous recording
        return st.session_state.cached_transcription
    else:
        return None
