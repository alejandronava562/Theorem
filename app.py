# backend: app.py
# Assumes these existing files remain as-is in the same folder:
#   unit_generator.py, tutor_helper.py, env_loader.py
# This Flask layer only adapts the CLI flow into HTTP.
# No extra features beyond: choose topic, optional AI tutor, generate unit, take quiz, track coins.

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from typing import Dict, Any, Optional
import uuid

from unit_generator import generate_unit
from tutor_helper import ai_tutor_reply
from path_generator import generate_pathway
from session_state import default_state, hydrate

# Serve static files under /static (Flask default). Explicit to avoid 404s in templates.
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "dev-secret-change-me"  # needed for session cookies

# In-memory per-session state
SESSIONS: Dict[str, Dict[str, Any]] = {}


def _get_session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = str(uuid.uuid4())
        session["sid"] = sid
    return sid


def _get_state() -> Dict[str, Any]:
    sid = _get_session_id()
    if sid not in SESSIONS:
        SESSIONS[sid] = {}
    return SESSIONS[sid]


def _extract_quiz_questions(lessoncontent: list) -> list:
    quizzes = [item for item in lessoncontent if item.get("TYPE") == "QUIZ"]
    if not quizzes:
        return []
    quiz = quizzes[0]
    return quiz.get("QUESTIONS", [])


def _extract_lessons(lessoncontent: list) -> list:
    return [item for item in lessoncontent if item.get("TYPE") == "LESSON"]


def _build_tutor_feedback(question_data: Dict[str, Any], user_answer: str) -> Optional[Dict[str, Any]]:
    options = question_data.get("OPTIONS", {}) or {}
    option_lines = "\n".join(f"{key} {text}" for key, text in options.items())

    question_text = question_data.get("QUESTION", "Unknown")
    prompt = (
        f"Question: {question_text}\n"
        f"Options:\n{option_lines}\n"
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
        # Match the spirit of the original CLI behavior: surface the error message
        return {"message": f"[Tutor error: {exc}]"}


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/start")
def start():
    data = request.get_json(force=True) or {}
    topic = (data.get("topic") or "").strip()
    username = (data.get("username") or "").strip() or None
    use_tutor = bool(data.get("use_tutor", False))
    if not topic:
        return jsonify({"error": "Topic is required"}), 400
    pathway = generate_pathway(topic=topic)
    state = _get_state()
    state.clear()
    state.update(default_state())
    state["user"] = username
    state["topic"] = topic
    state["user_tutor"] = use_tutor
    state["learning_path"] = pathway.get("learning_path", pathway)

    return jsonify({
        "topic": topic,
        "use_tutor": use_tutor,
        "pathway": pathway
    })
    

@app.get("/api/state")
def get_state():
    state = _get_state()
    if not state or "questions" not in state:
        return jsonify({"started": False})

    questions = state.get("questions", [])
    q_index = state.get("q_index", 0)
    q = questions[q_index] if 0 <= q_index < len(questions) else None

    return jsonify({
        "started": True,
        "topic": state.get("topic"),
        "use_tutor": state.get("use_tutor", False),
        "lessons": state.get("lessons", []),
        "question": q,
        "coins": state.get("coins", 0),
        "done": q is None,
    })

@app.get("/api/pathway")
def get_pathway():
    state = _get_state()
    if not state.get("learning_path"):
        return jsonify({"error": "No learning path generated yet"}), 404
    return jsonify({"learning_path": state["learning_path"]})

@app.post("/api/answer")
def answer():
    data = request.get_json(force=True) or {}
    user_answer = (data.get("answer") or "").strip().upper()

    state = _get_state()
    if not state or "questions" not in state:
        return jsonify({"error": "Quiz not started"}), 400

    questions = state.get("questions", [])
    q_index = state.get("q_index", 0)

    if q_index >= len(questions):
        return jsonify({
            "error": "Quiz already finished",
            "coins": state.get("coins", 0),
            "done": True
        }), 400

    if user_answer not in ["A", "B", "C", "D"]:
        return jsonify({"error": "Answer must be A, B, C, or D"}), 400

    q = questions[q_index]
    correct = (user_answer == q.get("CORRECT_ANSWER"))

    # Same scoring as CLI
    if correct:
        state["coins"] = state.get("coins", 0) + 10
    else:
        state["coins"] = state.get("coins", 0) - 5

    feedback = None
    if (not correct) and state.get("use_tutor"):
        feedback = _build_tutor_feedback(q, user_answer)

    # Advance
    state["q_index"] = q_index + 1
    next_q_index = state["q_index"]
    next_q = questions[next_q_index] if next_q_index < len(questions) else None

    return jsonify({
        "correct": correct,
        "coins": state["coins"],
        "feedback": feedback,
        "next_question": next_q,
        "done": next_q is None,
    })


if __name__ == "__main__":
    app.run(debug=True)
