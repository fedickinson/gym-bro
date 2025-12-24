"""
Chat Agent - Conversational ReAct agent with data access and workout planning.

This agent combines the friendly personality of the chat chain with the power
of tools to access workout data and trigger workout sessions.

Analogy: Like a personal trainer who can:
- Have casual conversations and provide motivation
- Look up your workout history when needed
- Answer questions about your progress
- Help you plan and start workouts
- Make recommendations based on your training data

They're conversational AND knowledgeable - best of both worlds!
"""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from src.tools.query_tools import (
    search_workouts,
    get_exercise_history,
    calculate_progression
)
from src.tools.recommend_tools import (
    get_weekly_split_status,
    suggest_next_workout
)
from src.tools.session_tools import start_workout_session


# ============================================================================
# System Prompt - The "Job Description" for our Chat Agent
# ============================================================================

CHAT_AGENT_PROMPT = """You are Gym Bro, an AI fitness coach who is both conversational AND knowledgeable about the user's training data.

Your personality:
- Supportive and motivating, never judgmental
- Celebrates all movement (gym, classes, walks, climbing, anything!)
- Believes consistency beats perfection
- No guilt for missed workouts - life happens
- Uses casual, friendly language (like a workout buddy)

Your capabilities:
1. **General conversation**: Answer fitness questions, provide motivation, discuss training concepts
2. **Data access**: Look up the user's workout history, progression, and training patterns
3. **Recommendations**: Suggest what to train based on their weekly split and recent workouts
4. **Planning**: Help them plan and start workout sessions

Your tools:
- search_workouts: Find workouts by keyword, exercise, or type in recent history
- get_exercise_history: Get weight/rep progression for a specific exercise
- calculate_progression: Calculate stats like trend, PR, and average weekly increase
- get_weekly_split_status: See what's done this week and what's remaining
- suggest_next_workout: Get AI suggestion based on rotation and weekly targets
- start_workout_session: Create a workout planning session (use when user wants to start a workout)

**CRITICAL RULES**:
1. **NEVER guess or make up workout data** - Always use tools for data questions
2. **Use tools when needed** - If user asks about their history, use the appropriate tool
3. **Be transparent** - Mention when you're checking their data (e.g., "Let me check your workout history...")
4. **Stay conversational** - Even when using tools, maintain friendly tone
5. **Check weekly split first** - When recommending workouts, ALWAYS call get_weekly_split_status() first

**Example interactions**:

User: "How are you?"
→ NO tools needed, just respond warmly

User: "What did I bench last week?"
→ Think: "I need their bench press history"
→ Use: get_exercise_history(exercise="bench press", days=14)
→ Respond: "Let me check your recent bench sessions... [analyze results]"

User: "What should I train today?"
→ Think: "I need to check their weekly split status first"
→ Use: get_weekly_split_status()
→ Analyze: See what's done, what's remaining
→ Respond: "Looking at your week... [make recommendation based on data]"

User: "I'm feeling tired today"
→ NO tools needed, just provide supportive advice

User: "Am I making progress on squats?"
→ Think: "I need progression data for squats"
→ Use: calculate_progression(exercise="squat")
→ Respond: "Let me pull up your squat progression... [analyze and celebrate gains]"

User: "Let's do a push workout"
→ Think: "User wants to start a workout session"
→ Use: start_workout_session(workout_type="Push")
→ Respond: "Awesome! I've created your Push workout with X exercises. Click the button below to start logging!"

User: "I want to workout but I don't have a barbell today"
→ Think: "User wants to workout with equipment constraint"
→ Use: start_workout_session(equipment_unavailable="Barbell")
→ Respond: "No problem! I've created a workout avoiding barbell exercises. Ready to start?"

**Temperature setting**: You run at low temperature (0.2) to ensure accurate data handling. Be warm and friendly, but prioritize factual accuracy over creativity.

**Keep responses**:
- Concise (2-5 sentences usually, unless analyzing data)
- Encouraging and positive
- Data-driven when answering history questions
- Honest when data is missing

Remember: You're a coach who KNOWS their athlete's training history and can have a real conversation about it!
"""


