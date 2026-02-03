"""
Main Orchestrator - Routes user input to the appropriate handler.

This is the "conductor" that coordinates all the other components.

Analogy: Orchestra Conductor
- Listens to the request
- Classifies the intent (which section should play?)
- Routes to the right handler (cues that section)
- Returns the response (beautiful music!)

Architecture:
    User Input
       ↓
    Intent Router (classify)
       ↓
    ┌─────┬────────┬───────────┬───────┐
    ↓     ↓        ↓           ↓       ↓
  Chat  Query  Recommend    Admin   (Log Graph - Phase 3)
  Chain Agent   Agent       Chain
    ↓     ↓        ↓           ↓
    └─────┴────────┴───────────┘
              ↓
         Response
"""

from src.agents.router import IntentRouter, quick_route
from src.chains.chat_chain import ChatChain
from src.agents.chat_agent import ChatAgent
from src.agents.query_agent import QueryAgent
from src.agents.recommend_agent import RecommendAgent
from src.chains.admin_chain import AdminChain
from src.agents.log_graph import start_workout_log, continue_workout_log


class GymBroOrchestrator:
    """
    Main orchestrator that routes user input to specialized handlers.

    This is the ENTRY POINT for the entire agentic system.

    Components:
    - Intent Router: Classifies user input → intent
    - Chat Agent: Handles conversation with data access and workout planning
    - Query Agent: Answers questions about workout history
    - Recommend Agent: Provides workout recommendations
    - Admin Chain: Handles edit/delete operations
    - Log Graph: Multi-step workout logging with confirmation
    """

    def __init__(self):
        """
        Initialize the orchestrator and all handlers.

        This creates instances of:
        - Router (for intent classification)
        - Chat Agent (for conversation with data access)
        - Query Agent (for data queries)
        - Recommend Agent (for planning)
        - Admin Chain (for admin operations)
        """
        print("🏋️  Initializing Gym Bro AI Coach...")

        # Intent classification
        self.router = IntentRouter()

        # Handlers for each intent
        self.chat_agent = ChatAgent()  # New: Conversational agent with tools
        self.chat_chain = ChatChain()  # Kept for backward compatibility
        self.query_agent = QueryAgent()
        self.recommend_agent = RecommendAgent()
        self.admin_chain = AdminChain()

        print("✅ All systems ready!\n")

    def process_message(self, user_input: str, chat_history: list = None) -> dict:
        """
        Main entry point - process a user message and return a response.

        Args:
            user_input: What the user said
            chat_history: Optional list of previous messages for context
                         Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]

        Returns:
            Dict with:
            - intent: The classified intent
            - response: The handler's response
            - handler: Which handler was used
            - session_data: Session data if workout session was created (or None)

        Example:
            orchestrator = GymBroOrchestrator()

            result = orchestrator.process_message("What's my bench PR?")
            # {
            #   "intent": "query",
            #   "handler": "query_agent",
            #   "response": "Your bench press PR is 135 lbs!",
            #   "session_data": None
            # }

            result = orchestrator.process_message("Let's do legs", chat_history=[...])
            # {
            #   "intent": "chat",
            #   "handler": "chat_agent",
            #   "response": "Perfect! I've created...",
            #   "session_data": {...}  # Full session state
            # }
        """
        # Step 1: Classify intent
        # Try quick pattern matching first (faster!)
        intent = quick_route(user_input)

        if intent is None:
            # Fall back to full LLM classification
            intent = self.router.route(user_input)

        print(f"🎯 Intent: {intent}")

        # Step 2: Route to appropriate handler
        handler_name, response, session_data, edit_context = self._route_to_handler(intent, user_input, chat_history)

        # Step 3: Return structured result
        return {
            "intent": intent,
            "handler": handler_name,
            "response": response,
            "session_data": session_data,
            "edit_context": edit_context
        }

    def _route_to_handler(self, intent: str, user_input: str, chat_history: list = None) -> tuple:
        """
        Internal method to route to the correct handler based on intent.

        Args:
            intent: The classified intent (log, query, recommend, chat, admin)
            user_input: The user's message
            chat_history: Optional conversation history for context

        Returns:
            Tuple of (handler_name, response, session_data, edit_context)
        """
        try:
            if intent == "chat":
                result = self.chat_agent.chat(user_input, chat_history=chat_history)
                # ChatAgent now returns dict with response + session_data + edit_context
                response = result.get("response") if isinstance(result, dict) else result
                session_data = result.get("session_data") if isinstance(result, dict) else None
                edit_context = result.get("edit_context") if isinstance(result, dict) else None
                return ("chat_agent", response, session_data, edit_context)

            elif intent == "query":
                response = self.query_agent.query(user_input)
                return ("query_agent", response, None, None)

            elif intent == "recommend":
                response = self.recommend_agent.recommend(user_input)
                return ("recommend_agent", response, None, None)

            elif intent == "admin":
                # For now, just use the delete latest demo
                response = self.admin_chain.handle_delete_latest()
                return ("admin_chain", response, None, None)

            elif intent == "log":
                # Phase 3: LangGraph workout logging!
                # Start the logging workflow
                state = start_workout_log(user_input)
                response = state["response"]

                # Note: In a real Streamlit app, we'd return the state
                # and wait for user confirmation. For CLI demo, we auto-approve.
                # See log_graph.py for full implementation.
                return ("log_graph", response, None, None)

            else:
                # Fallback to chat for unknown intents
                result = self.chat_agent.chat(user_input, chat_history=chat_history)
                response = result.get("response") if isinstance(result, dict) else result
                session_data = result.get("session_data") if isinstance(result, dict) else None
                edit_context = result.get("edit_context") if isinstance(result, dict) else None
                return ("chat_agent_fallback", response, session_data, edit_context)

        except Exception as e:
            # Error handling - return friendly error message
            return ("error", f"Oops! Something went wrong: {str(e)}", None, None)

    def chat(self, user_input: str) -> str:
        """
        Convenience method that just returns the response string.

        Most users will use this instead of process_message().

        Args:
            user_input: What the user said

        Returns:
            The response string

        Example:
            coach = GymBroOrchestrator()
            response = coach.chat("What should I do today?")
            print(response)
        """
        result = self.process_message(user_input)
        return result["response"]


