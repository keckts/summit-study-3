example_json_flashcard = {
        "title": "Biology Basics",
        "description": "A set of flashcards covering fundamental biology concepts.",
        "difficulty": "Medium",
        "flashcards": [
            {
                "front": "What is the powerhouse of the cell?",
                "back": "Mitochondria"
            },
            {
                "front": "DNA is composed of what molecules?",
                "back": "Nucleotides"
            },
            {
                "front": "What organelles are responsible for photosynthesis?",
                "back": "Chloroplasts"
            },
            {
                "front": "Which blood cells carry oxygen?",
                "back": "Red blood cells"
            },
            {
                "front": "What process do plants use to make food?",
                "back": "Photosynthesis"
            }
        ]
    }

example_json_practice_test = {
    "title": "Biology Basics Test 2",
    "description": "A short test on fundamental biology concepts.",
    "subject": "Biology",
    "duration": 25,
    "difficulty": "Medium",
    "is_public": True,
    "questions": [
        {
            "text": "What is the powerhouse of the cell?",
            "question_type": "mcq",
            "subject": "Biology",
            "answer": "Mitochondria",
            "explanation": "Mitochondria produce ATP through cellular respiration.",
            "options": [
                {"text": "Nucleus", "is_correct": False},
                {"text": "Mitochondria", "is_correct": True},
                {"text": "Ribosome", "is_correct": False},
                {"text": "Chloroplast", "is_correct": False}
            ]
        }
        # Add more questions if needed
    ]
}

practice_test_schema = """
    PracticeTest:
    - title (string)
    - description (string)
    - subject (string)
    - duration (integer, minutes)
    - difficulty (string: Easy, Medium, Hard)
    - questions (array of Question objects)

    Question:
    - text (string)
    - question_type (string: "mcq", "text", or "tf")
    - subject (string)
    - answer (string)
    - explanation (string)
    - options (array of Option objects, only if question_type is "mcq")

    Option:
    - text (string)
    - is_correct (boolean)
"""

flashcard_schema = """
    FlashcardSet:
    - title (string)
    - description (string)
    - subject (string)
    - difficulty (string: Easy, Medium, Hard)

    Flashcard:
    - front (string)
    - back (string)
"""

import json

def ai_prompt(full_prompt, amount, difficulty, activity_type, extra_file_data=None):
    """
    Generate a strict AI prompt that ensures JSON output
    matching the exact schema for flashcards or practice tests.
    """
    activity_word = "flashcards" if activity_type == "flashcards" else "questions"

    # Include extra_file_data only if present
    extra_data_text = f"Include this additional context from the file:\n{extra_file_data}" if extra_file_data else ""

    # Strict instructions
    instructions = f"""
You are a JSON-generating AI. Your task is to create exactly {amount} {activity_word} 
based on the following description:

{full_prompt}

Difficulty: {difficulty}.
{extra_data_text}

⚠️ IMPORTANT RULES:
1. Only return raw JSON — no Markdown, no text, no code fences.
2. JSON MUST strictly match the following schema:

{flashcard_schema if activity_word == "flashcards" else practice_test_schema}

3. Use the example JSON format exactly as a reference for structure, nesting, and key names:

{json.dumps(example_json_flashcard, indent=4) if activity_word == "flashcards" else json.dumps(example_json_practice_test, indent=4)}

4. Do not include IDs, timestamps, or any extra fields — only the keys in the schema.
5. Make sure all required fields are present and correctly typed (string, integer, boolean, array).

Return the JSON as a single valid object.
"""

    return instructions

