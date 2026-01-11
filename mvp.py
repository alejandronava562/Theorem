from typing import Callable, Dict, Optional
from unit_generator import generate_unit, generate_quiz
from tutor_helper import ai_tutor_reply
from quiz import run_quiz, TutorCallback

def build_tutor_callback() -> TutorCallback:
    """Return a function that describes the mistake and calls ai_tutor_reply."""
    def callback(question_data: Dict[str, str], user_answer: str) -> Optional[str]:
        options = question_data.get("OPTIONS", {})
        option_lines = "\n".join(f'{key}{text}' for key,text in options.items())
        prompt = (
            f"Question: {question_data.get('QUESTION', 'Unknown')}\n"
            f"Options:\n{option_lines}"
        )
        correct_letter = question_data.get("CORRECT_ANSWER")
        correct_text = options.get(correct_letter, "Unknown")
        user_text = options.get(user_answer, "Not provided")

        context = (
            "Please explain the user's mistake in JSON.\n"
            f"User answered: {user_answer} ({user_text}). "
            f"Correct answer: {correct_letter} ({correct_text}). "
            "Give a short recap of the concept."
        )

        try:
            return ai_tutor_reply(question=prompt, context=context)
        except Exception as exc:
            return f"[Tutor error: {exc}]"

    return callback

def main():
    topic = input("What topic should this unit cover?\n")
    use_tutor = input("Enable AI tutor explanations? (Y/N): ").strip().lower().startswith('y')
    unit = generate_unit(topic, model="gpt-4o")
    lessons = unit["LESSON1CONTENT"]
    tutor_cb = build_tutor_callback() if use_tutor else None
    coins = run_quiz(lessons, tutor_callback=tutor_cb)
    print(f"\nTotal coins earned: {coins}")

if __name__ == "__main__":
    main()
