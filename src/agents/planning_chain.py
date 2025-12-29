"""
Template Planning Chain - AI-guided workout template modification.

Handles pre-workout chat for template modifications via natural language.
Users can modify templates by saying things like:
- "No cables today"
- "Replace bench press with dumbbells"
- "Add more shoulder work"
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import os


class TemplateModification(BaseModel):
    """Structured output for template modifications."""
    modified_template: dict = Field(description="The modified workout template")
    explanation: str = Field(description="Brief explanation of changes made")
    equipment_unavailable: list[str] | None = Field(description="Equipment mentioned as unavailable")
    equipment_required: list[str] | None = Field(description="Equipment required for this template")


PLANNING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a workout planning assistant helping users customize their workout templates.

Your job is to modify workout templates based on user requests. Common modifications:
- **Replace exercise**: Swap one exercise for another (e.g., "Replace bench press with dumbbells")
- **Equipment substitution**: Find alternatives when equipment is unavailable (e.g., "No cable machine")
- **Volume adjustment**: Add/remove sets or exercises (e.g., "Add more shoulder work")
- **Focus shift**: Emphasize certain muscle groups

Current Template:
{current_template}

Equipment Constraints:
Available: {equipment_available}
Unavailable: {equipment_unavailable}

User Request: {user_message}

INSTRUCTIONS:
1. Analyze the user's request
2. Modify the template accordingly
3. If equipment is mentioned as unavailable, find suitable alternatives that work the same muscle groups
4. Maintain the workout type (Push/Pull/Legs) unless user explicitly asks to change it
5. Keep target sets/reps similar unless user asks to change volume
6. **IMPORTANT: For suggested_weight_lbs:**
   - ALWAYS include this field for weighted exercises
   - If the user has exercise history, use progressive overload (last weight + 2.5-5 lbs)
   - If no history (new user), suggest beginner-friendly starting weights:
     * Compound upper (bench, rows, press): 20-30 lbs dumbbells / 45-95 lbs barbell
     * Compound lower (squat, deadlift): 65-135 lbs (bar + light plates)
     * Isolation upper (curls, raises, extensions): 10-20 lbs dumbbells / 20-40 lbs cable
     * Isolation lower (leg curl, extension): 40-70 lbs machine
     * Bodyweight (pull-ups, dips, push-ups): null (suggest assisted variations if needed)
   - Always err on the conservative side for safety
   - Include reasoning mentioning "beginner weight" if applicable
7. Provide a brief 1-2 sentence explanation of what changed

## CATCH-UP MODE & EXPRESS WORKOUTS

When the user is in catch-up mode (multiple workouts needed, limited days):
1. **Suggest Express versions** - Shorter, efficient workouts
2. **Express guidelines:**
   - Keep heavy compound lifts (squat, bench, deadlift variations, rows, overhead press)
   - Remove or reduce isolation exercises (lateral raises, curls, extensions unless critical)
   - Reduce sets: 4→3, 3→2 (maintain intensity, reduce volume)
   - Keep 1-2 accessories per muscle group (prioritize weak points)
   - Target 30-35 min instead of 50-60 min
   - Example: "Express Upper" = Incline Bench, Overhead Press, Cable Row, Lateral Raise, Curl (5 exercises vs 9)

3. **Multi-workout recommendations:**
   - If user needs 2+ workouts same day, suggest Express for both
   - Example: "Express Upper (35 min) + Express Lower (35 min) = 70 min total"
   - Show time estimates to help planning
   - Prioritize getting both workouts done over perfecting one

4. **Prioritization:**
   - Compounds over isolation (strength > pump)
   - Main movers over finishers (bench > cable fly)
   - Core lifts over variations (squat > leg extension)
   - Multi-joint over single-joint

Return your response in this JSON format:
{{
    "modified_template": {{
        "id": "adaptive_push",
        "name": "Adaptive Push Workout",
        "type": "Push",
        "exercises": [
            {{
                "name": "Exercise Name",
                "target_sets": 3,
                "target_reps": 10,
                "suggested_weight_lbs": 45.0,
                "rest_seconds": 90,
                "reasoning": "Why this exercise/weight"
            }}
        ],
        "coaching_notes": ["Note 1", "Note 2"],
        "mode": "adaptive"
    }},
    "explanation": "Brief explanation of changes",
    "equipment_unavailable": ["cable", "smith machine"],
    "equipment_required": ["dumbbells", "barbell", "bench"]
}}"""),
    ("user", "{user_message}")
])


class TemplatePlanningChain:
    """Chain for modifying workout templates via natural language."""

    def __init__(self):
        """Initialize the planning chain."""
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0.3,  # Low temperature for consistent modifications
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        self.parser = JsonOutputParser(pydantic_object=TemplateModification)

        self.chain = PLANNING_PROMPT | self.llm | self.parser

    def modify_template(
        self,
        user_message: str,
        current_template: dict,
        equipment_available: list[str] | None = None,
        equipment_unavailable: list[str] | None = None
    ) -> dict:
        """
        Modify a workout template based on user's natural language request.

        Args:
            user_message: User's modification request
            current_template: Current workout template dict
            equipment_available: List of available equipment
            equipment_unavailable: List of unavailable equipment

        Returns:
            Dict with:
                - modified_template: Updated template
                - explanation: What changed
                - equipment_unavailable: Updated list
                - equipment_required: What template needs
        """
        try:
            result = self.chain.invoke({
                "user_message": user_message,
                "current_template": current_template,
                "equipment_available": equipment_available or [],
                "equipment_unavailable": equipment_unavailable or []
            })

            return result

        except Exception as e:
            # Fallback: Return original template with error explanation
            return {
                "modified_template": current_template,
                "explanation": f"Could not modify template: {str(e)}. Using original template.",
                "equipment_unavailable": equipment_unavailable,
                "equipment_required": None
            }


# Singleton instance
_planning_chain = None

def get_planning_chain() -> TemplatePlanningChain:
    """Get or create the planning chain singleton."""
    global _planning_chain
    if _planning_chain is None:
        _planning_chain = TemplatePlanningChain()
    return _planning_chain
