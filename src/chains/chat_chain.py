"""
Chat Chain - Simple conversational fitness coach.

This is the SIMPLEST pattern in our agentic architecture.
No tools, no data access, just direct LLM conversation.

Analogy: Like calling a fitness coach friend for motivation or general advice.
They can't look up your specific workout history, but they can chat, motivate,
and give general fitness advice.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


# ============================================================================
# System Prompt - The "Personality" of our Fitness Coach
# ============================================================================

CHAT_SYSTEM_PROMPT = """You are an encouraging, knowledgeable fitness coach chatbot.

Your personality:
- Supportive and motivating, never judgmental
- Celebrates all movement (gym, classes, walks, climbing, anything!)
- Believes consistency beats perfection
- No guilt for missed workouts - life happens
- Uses casual, friendly language (like a workout buddy)

What you can do:
- Provide general fitness advice and education
- Answer questions about exercises, form, programming
- Offer motivation and encouragement
- Discuss fitness concepts (progressive overload, splits, recovery, etc.)
- Have friendly conversations

What you CANNOT do:
- Look up the user's specific workout history (that's the Query Agent's job)
- Make personalized recommendations based on their data (that's the Recommend Agent's job)
- Log workouts (that's the Log Graph's job)
- Edit or delete data (that's the Admin Chain's job)

If the user asks for something you can't do, kindly redirect them:
- "I can't look up your history, but you could ask me to check your workout logs!"
- "For a personalized plan based on your weekly split, try asking 'what should I do today?'"

Keep responses concise (2-4 sentences usually). Be warm and human!
"""


# ============================================================================
# Chat Chain Builder
# ============================================================================

class ChatChain:
    """
    A simple conversational chain with no tools or data access.

    Architecture (LCEL - LangChain Expression Language):

        prompt → llm → output_parser

    That's it! Simple as a phone call.
    """

    def __init__(self, model_name: str = "claude-sonnet-4-20250514", temperature: float = 0.7):
        """
        Initialize the chat chain.

        Args:
            model_name: Which Claude model to use
            temperature: 0-1, how creative the responses are
                        0 = deterministic/consistent
                        1 = creative/varied
                        0.7 = good balance for friendly chat
        """
        # The LLM - the actual Claude model
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=temperature  # A bit creative for friendly conversation
        )

        # The prompt template
        # MessagesPlaceholder lets us inject conversation history
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", CHAT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{user_input}")
        ])

        # Output parser - just returns the string response
        self.output_parser = StrOutputParser()

        # Build the chain using LCEL (LangChain Expression Language)
        # The "|" operator pipes data from one step to the next
        # Like: prompt | llm | parser
        #       └─────→ input goes in, response comes out ─────→
        self.chain = self.prompt | self.llm | self.output_parser

    def chat(self, user_input: str, chat_history: list = None) -> str:
        """
        Send a message and get a response.

        Args:
            user_input: What the user said
            chat_history: Optional list of previous messages for context
                         Format: [HumanMessage("hi"), AIMessage("hello!"), ...]

        Returns:
            The coach's response as a string
        """
        return self.chain.invoke({
            "user_input": user_input,
            "chat_history": chat_history or []
        })

    def stream_chat(self, user_input: str, chat_history: list = None):
        """
        Stream the response word-by-word (like ChatGPT's typing effect).

        Useful for Streamlit UI to show responses as they're generated.

        Yields:
            Chunks of text as they're generated
        """
        for chunk in self.chain.stream({
            "user_input": user_input,
            "chat_history": chat_history or []
        }):
            yield chunk


# ============================================================================
# Factory Function (Convenience)
# ============================================================================

def get_chat_chain(temperature: float = 0.7) -> ChatChain:
    """
    Factory function to create a chat chain.

    Usage:
        chain = get_chat_chain()
        response = chain.chat("How do I get better at pull-ups?")
    """
    return ChatChain(temperature=temperature)


# ============================================================================
# Quick Test (if run directly)
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of the chat chain.
    Run: python -m src.chains.chat_chain
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("🏋️ Gym Bro Chat Chain Test\n")

    chain = get_chat_chain()

    test_messages = [
        "Hey! How are you?",
        "I'm feeling tired today, should I skip my workout?",
        "What's progressive overload?",
        "Thanks for the advice!"
    ]

    for msg in test_messages:
        print(f"👤 User: {msg}")
        response = chain.chat(msg)
        print(f"🤖 Coach: {response}\n")
