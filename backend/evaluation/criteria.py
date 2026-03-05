"""Evaluation criteria for LLM-as-Judge."""

CRITERIA = {
    "relevance": {
        "name": "Relevance",
        "description": "How relevant is the response to the user's question and current conversation context?",
        "rubric": {
            1: "Completely irrelevant, addresses a different topic",
            2: "Partially relevant but misses the main point",
            3: "Somewhat relevant but includes unnecessary information",
            4: "Mostly relevant with minor tangential content",
            5: "Perfectly relevant, directly addresses the user's concern",
        },
    },
    "accuracy": {
        "name": "Technical Accuracy",
        "description": "Are the troubleshooting steps and technical information correct for Reolink products?",
        "rubric": {
            1: "Contains serious technical errors that could damage equipment",
            2: "Multiple inaccuracies in troubleshooting steps",
            3: "Generally correct but some steps are imprecise or outdated",
            4: "Accurate with minor imprecisions",
            5: "Technically flawless, correct product-specific information",
        },
    },
    "helpfulness": {
        "name": "Helpfulness",
        "description": "Does the response effectively move toward resolving the customer's issue?",
        "rubric": {
            1: "Not helpful at all, provides no actionable guidance",
            2: "Minimally helpful, vague suggestions",
            3: "Somewhat helpful but could provide clearer instructions",
            4: "Helpful with clear, actionable steps",
            5: "Extremely helpful, provides clear steps and proactively anticipates follow-up needs",
        },
    },
    "tone": {
        "name": "Tone & Professionalism",
        "description": "Is the tone professional, empathetic, and appropriate for customer service?",
        "rubric": {
            1: "Rude, dismissive, or unprofessional",
            2: "Cold or robotic, lacks empathy",
            3: "Neutral, neither warm nor cold",
            4: "Professional and friendly",
            5: "Excellent: warm, empathetic, patient, and professional",
        },
    },
}


def format_criteria_for_prompt() -> str:
    """Format criteria into a string for the judge prompt."""
    lines = []
    for key, criterion in CRITERIA.items():
        lines.append(f"\n### {criterion['name']} ({key})")
        lines.append(criterion["description"])
        lines.append("Rating scale:")
        for score, desc in criterion["rubric"].items():
            lines.append(f"  {score}: {desc}")
    return "\n".join(lines)
