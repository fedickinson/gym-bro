"""
AI-powered abs template recommendation system.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.tools.abs_tools import get_abs_history, get_available_abs_templates, get_abs_template_by_id
import json


def recommend_abs_template(
    time_available: int = 15,
    equipment_unavailable: list[str] = None
) -> dict:
    """
    Use AI to recommend the best abs template based on history and context.

    Args:
        time_available: Minutes available for abs (default: 15)
        equipment_unavailable: Equipment not available from main workout

    Returns:
        {
            "template_id": str,
            "template": dict,  # Full template with exercises
            "reason": str,  # AI's reasoning for recommendation
            "modifications": list[str]  # Suggested modifications
        }
    """
    # Get abs history using the tool
    history_data = get_abs_history.invoke({"days": 30})

    # Get available templates using the tool
    available_templates = get_available_abs_templates.invoke({})

    if not available_templates:
        # No templates available - return error
        return {
            "template_id": None,
            "template": None,
            "reason": "No abs templates found. Please create abs_templates.json",
            "modifications": []
        }

    # Use AI to make recommendation
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.3)

    system_msg = SystemMessage(content="""You are a personal trainer recommending abs templates.

Your job:
1. Analyze user's abs history (sessions, exercises, recency)
2. Consider time available and equipment constraints
3. Recommend ONE template that:
   - Provides variety (don't repeat recent exercises too much)
   - Matches difficulty to their experience
   - Fits time constraint
   - Avoids unavailable equipment
4. Explain your reasoning in 1-2 sentences
5. Suggest modifications if needed

Output ONLY valid JSON in this exact format:
{
  "template_id": "abs_core_strength",
  "reason": "You haven't done planks in 2 weeks and need more anti-rotation work",
  "modifications": ["Increase plank hold to 60s based on last session"]
}""")

    human_msg = HumanMessage(content=f"""Recommend an abs template:

Abs History (last 30 days):
{json.dumps(history_data, indent=2)}

Available Templates:
{json.dumps(available_templates, indent=2)}

Time Available: {time_available} minutes
Equipment Unavailable: {equipment_unavailable or 'None'}

Recommend the best template (return JSON only).""")

    try:
        response = llm.invoke([system_msg, human_msg])

        # Parse AI response
        recommendation = json.loads(response.content)
        template_id = recommendation['template_id']

        # Validate template exists
        if not any(t['id'] == template_id for t in available_templates):
            # Fallback to first template
            template_id = available_templates[0]['id']
            recommendation['template_id'] = template_id
            recommendation['reason'] = "Default recommendation - let's start with a balanced core workout"

        # Get full template
        full_template = get_abs_template_by_id(template_id)

        if not full_template:
            # Fallback if template not found
            template_id = available_templates[0]['id']
            full_template = get_abs_template_by_id(template_id)
            recommendation['reason'] = "Starting with a balanced core workout"

        recommendation['template'] = full_template

        return recommendation

    except Exception as e:
        # Fallback: Return first available template
        fallback_id = available_templates[0]['id']
        fallback_template = get_abs_template_by_id(fallback_id)

        return {
            "template_id": fallback_id,
            "template": fallback_template,
            "reason": "Let's start with a balanced core workout",
            "modifications": []
        }


def _extract_exercise_counts(abs_history: list[dict]) -> list[dict]:
    """
    Extract exercise frequency from history.

    Args:
        abs_history: List of abs sessions with exercises

    Returns:
        List of dicts with exercise name and count
    """
    counts = {}
    for session in abs_history:
        for ex in session.get('exercises', []):
            name = ex.get('name')
            if name:
                counts[name] = counts.get(name, 0) + 1

    return [{"name": name, "count": count} for name, count in counts.items()]
