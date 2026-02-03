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
import httpx


def record_and_transcribe() -> str | None:
    """
    Record audio and transcribe using Whisper API.

    Returns:
        Transcribed text, or None if recording not started/failed
    """
    st.subheader("🎙️ Record Your Workout")
    st.caption("Tap to start, speak your workout, tap again to stop")

    # Initialize recorder key counter if not exists
    if 'audio_recorder_key' not in st.session_state:
        st.session_state.audio_recorder_key = 0

    # Display audio recorder with dynamic key to force reset
    audio_bytes = audio_recorder(
        key=f"audio_recorder_{st.session_state.audio_recorder_key}",
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
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OpenAI API key not configured")
        st.warning("💡 Audio transcription requires OPENAI_API_KEY in app settings")
        st.info("For now, use the text input below to log your workout")
        return None

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
        client = openai.OpenAI()

        with st.spinner("Transcribing your audio... 🎙️"):
            with open(tmp_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )

        transcribed_text = transcription.text

        # Check if transcription is empty
        if not transcribed_text.strip():
            st.error("❌ Couldn't hear anything - try speaking louder")
            return None

        # Show what was heard
        st.success("✅ Transcription complete!")
        st.info(f"**You said:** {transcribed_text}")

        return transcribed_text

    except httpx.ConnectError:
        st.error("❌ Cannot connect to OpenAI API")
        st.warning("💡 Check your OPENAI_API_KEY in app settings or network connection")
        st.info("For now, use the text input below to log your workout")
        return None

    except (httpx.TimeoutException, httpx.ReadTimeout, httpx.ConnectTimeout):
        st.error("❌ OpenAI API request timed out")
        st.warning("💡 Network connection issue - try again or use text input")
        return None

    except openai.APIError as e:
        st.error(f"❌ OpenAI API error: {str(e)}")
        st.warning("💡 Try typing your workout instead (see below)")
        return None

    except Exception as e:
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
        User's typed input when submit button is clicked
    """
    st.subheader("⌨️ Or Type Your Workout")

    # Text area for input
    manual_text = st.text_area(
        "Workout notes",
        placeholder=placeholder,
        height=150,
        help="Enter your exercises with sets, reps, and weights. Natural language works!",
        key="manual_workout_input"
    )

    # Submit button for mobile (large touch target)
    if st.button("✅ Submit Workout", key="submit_manual_workout", use_container_width=True, type="primary"):
        if manual_text and manual_text.strip():
            # Store in session state to persist the submission
            st.session_state.submitted_manual_workout = manual_text
            return manual_text

    # Return submitted text from session state if it exists
    if 'submitted_manual_workout' in st.session_state:
        return st.session_state.submitted_manual_workout

    return ""


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

    # IMPORTANT: We're now outside the column context here
    # Priority: transcription > manual input > cached transcription
    if transcription:
        # Clear any submitted manual workout when new audio is recorded
        if 'submitted_manual_workout' in st.session_state:
            del st.session_state.submitted_manual_workout
        return transcription
    elif manual_input and manual_input.strip():
        # User submitted manual text via button
        # Clear cached transcription if user types instead
        if 'cached_transcription' in st.session_state:
            del st.session_state.cached_transcription
        return manual_input
    elif 'cached_transcription' in st.session_state:
        # Return cached transcription from previous recording
        return st.session_state.cached_transcription
    else:
        return None
