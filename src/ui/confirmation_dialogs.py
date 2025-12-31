"""
Confirmation Dialog Components for Gym Bro.

Provides reusable confirmation dialogs for delete operations.
Follows Streamlit modal dialog pattern with session state management.
"""

import streamlit as st
from datetime import datetime, date


# ============================================================================
# Single Workout Delete Confirmation
# ============================================================================

@st.dialog("Confirm Delete")
def show_delete_confirmation(workout: dict, on_confirm_callback: callable = None):
    """
    Show confirmation dialog for deleting a single workout.

    Simple "Are you sure?" confirmation with workout summary.

    Args:
        workout: The workout dict to delete (must have 'id', 'date', 'type')
        on_confirm_callback: Optional callback to execute after successful delete

    Returns:
        None (uses st.rerun() to refresh page after action)
    """
    # Extract workout info
    workout_id = workout.get('id', 'Unknown')
    workout_date = workout.get('date', 'Unknown')
    workout_type = workout.get('type', 'Unknown')
    exercise_count = len(workout.get('exercises', []))

    # Format date nicely
    try:
        if isinstance(workout_date, str):
            workout_date_obj = date.fromisoformat(workout_date)
            formatted_date = workout_date_obj.strftime("%b %d, %Y")
        else:
            formatted_date = str(workout_date)
    except (ValueError, AttributeError):
        formatted_date = str(workout_date)

    # Show warning message
    st.warning(f"**Are you sure you want to delete this workout?**")

    # Show workout summary
    st.markdown(f"""
    **{workout_type}** workout from **{formatted_date}**
    {exercise_count} exercise{'s' if exercise_count != 1 else ''}
    """)

    st.info("💡 Deleted workouts can be recovered for 30 days from the Trash page.")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("🗑️ Delete", type="primary", use_container_width=True):
            # Import here to avoid circular imports
            from src.data import delete_log

            success = delete_log(workout_id)

            if success:
                st.success("✅ Workout deleted successfully!")

                # Execute callback if provided
                if on_confirm_callback:
                    on_confirm_callback()

                # Brief pause to show success message
                import time
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Failed to delete workout. Please try again.")


# ============================================================================
# Bulk Delete Confirmation
# ============================================================================

@st.dialog("Confirm Bulk Delete")
def show_bulk_delete_confirmation(workouts: list[dict], on_confirm_callback: callable = None):
    """
    Show confirmation dialog for deleting multiple workouts.

    Displays count and summary of workouts to be deleted.

    Args:
        workouts: List of workout dicts to delete
        on_confirm_callback: Optional callback to execute after successful delete

    Returns:
        None (uses st.rerun() to refresh page after action)
    """
    workout_count = len(workouts)

    # Show warning message
    st.warning(f"**Are you sure you want to delete {workout_count} workout{'s' if workout_count != 1 else ''}?**")

    # Show workout summaries (limited to first 10 for readability)
    st.markdown("**Workouts to delete:**")

    display_limit = 10
    for i, workout in enumerate(workouts[:display_limit]):
        workout_date = workout.get('date', 'Unknown')
        workout_type = workout.get('type', 'Unknown')
        exercise_count = len(workout.get('exercises', []))

        # Format date
        try:
            if isinstance(workout_date, str):
                workout_date_obj = date.fromisoformat(workout_date)
                formatted_date = workout_date_obj.strftime("%b %d")
            else:
                formatted_date = str(workout_date)
        except (ValueError, AttributeError):
            formatted_date = str(workout_date)

        st.text(f"  • {formatted_date} - {workout_type} ({exercise_count} exercises)")

    # Show "and N more" if we truncated the list
    if workout_count > display_limit:
        st.text(f"  ... and {workout_count - display_limit} more")

    st.info("💡 Deleted workouts can be recovered for 30 days from the Trash page.")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("🗑️ Delete All", type="primary", use_container_width=True):
            # Import here to avoid circular imports
            from src.data import bulk_delete_logs

            # Extract IDs
            workout_ids = [w.get('id') for w in workouts if w.get('id')]

            result = bulk_delete_logs(workout_ids)

            deleted_count = result.get('deleted_count', 0)
            failed_ids = result.get('failed_ids', [])

            if deleted_count > 0:
                st.success(f"✅ Deleted {deleted_count} workout{'s' if deleted_count != 1 else ''} successfully!")

                if failed_ids:
                    st.warning(f"⚠️ Failed to delete {len(failed_ids)} workout(s).")

                # Execute callback if provided
                if on_confirm_callback:
                    on_confirm_callback()

                # Brief pause to show success message
                import time
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Failed to delete workouts. Please try again.")


