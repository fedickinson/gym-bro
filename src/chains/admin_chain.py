"""
Admin Chain - Structured workflow for editing/deleting workout data.

This is a CHAIN (not an agent) because admin operations need to be:
- Predictable and structured
- Safe (no accidental deletions!)
- Confirmation-based

Analogy: Like a bank teller processing a withdrawal:
1. Identify what to change
2. Show current state
3. Confirm with user
4. Execute the change
5. Confirm completion

We DON'T want an agent "thinking creatively" about data modifications!
We want a structured, careful process.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.data import get_all_logs, update_log, delete_log


# ============================================================================
# System Prompts for Different Admin Operations
# ============================================================================

IDENTIFY_OPERATION_PROMPT = """You are helping identify what admin operation the user wants.

Based on their message, determine:
1. Operation type: "edit" or "delete"
2. Which workout they're referring to (latest, specific date, specific ID)
3. What they want to change (if editing)

User message: {user_input}

Respond with a structured summary:
- Operation: [edit/delete]
- Target: [which workout]
- Details: [what to change, if editing]

Be clear and concise."""


CONFIRM_OPERATION_PROMPT = """You are confirming an admin operation before it happens.

Current workout data:
{workout_data}

Proposed operation:
{operation_description}

Generate a confirmation message that:
1. Shows what will be changed/deleted
2. Asks "Are you sure? (yes/no)"

Keep it clear and direct. This is a safety check!"""


EXECUTE_RESPONSE_PROMPT = """You are confirming that an admin operation completed.

Operation: {operation_type}
Result: {result}

Generate a brief confirmation message:
- Acknowledge what was done
- Keep it friendly but concise

Examples:
- "✅ Deleted your workout from Dec 20th."
- "✅ Updated your bench press weight to 145 lbs."
- "❌ Couldn't find that workout. Want to try again?"
"""


# ============================================================================
# Admin Chain
# ============================================================================

class AdminChain:
    """
    A structured chain for safe admin operations.

    Unlike agents (which decide what to do), this chain follows a strict flow:
        User Request → Identify Op → Confirm → Execute → Respond

    This is safer for destructive operations!

    Note: In a real app, you'd add more safeguards:
    - User authentication
    - Audit logs
    - Undo capability
    - Backup before delete
    """

    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        """
        Initialize the admin chain.

        Args:
            model_name: Which Claude model to use
        """
        # LLM for parsing and generating messages
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0  # Need consistency for admin ops
        )

        # Prompt templates for different steps
        self.identify_prompt = ChatPromptTemplate.from_template(
            IDENTIFY_OPERATION_PROMPT
        )
        self.confirm_prompt = ChatPromptTemplate.from_template(
            CONFIRM_OPERATION_PROMPT
        )
        self.execute_prompt = ChatPromptTemplate.from_template(
            EXECUTE_RESPONSE_PROMPT
        )

        # Output parser
        self.parser = StrOutputParser()

    def identify_operation(self, user_input: str) -> str:
        """
        Step 1: Figure out what the user wants to do.

        Args:
            user_input: User's request (e.g., "delete my last workout")

        Returns:
            Structured description of the operation
        """
        chain = self.identify_prompt | self.llm | self.parser
        return chain.invoke({"user_input": user_input})

    def delete_workout(self, workout_id: str) -> dict:
        """
        Delete a workout by ID.

        Args:
            workout_id: The workout ID to delete

        Returns:
            Dict with success status and message
        """
        success = delete_log(workout_id)

        if success:
            return {
                "success": True,
                "message": f"Deleted workout {workout_id}"
            }
        else:
            return {
                "success": False,
                "message": f"Couldn't find workout {workout_id}"
            }

    def update_workout(self, workout_id: str, updates: dict) -> dict:
        """
        Update a workout with new data.

        Args:
            workout_id: The workout ID to update
            updates: Dict of fields to update

        Returns:
            Dict with success status and message
        """
        success = update_log(workout_id, updates)

        if success:
            return {
                "success": True,
                "message": f"Updated workout {workout_id}"
            }
        else:
            return {
                "success": False,
                "message": f"Couldn't find workout {workout_id}"
            }

    def get_latest_workout(self) -> dict | None:
        """
        Helper to get the most recent workout.

        Returns:
            The latest workout log, or None if no workouts
        """
        logs = get_all_logs()
        if not logs:
            return None

        # Sort by date (descending) and return first
        sorted_logs = sorted(logs, key=lambda x: x.get("date", ""), reverse=True)
        return sorted_logs[0]

    def handle_delete_latest(self) -> str:
        """
        Handle "delete my last workout" type requests.

        This is a convenience method for the common case.

        Returns:
            Response message
        """
        latest = self.get_latest_workout()

        if not latest:
            return "You don't have any workouts logged yet!"

        # Show what will be deleted
        workout_id = latest.get("id")
        date = latest.get("date")
        workout_type = latest.get("type")
        exercises = [ex.get("name") for ex in latest.get("exercises", [])]

        confirmation_msg = f"""I found your most recent workout:

**Date**: {date}
**Type**: {workout_type}
**Exercises**: {", ".join(exercises[:3])}{"..." if len(exercises) > 3 else ""}

⚠️  This will permanently delete this workout. Are you sure? (In a real app, you'd confirm here!)

For this demo, I'll show you how to delete it:
```python
from src.chains.admin_chain import get_admin_chain

admin = get_admin_chain()
result = admin.delete_workout("{workout_id}")
```
"""
        return confirmation_msg


# ============================================================================
# Factory Function
# ============================================================================

def get_admin_chain() -> AdminChain:
    """
    Factory function to create an admin chain.

    Usage:
        admin = get_admin_chain()

        # Delete latest workout
        result = admin.handle_delete_latest()

        # Delete specific workout
        result = admin.delete_workout("2024-12-20-001")

        # Update a workout
        result = admin.update_workout(
            "2024-12-20-001",
            {"notes": "Updated notes"}
        )
    """
    return AdminChain()


# ============================================================================
# Quick Test
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of the admin chain.
    Run: python -m src.chains.admin_chain
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("🏋️ Gym Bro Admin Chain Test\n")
    print("=" * 60)

    admin = get_admin_chain()

    # Test 1: Identify operation
    print("\n📋 Test 1: Identify Operation")
    user_input = "Delete my last workout"
    identification = admin.identify_operation(user_input)
    print(f"User: {user_input}")
    print(f"Identified:\n{identification}\n")

    # Test 2: Show latest workout (but don't delete)
    print("\n📋 Test 2: Show Latest Workout (for deletion)")
    result = admin.handle_delete_latest()
    print(result)

    print("\n" + "=" * 60)
    print("\n💡 Note: In a real app, you'd add:")
    print("   - User confirmation dialogs")
    print("   - Undo capability")
    print("   - Audit logging")
    print("   - Backup before delete")
