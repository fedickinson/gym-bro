"""
Query Agent - ReAct agent for answering questions about workout history.

This is the AGENT pattern - much more powerful than a simple chain!

Analogy: Like a research librarian who can:
- Search through your workout logs
- Calculate statistics and trends
- Compare exercises
- Pull up specific historical data

They THINK about what info they need, USE TOOLS to get it, then ANSWER.
This is called the "ReAct" pattern (Reasoning + Acting).
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from src.tools.query_tools import QUERY_TOOLS


# ============================================================================
# System Prompt - The "Job Description" for our Query Agent
# ============================================================================

QUERY_AGENT_PROMPT = """You are a fitness data analyst helping users explore their workout history.

Your job: Answer questions about the user's workout data using the tools available to you.

Your tools:
- search_workouts: Find workouts by keyword, exercise, or type
- get_exercise_history: Get weight/rep history for a specific exercise
- calculate_progression: Calculate stats like trend, PR, and avg increase
- compare_exercises: Compare progression between two exercises
- get_workout_count: Count workouts in a time period

Guidelines:
- Use tools to look up data - don't guess or make up information
- If you need specific data, use the appropriate tool
- Explain what you find in a clear, encouraging way
- Celebrate progress! "Your bench went from 115 to 135 - that's 20 lbs in 2 months!"
- If data is missing, say so honestly: "I don't see any squat workouts in the last 90 days"

Example reasoning process:
User asks: "What's my bench press PR?"
1. Think: "I need to search for bench press exercises and find the max weight"
2. Use tool: get_exercise_history(exercise="bench press", days=180)
3. Analyze results: Find the highest weight across all sessions
4. Answer: "Your bench press PR is 135 lbs from December 20th!"

Keep responses concise and actionable. Focus on the data, not fluff.
"""


# ============================================================================
# Query Agent Builder
# ============================================================================

class QueryAgent:
    """
    A ReAct agent that can search and analyze workout data.

    Architecture:

        User Question
             ↓
        Agent Thinks → Need tool? → Use Tool → Observe Result
             ↓                           ↑___________|
        Answer                         (repeat as needed)

    This is MUCH more powerful than a simple chain because it can:
    - Decide which tools to use
    - Use multiple tools in sequence
    - Reason about the results

    But it's also:
    - Slower (multiple LLM calls)
    - More expensive (more tokens)
    - Can make mistakes (might use wrong tool)
    """

    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        """
        Initialize the query agent.

        Args:
            model_name: Which Claude model to use
                       Note: We use temperature=0 for agents (consistent, logical)
        """
        # The LLM - note we use temperature=0 for agents (need consistency!)
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0  # Agents need to be logical and consistent
        )

        # The tools this agent can use
        # These were already defined in src/tools/query_tools.py
        self.tools = QUERY_TOOLS

        # Create the agent using LangGraph's prebuilt ReAct agent
        # This handles the ReAct loop (think → act → observe → repeat)
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=QUERY_AGENT_PROMPT  # System prompt
        )

    def query(self, user_input: str) -> str:
        """
        Answer a question about workout data.

        Args:
            user_input: The user's question

        Returns:
            The agent's answer (as a string)

        Example:
            agent = QueryAgent()
            answer = agent.query("What's my bench press PR?")
            # Agent will:
            # 1. Think: "I need bench press history"
            # 2. Use: get_exercise_history(exercise="bench")
            # 3. Analyze: Find max weight
            # 4. Answer: "Your PR is 135 lbs!"
        """
        # Invoke the agent with the user's message
        result = self.agent.invoke({
            "messages": [("user", user_input)]
        })

        # The agent returns a state dict with 'messages' list
        # The last message is the agent's response
        return result["messages"][-1].content


# ============================================================================
# Factory Function
# ============================================================================

def get_query_agent() -> QueryAgent:
    """
    Factory function to create a query agent.

    Usage:
        agent = get_query_agent()
        answer = agent.query("How many workouts did I do in December?")
    """
    return QueryAgent()


# ============================================================================
# Quick Test
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of the query agent.
    Run: python -m src.agents.query_agent
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("🏋️ Gym Bro Query Agent Test\n")
    print("=" * 60)

    agent = get_query_agent()

    test_questions = [
        "How many workouts did I do in the last 30 days?",
        "Show me my bench press history",
    ]

    for question in test_questions:
        print(f"\n👤 User: {question}")
        print("🤖 Agent is thinking and using tools...\n")

        try:
            answer = agent.query(question)
            print(f"\n✅ Answer: {answer}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 60)
