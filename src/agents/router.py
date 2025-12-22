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

- **log**: User wants to record a workout they did
  Examples: "Just did push day", "Logged 3x8 bench at 135", "Here's my workout..."
  
- **query**: User is asking about their workout history or data
  Examples: "What did I bench last time?", "How many workouts in October?", "Show my progress"
  
- **recommend**: User wants suggestions or planning help
  Examples: "What should I do today?", "Plan my week", "I'm tired, what's lighter?"
  
- **admin**: User wants to edit, delete, or fix existing data
  Examples: "Fix my last workout", "Delete Tuesday's log", "Change the weight to 145"
  
- **chat**: General conversation, motivation, questions about fitness
  Examples: "How are you?", "Is this a good routine?", "Thanks!", "Tell me about progressive overload"

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
QUICK_PATTERNS = {
    "log": [
        "just did", "finished", "here's my workout", "logged", 
        "completed", "worked out", "hit the gym"
    ],
    "recommend": [
        "what should i do", "plan my", "suggest", "recommendation",
        "what's next", "what workout"
    ],
    "query": [
        "how many", "what did i", "show me", "my progress",
        "last time", "history", "when did"
    ],
    "admin": [
        "fix", "delete", "remove", "edit", "change", "update"
    ]
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
