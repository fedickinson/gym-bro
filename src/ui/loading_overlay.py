"""
Full-page loading overlay for blocking UI during async operations.

Provides a professional, animated loading screen with step-by-step
progress indicators and motivational messages.
"""

import streamlit as st
import random


def show_loading_overlay(step: int, total: int, message: str):
    """
    Display a full-page loading overlay with progress.

    Args:
        step: Current step number (1-indexed)
        total: Total number of steps
        message: Message to display (e.g., "Transcribing audio...")

    Example:
        show_loading_overlay(1, 2, "Transcribing your audio... 🎙️")
        # Do work
        show_loading_overlay(2, 2, "Understanding your workout... 🧠")
        # More work
        hide_loading_overlay()
    """

    progress_percent = (step / total) * 100

    # Motivational phrases
    motivational_phrases = [
        "Let's go! 💪",
        "You got this! 🔥",
        "Beast mode activated! 🦍",
        "Crushing it! ⚡",
        "One rep at a time! 🏋️"
    ]
    motivation = random.choice(motivational_phrases)

    # CSS + HTML for full-page overlay
    overlay_html = f"""
    <style>
    .gym-bro-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.85);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(4px);
    }}

    .gym-bro-overlay-content {{
        background: #1E1E1E;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        max-width: 400px;
        border: 2px solid #4CAF50;
        box-shadow: 0 8px 32px rgba(76, 175, 80, 0.3);
    }}

    .gym-bro-spinner {{
        border: 4px solid #333;
        border-top: 4px solid #4CAF50;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        animation: spin 1s linear infinite;
        margin: 0 auto 1.5rem auto;
    }}

    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}

    .gym-bro-overlay h2 {{
        color: #4CAF50;
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
    }}

    .gym-bro-overlay-step {{
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }}

    .gym-bro-overlay-message {{
        color: #fff;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }}

    .gym-bro-progress-bar {{
        width: 100%;
        height: 8px;
        background: #333;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 1rem;
    }}

    .gym-bro-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, #4CAF50, #45a049);
        width: {progress_percent}%;
        transition: width 0.3s ease;
    }}

    /* Mobile optimizations */
    @media (max-width: 768px) {{
        .gym-bro-overlay-content {{
            max-width: 90vw;
            padding: 1.5rem;
        }}

        .gym-bro-overlay h2 {{
            font-size: 1.4rem;
        }}

        .gym-bro-spinner {{
            width: 50px;
            height: 50px;
        }}

        .gym-bro-overlay-message {{
            font-size: 1rem;
        }}
    }}
    </style>

    <div class="gym-bro-overlay">
        <div class="gym-bro-overlay-content">
            <div class="gym-bro-spinner"></div>
            <h2>{motivation}</h2>
            <div class="gym-bro-overlay-step">Step {step} of {total}</div>
            <div class="gym-bro-overlay-message">{message}</div>
            <div class="gym-bro-progress-bar">
                <div class="gym-bro-progress-fill"></div>
            </div>
        </div>
    </div>
    """

    st.markdown(overlay_html, unsafe_allow_html=True)


def hide_loading_overlay():
    """Remove the loading overlay."""
    st.markdown("""
    <script>
    document.querySelectorAll('.gym-bro-overlay').forEach(el => el.remove());
    </script>
    """, unsafe_allow_html=True)
