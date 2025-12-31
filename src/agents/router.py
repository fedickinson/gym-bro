"""
Intent Router - Classifies user input and routes to appropriate handler.

This is the entry point for the agentic system. Uses Claude to classify
intent, then routes to the appropriate agent or chain.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.models import ClassifiedIntent, Intent


ROUTER_PROMPT = """You are an intent classifier for a fitness coaching app.

Classify the user's message into one of these intents:

- **log**: User wants to record a workout they ALREADY DID
  Examples: "Just did push day", "Logged 3x8 bench at 135", "Here's my workout..."
  NOTE: If talking about FUTURE workout, use CHAT instead!

- **query**: User is asking about their workout history or PAST data
  Examples: "What did I bench last time?", "How many workouts in October?", "Show my progress"

- **recommend**: RARELY USED - Only for passive suggestions with NO intent to start
  Examples: "What should I do today?" (asking, not doing), "Any recommendations?"
  CRITICAL: If user expresses ANY desire to workout, plan, or start → use CHAT instead!

- **admin**: User wants to edit, delete, or fix existing data
  Examples: "Fix my last workout", "Delete Tuesday's log", "Change the weight to 145"

- **chat**: DEFAULT for anything workout-related that isn't logging PAST workouts
  Use this for:
  - Planning: "I need a workout", "workout for tomorrow", "quick workout", "simple workout"
  - Starting: "Let's start", "Let's do it", "Let's begin", "I'm ready", "show me the plan"
  - Discussing: "What will we do?", "Tell me more", "I want details"
  - General: "How are you?", "Tell me about progressive overload", "Thanks!"
  - ANY workout with constraints: "I only have dumbbells", "no barbell", "at home"

  CRITICAL RULE: If user mentions they NEED, WANT, or are PLANNING a workout → CHAT!

User message: {user_input}

{format_instructions}
"""


class IntentRouter:
    """Routes user input to the appropriate handler."""
    
    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        self.llm = ChatAnthropic(model=model_name, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=ClassifiedIntent)
        self.prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
        
        self.chain = self.prompt | self.llm | self.parser
    
    def classify(self, user_input: str) -> ClassifiedIntent:
        """Classify user input into an intent category."""
        result = self.chain.invoke({
            "user_input": user_input,
            "format_instructions": self.parser.get_format_instructions()
        })
        return result
    
    def route(self, user_input: str) -> Intent:
        """Convenience method that just returns the intent string."""
        return self.classify(user_input).intent


# Quick routing without full classification (for simple cases)
# NOTE: Keep these VERY specific to avoid false matches
# When uncertain, return None to let the LLM classifier handle it
QUICK_PATTERNS = {
    "log": [
        "just did", "just finished", "here's my workout", "logged",
        "completed my workout", "finished my workout"
    ],
    "query": [
        "how many workouts", "what did i bench", "what did i squat",
        "show me my progress", "my workout history"
    ],
    "admin": [
        "delete my last workout", "fix my workout", "remove my log"
    ],
    "chat": [
        # Workout planning/starting phrases
        "let's start", "let's begin", "let's do", "lets do", "lets start",
        "i need a workout", "need a workout", "i want to workout",
        "quick workout", "simple workout", "i'm ready to",
        "only have dumbbells", "at home workout", "no barbell",
        "show me the plan", "tell me what we'll do", "what will we do",
        # General chat
        "how are you", "thank you", "thanks"
    ]
    # NOTE: "What should I do today?" removed from recommend - too ambiguous
    # Let LLM handle recommendation vs chat distinction for those cases
}


def quick_route(user_input: str) -> Intent | None:
    """
    Fast pattern-based routing for obvious cases.
    Returns None if uncertain (should use full classifier).
    """
    lower = user_input.lower()
    
    for intent, patterns in QUICK_PATTERNS.items():
        for pattern in patterns:
            if pattern in lower:
                return intent
    
    return None


def get_router() -> IntentRouter:
    """Factory function to get a router instance."""
    return IntentRouter()