# ============================================================================
# Chat Agent Builder
# ============================================================================

class ChatAgent:
    """
    A conversational ReAct agent with workout data access.

    Combines:
    - Friendly chat personality (like chat_chain.py)
    - Tool access for data (like query_agent.py and recommend_agent.py)

    Architecture:
        User Message
             ↓
        Agent Thinks → Need data? → Use Tool → Observe Result
             ↓                           ↑___________|
        Conversational Response    (repeat as needed)

    This gives us the best of both worlds:
    - Can chat naturally about general fitness topics
    - Can answer specific questions about user's data
    - Can provide personalized recommendations
    """

    def __init__(self, model_name: str = "claude-haiku-4-5-20251001"):
        """
        Initialize the chat agent.

        Args:
            model_name: Which Claude model to use
                       Default: Haiku for faster responses and lower cost
                       Uses temperature=0.2 for accuracy while maintaining friendliness
        """
        # The LLM - using Haiku for performance and cost efficiency
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0.2  # Low for accuracy, but not 0 to maintain conversational tone
        )

        # The tools this agent can use
        # Subset of Query + Recommend tools + Session tools
        self.tools = [
            search_workouts,
            get_exercise_history,
            calculate_progression,
            get_weekly_split_status,
            suggest_next_workout,
            start_workout_session
        ]

        # Create the ReAct agent using LangGraph
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=CHAT_AGENT_PROMPT
        )

    def chat(self, user_input: str, chat_history: list = None) -> str:
        """
        Send a message and get a conversational response.

        The agent will:
        1. Decide if it needs to use tools
        2. Use appropriate tools if needed (search history, check split status, etc.)
        3. Respond in a friendly, conversational way

        Args:
            user_input: What the user said
            chat_history: Optional list of previous messages for context
                         Format: [("user", "hi"), ("assistant", "hello!"), ...]

        Returns:
            The agent's response (as a string)

        Example:
            agent = ChatAgent()

            # General chat - no tools
            response = agent.chat("How are you?")
            # → "Hey! I'm doing great, thanks for asking! How's your training going?"

            # Data question - uses tools
            response = agent.chat("What did I bench last week?")
            # → Agent calls get_exercise_history, analyzes, responds with data

            # Recommendation - uses tools
            response = agent.chat("What should I train today?")
            # → Agent calls get_weekly_split_status, suggests based on rotation
        """
        # Build messages list with optional history
        messages = []

        if chat_history:
            for msg in chat_history:
                if isinstance(msg, tuple):
                    role, content = msg
                    messages.append((role, content))
                else:
                    # Handle dict format {role: ..., content: ...}
                    messages.append((msg.get("role", "user"), msg.get("content", "")))

        # Add current user message
        messages.append(("user", user_input))

        # Invoke the agent
        result = self.agent.invoke({
            "messages": messages
        })

        # Return the agent's final response
        return result["messages"][-1].content


# ============================================================================
# Factory Function
# ============================================================================

def get_chat_agent() -> ChatAgent:
    """
    Factory function to create a chat agent.

    Usage:
        agent = get_chat_agent()
        response = agent.chat("What should I train today?")
    """
    return ChatAgent()


# ============================================================================
# Quick Test
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of the chat agent.
    Run: python -m src.agents.chat_agent
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("🏋️ Gym Bro Chat Agent Test\n")
    print("=" * 60)

    agent = get_chat_agent()

    test_messages = [
        "Hey! How are you?",  # General chat - no tools
        "What did I do last week?",  # Data question - should use search_workouts
        "What should I train today?",  # Recommendation - should use get_weekly_split_status
        "Am I making progress on bench press?",  # Progression - should use calculate_progression
    ]

    for msg in test_messages:
        print(f"\n👤 User: {msg}")
        print("🤖 Agent is thinking...\n")

        try:
            response = agent.chat(msg)
            print(f"✅ Response: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 60)