# ============================================================================
# Factory Function
# ============================================================================

def get_gym_bro() -> GymBroOrchestrator:
    """
    Factory function to create the orchestrator.

    Usage:
        coach = get_gym_bro()
        response = coach.chat("What's my bench PR?")
    """
    return GymBroOrchestrator()


# ============================================================================
# Interactive Demo
# ============================================================================

def demo():
    """
    Interactive demo of the complete system.

    Run: python -m src.agents.main
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("=" * 70)
    print(" 🏋️  GYM BRO - AI FITNESS COACH (Phase 2 Demo)")
    print("=" * 70)
    print("\nThis demo shows all components working together:")
    print("  • Chat Chain - General conversation")
    print("  • Query Agent - Workout history questions")
    print("  • Recommend Agent - Workout planning")
    print("  • Admin Chain - Edit/delete operations")
    print("  • Intent Router - Automatic routing\n")
    print("=" * 70)

    # Create the orchestrator
    coach = get_gym_bro()

    # Test cases showing different intents
    test_messages = [
        ("Hey! How are you today?", "chat"),
        ("How many workouts did I do in December?", "query"),
        ("What should I work on today?", "recommend"),
        ("Delete my last workout", "admin"),
        ("Thanks for the help!", "chat"),
    ]

    for user_msg, expected_intent in test_messages:
        print(f"\n👤 User: {user_msg}")
        print(f"   (Expected intent: {expected_intent})")
        print("-" * 70)

        result = coach.process_message(user_msg)

        print(f"🎯 Classified: {result['intent']}")
        print(f"🔧 Handler: {result['handler']}")
        print(f"\n🤖 Response:\n{result['response']}\n")
        print("=" * 70)


if __name__ == "__main__":
    demo()
