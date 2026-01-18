"""
Database connection manager for Supabase.

Uses connection caching to reuse the client across Streamlit reruns.
"""

import os
from functools import lru_cache
from supabase.client import create_client, Client
import streamlit as st


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Get cached Supabase client (singleton).

    Uses LRU cache to reuse connection across Streamlit reruns.
    Falls back to environment variables if Streamlit secrets are not available.

    Returns:
        Supabase client instance

    Raises:
        ValueError: If credentials are missing
    """
    # Try Streamlit secrets first (for deployed app)
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except (FileNotFoundError, AttributeError):
        # Fall back to environment variables (for local development)
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials. "
            "Set SUPABASE_URL and SUPABASE_KEY in Streamlit secrets or environment variables."
        )

    return create_client(url, key)


def test_connection() -> bool:
    """
    Test the database connection.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        client = get_supabase_client()
        # Simple query to test connection
        client.table("workout_logs").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False