# ============================================================================
# Permanent Delete Warning (for trash page)
# ============================================================================

@st.dialog("⚠️ Permanent Delete Warning")
def show_permanent_delete_warning(workout: dict, on_confirm_callback: callable = None):
    """
    Show strong warning dialog for permanently deleting a workout.

    This is for hard deletes from the trash page (irreversible).
    Uses more alarming language and requires explicit confirmation.

    Args:
        workout: The workout dict to permanently delete
        on_confirm_callback: Optional callback to execute after successful delete

    Returns:
        None (uses st.rerun() to refresh page after action)
    """
    # Extract workout info
    workout_id = workout.get('id', 'Unknown')
    workout_date = workout.get('date', 'Unknown')
    workout_type = workout.get('type', 'Unknown')
    exercise_count = len(workout.get('exercises', []))

    # Format date
    try:
        if isinstance(workout_date, str):
            workout_date_obj = date.fromisoformat(workout_date)
            formatted_date = workout_date_obj.strftime("%b %d, %Y")
        else:
            formatted_date = str(workout_date)
    except (ValueError, AttributeError):
        formatted_date = str(workout_date)

    # Show strong warning
    st.error("**⚠️ This action is PERMANENT and IRREVERSIBLE!**")

    st.markdown(f"""
    You are about to **permanently delete** this workout:

    **{workout_type}** from **{formatted_date}**
    {exercise_count} exercise{'s' if exercise_count != 1 else ''}

    **This cannot be undone!** The workout data will be lost forever.
    """)

    # Confirmation checkbox
    confirm = st.checkbox("I understand this action is permanent and cannot be undone")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("🔥 Delete Forever", type="primary", use_container_width=True, disabled=not confirm):
            if not confirm:
                st.error("Please confirm you understand this is permanent.")
            else:
                # Import here to avoid circular imports
                from src.data import delete_log_permanent

                success = delete_log_permanent(workout_id)

                if success:
                    st.success("✅ Workout permanently deleted.")

                    # Execute callback if provided
                    if on_confirm_callback:
                        on_confirm_callback()

                    # Brief pause to show success message
                    import time
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Failed to permanently delete workout. Please try again.")


# ============================================================================
# Bulk Permanent Delete Warning (for trash cleanup)
# ============================================================================

@st.dialog("⚠️ Permanent Bulk Delete Warning")
def show_bulk_permanent_delete_warning(workout_count: int, on_confirm_callback: callable = None):
    """
    Show warning dialog for permanently deleting old workouts from trash.

    Used by the cleanup function for 30+ day old deleted workouts.

    Args:
        workout_count: Number of workouts to permanently delete
        on_confirm_callback: Optional callback to execute after successful delete

    Returns:
        None (uses st.rerun() to refresh page after action)
    """
    # Show strong warning
    st.error(f"**⚠️ This will PERMANENTLY delete {workout_count} workout{'s' if workout_count != 1 else ''}!**")

    st.markdown(f"""
    You are about to **permanently delete all workouts** that have been in trash for 30+ days.

    **This cannot be undone!** These {workout_count} workout{'s' if workout_count != 1 else ''} will be lost forever.
    """)

    # Confirmation checkbox
    confirm = st.checkbox(f"I understand this will permanently delete {workout_count} workout{'s' if workout_count != 1 else ''}")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("🔥 Delete Forever", type="primary", use_container_width=True, disabled=not confirm):
            if not confirm:
                st.error("Please confirm you understand this is permanent.")
            else:
                # Import here to avoid circular imports
                from src.data import cleanup_old_deleted_logs

                result = cleanup_old_deleted_logs(days_threshold=30)
                deleted_count = result.get('deleted_count', 0)

                if deleted_count > 0:
                    st.success(f"✅ Permanently deleted {deleted_count} old workout{'s' if deleted_count != 1 else ''}.")

                    # Execute callback if provided
                    if on_confirm_callback:
                        on_confirm_callback()

                    # Brief pause to show success message
                    import time
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("No workouts were permanently deleted (none were old enough).")
                    import time
                    time.sleep(1)
                    st.rerun()
