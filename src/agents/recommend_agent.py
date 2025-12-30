"""
Recommend Agent - ReAct agent for workout recommendations and planning.

This agent helps users plan their training using weekly split tracking,
muscle balance analysis, and workout templates.

Analogy: Like a strategic workout planner who:
- Tracks your weekly split (Push/Pull/Legs rotation)
- Checks if you're balanced or missing muscle groups
- Suggests what workout to do next based on your program
- Pulls up workout templates when you need them

They THINK about your training program, USE TOOLS to check progress, then RECOMMEND.
"""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from src.tools.recommend_tools import RECOMMEND_TOOLS


# ============================================================================
# System Prompt - The "Job Description" for our Recommend Agent
# ============================================================================

RECOMMEND_AGENT_PROMPT = """You are an intelligent workout planning assistant.

Your job: Help users plan their training using their weekly split, workout history, and program design.

Your tools:
- get_weekly_split_status: See what's done this week and what's remaining (includes ab workout status)
- suggest_next_workout: Get a smart suggestion based on rotation and weekly targets
- get_last_workout_by_type: Find the most recent workout of a specific type
- check_muscle_balance: Analyze if any muscle groups are over/under trained
- get_workout_template: Pull up the template for a specific workout type
- get_abs_status: Check ab workout completion and spacing for this week

**CRITICAL: When the user mentions what they've done this week OR asks "what should I do today", you MUST call get_weekly_split_status() FIRST before making any recommendations. NEVER suggest a workout without checking the split status first.**

Guidelines:
- Focus on balance and consistency, not perfection
- Consider the user's weekly split rotation (Push/Pull/Legs/Upper/Lower)
- Celebrate what they've accomplished this week
- If they're behind on a workout type, gently suggest catching up
- Adapt to their situation (tired, busy, injured, etc.)
- Pull up templates when they're ready to start a workout

**IMPORTANT AB WORKOUT RULES:**
- Target: 2 ab sessions per week
- Spacing: No ab workouts on consecutive days (minimum 1 day rest between ab sessions)
- Timing: Abs are done AFTER the main workout on the same day (not a separate session)
- Catch-up: If behind on weekly ab target, prioritize suggesting abs
- Flexibility: If abs can be done today AND user is behind, strongly recommend including them

When suggesting a workout:
1. First recommend the main workout (e.g., "Do a Pull workout today")
2. Then check if abs should be included: "Also add abs after your Pull workout"
3. If abs can't be done today due to spacing, explain why briefly
4. If user is behind on abs AND spacing allows, emphasize catching up on abs

Example reasoning process:
User asks: "What should I do today? It's Friday and I've already done Push on Monday, Pull on Wednesday, and Legs on Thursday this week."

CORRECT approach:
1. Think: "User mentioned recent workouts. I MUST check weekly split status first."
2. Use tool: get_weekly_split_status()
3. Observe tool result: {"Push": 1/1, "Pull": 1/1, "Legs": 1/2, "Upper": 0/1, "Lower": 0/1, "next_in_rotation": "Upper"}
4. Think: "They've done Push, Pull, and Legs. Next in rotation is Upper, and they haven't done Upper yet this week."
5. Answer: "Great consistency this week! Based on your split, Upper is next in the rotation and you haven't done it yet this week. Want me to pull up your Upper day template?"

INCORRECT approach (DO NOT DO THIS):
1. Think: "They mentioned Push, Pull, Legs... so maybe Push next?"
2. Answer without checking tools first ❌

Simple example:
User asks: "What should I do today?"
1. Think: "I need to check their weekly split status"
2. Use tool: get_weekly_split_status()
3. Observe: "They've done Push and Pull, missing 2x Legs"
4. Think: "Legs is next in rotation and they need to catch up"
5. Answer: "Legs is up next! You've hit Push and Pull this week, but you're 0/2 on legs. Want me to pull up your leg day template?"

Ab workout example:
User asks: "What should I do today?"
1. Use tool: get_weekly_split_status()
2. Observe: "Push: 1/1, Pull: 1/1, Legs: 0/2, abs: 1/2"
3. Use tool: get_abs_status()
4. Observe: "can_do_today: true, behind: true, days_since_last: 3"
5. Think: "Legs is next, and they can add abs (behind on target, spacing OK)"
6. Answer: "Do a Legs workout today. You're 0/2 on legs this week! **Also:** You're at 1/2 on abs this week - add abs after your leg workout to stay on track!"

Keep recommendations encouraging and practical. It's okay to skip a workout if needed!
"""


# ============================================================================
# Recommend Agent Builder
# ============================================================================

class RecommendAgent:
    """
    A ReAct agent that helps plan workouts and training.

    Similar to QueryAgent, but focuses on:
    - Future planning (not past analysis)
    - Weekly split tracking
    - Muscle balance
    - Workout suggestions

    Architecture: Same ReAct loop as QueryAgent
        Think → Act → Observe → Respond
    """

    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        """
        Initialize the recommend agent.

        Args:
            model_name: Which Claude model to use
                       Uses temperature=0 for consistent logic
        """
        # The LLM - temperature=0 for consistent recommendations
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0  # Need logical, consistent planning
        )

        # The tools this agent can use
        # These were defined in src/tools/recommend_tools.py
        self.tools = RECOMMEND_TOOLS

        # Create the ReAct agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=RECOMMEND_AGENT_PROMPT  # System prompt
        )

    def recommend(self, user_input: str) -> str:
        """
        Get a workout recommendation or planning advice.

        Args:
            user_input: The user's request

        Returns:
            The agent's recommendation (as a string)

        Example:
            agent = RecommendAgent()
            suggestion = agent.recommend("What should I do today?")
            # Agent will:
            # 1. Check weekly split status
            # 2. See what's done/remaining
            # 3. Suggest the next workout in rotation
        """
        # Invoke the agent with the user's message
        result = self.agent.invoke({
            "messages": [("user", user_input)]
        })

        # Return the agent's response
        return result["messages"][-1].content


# ============================================================================
# Factory Function
# ============================================================================

def get_recommend_agent() -> RecommendAgent:
    """
    Factory function to create a recommend agent.

    Usage:
        agent = get_recommend_agent()
        suggestion = agent.recommend("What should I work on today?")
    """
    return RecommendAgent()


# ============================================================================
# Quick Test
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of the recommend agent.
    Run: python -m src.agents.recommend_agent
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("🏋️ Gym Bro Recommend Agent Test\n")
    print("=" * 60)

    agent = get_recommend_agent()

    test_questions = [
        "What should I do today?",
        "Am I overtraining any muscle groups?",
    ]

    for question in test_questions:
        print(f"\n👤 User: {question}")
        print("🤖 Agent is thinking and planning...\n")

        try:
            answer = agent.recommend(question)
            print(f"\n✅ Recommendation: {answer}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 60)
