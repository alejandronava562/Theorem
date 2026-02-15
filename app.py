# backend: app.py
# Assumes these existing files remain as-is in the same folder:
#   unit_generator.py, tutor_helper.py, env_loader.py
# This Flask layer only adapts the CLI flow into HTTP.
# No extra features beyond: choose topic, optional AI tutor, generate unit, take quiz, track coins.

from flask import Flask, render_template, request, jsonify, session
from typing import Dict, Any, Optional
import os
import json
import uuid

from dotenv import load_dotenv

from unit_generator import generate_unit
from tutor_helper import ai_tutor_reply
from path_generator import generate_pathway
from learning_path import extract_learning_path, flatten_units, init_progress, next_unit_id
from session_state import default_state

#Firebase Imports
import firebase_admin
from firestore_db import *
from firebase_admin import credentials, auth

# Load .env if present (local/dev)
load_dotenv()

def _resolve_firebase_credentials():
    firebase_creds_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if firebase_creds_json:
        try:
            return "info", json.loads(firebase_creds_json)
        except json.JSONDecodeError as exc:
            print(f"Warning: FIREBASE_SERVICE_ACCOUNT_JSON is invalid JSON: {exc}")

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path:
        expanded = os.path.expanduser(cred_path)
        if os.path.exists(expanded):
            return "path", expanded

    local_path = os.path.join(os.path.dirname(__file__), "service-account.json")
    if os.path.exists(local_path):
        return "path", local_path

    return None, None


cred_type, cred_value = _resolve_firebase_credentials()

if not firebase_admin._apps:
    try:
        if cred_type in ("info", "path"):
            firebase_admin.initialize_app(credentials.Certificate(cred_value))
        else:
            firebase_admin.initialize_app()
    except Exception as exc:
        print(f"Warning: Firebase Admin not initialized: {exc}")

try:
    if cred_type == "info":
        init_firestore(credentials_info=cred_value)
    elif cred_type == "path":
        init_firestore(credentials_path=cred_value)
    else:
        init_firestore()
except Exception as exc:
    print(f"Warning: Firestore not initialized: {exc}")


def _validate_firestore_connection() -> None:
    try:
        client = get_firestore_client()
        next(client.collections(), None)
        print("Firestore connection: OK")
    except Exception as exc:
        print(f"Warning: Firestore connectivity check failed: {exc}")


_validate_firestore_connection()

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

    # Use authenticated user info if available
    if not username:
        username = session.get("name") or None

    if not topic:
        return jsonify({"error": "Topic is required"}), 400
    pathway = generate_pathway(topic=topic)
    learning_path = extract_learning_path(pathway)
    unit_order, unit_meta_obj = flatten_units(learning_path)
    unit_meta = {unit_id: meta.to_dict() for unit_id, meta in unit_meta_obj.items()}

    state = _get_state()
    state.clear()
    state.update(default_state())
    state["user"] = username
    state["uid"] = session.get("uid")
    state["topic"] = topic
    state["use_tutor"] = use_tutor
    state["learning_path"] = learning_path
    state["unit_order"] = unit_order
    state["unit_meta"] = unit_meta
    state["progress"] = init_progress(unit_order)
    state["active_unit_id"] = None
    state["lessons"] = []
    state["questions"] = []
    state["q_index"] = 0

    return jsonify({
        "topic": topic,
        "use_tutor": use_tutor,
        "pathway": {"learning_path": learning_path},
        "progress": state["progress"],
        "unit_order": unit_order,
        "unit_meta": unit_meta,
    })
    

@app.get("/api/state")
def get_state():
    state = _get_state()
    if not state or not state.get("topic"):
        return jsonify({"started": False})

    questions = state.get("questions", [])
    q_index = state.get("q_index", 0)
    q = questions[q_index] if 0 <= q_index < len(questions) else None

    return jsonify({
        "started": True,
        "topic": state.get("topic"),
        "use_tutor": state.get("use_tutor", False),
        "learning_path": state.get("learning_path"),
        "unit_meta": state.get("unit_meta", {}),
        "unit_order": state.get("unit_order", []),
        "progress": state.get("progress", {}),
        "active_unit_id": state.get("active_unit_id"),
        "lessons": state.get("lessons", []),
        "question": q,
        "coins": state.get("coins", 0),
        "done": q is None,
    })

@app.post("/api/auth")
def auth_login():
    data = request.get_json(force=True) or {}
    id_token = data.get("idToken")
    if not id_token:
        return jsonify({"error": "Missing idToken"}), 400

    try:
        decoded = auth.verify_id_token(id_token)
        uid = decoded.get("uid")
        email = decoded.get("email")
        name = decoded.get("name") or decoded.get("displayName") or ""
        picture = decoded.get("picture")

        # Save or update user in Firestore
        try:
            upsert_user(uid, email, name, picture)
        except Exception:
            pass  # don't block sign-in if Firestore write fails

        session["uid"] = uid
        session["email"] = email
        session["name"] = name
        return jsonify({"uid": uid, "email": email, "name": name})
    except Exception as exc:
        return jsonify({"error": f"Invalid token: {exc}"}), 401


@app.post("/api/logout")
def auth_logout():
    session.clear()
    return jsonify({"status": "logged out"}), 200


@app.get("/api/check-auth")
def check_auth():
    uid = session.get("uid")
    email = session.get("email")
    name = session.get("name")
    if uid:
        return jsonify({"authenticated": True, "uid": uid, "email": email, "name": name})
    else:
        return jsonify({"authenticated": False}), 200


@app.get("/api/pathway")
def get_pathway():
    state = _get_state()
    if not state.get("learning_path"):
        return jsonify({"error": "No learning path generated yet"}), 404
    return jsonify({"learning_path": state["learning_path"]})

@app.get("/api/progress")
def get_progress():
    state = _get_state()
    if not state.get("learning_path"):
        return jsonify({"error": "No learning path generated yet"}), 404
    return jsonify({
        "progress": state.get("progress", {}),
        "coins": state.get("coins", 0),
        "active_unit_id": state.get("active_unit_id"),
    })


@app.post("/api/unit/start")
def start_unit():
    data = request.get_json(force=True) or {}
    unit_id = (data.get("unit_id") or "").strip()
    if not unit_id:
        return jsonify({"error": "unit_id is required"}), 400

    state = _get_state()
    if not state.get("learning_path"):
        return jsonify({"error": "Start a topic first"}), 400

    progress = state.get("progress", {}) or {}
    if progress.get(unit_id, {}).get("status") == "locked":
        return jsonify({"error": "Unit is locked"}), 403

    unit_meta = (state.get("unit_meta") or {}).get(unit_id)
    if not unit_meta:
        return jsonify({"error": "Unknown unit_id"}), 404

    unit_json = generate_unit(
        topic=state.get("topic") or "Topic",
        unit_title=unit_meta.get("title"),
        skills=unit_meta.get("skills") or [],
    )
    lessoncontent = unit_json.get("LESSON1CONTENT", []) or []
    lessons = [item.get("TEXT", "") for item in _extract_lessons(lessoncontent)]
    questions = _extract_quiz_questions(lessoncontent)

    if not questions:
        return jsonify({"error": "Unit generated without quiz questions"}), 500

    state["active_unit_id"] = unit_id
    state["lessons"] = lessons
    state["questions"] = questions
    state["q_index"] = 0

    progress.setdefault(unit_id, {})
    if progress[unit_id].get("status") != "completed":
        progress[unit_id]["status"] = "unlocked"
    state["progress"] = progress

    return jsonify({
        "unit_id": unit_id,
        "unit_meta": unit_meta,
        "lessons": lessons,
        "question": questions[0],
        "coins": state.get("coins", 0),
        "progress": state.get("progress", {}),
    })


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

    just_completed = False
    if next_q is None:
        active_unit_id = state.get("active_unit_id")
        if active_unit_id:
            state.setdefault("progress", {})
            state["progress"].setdefault(active_unit_id, {})
            state["progress"][active_unit_id]["status"] = "completed"
            just_completed = True

            nxt = next_unit_id(state.get("unit_order", []), active_unit_id)
            if nxt:
                state["progress"].setdefault(nxt, {})
                if state["progress"][nxt].get("status") != "completed":
                    state["progress"][nxt]["status"] = "unlocked"

    return jsonify({
        "correct": correct,
        "coins": state["coins"],
        "feedback": feedback,
        "next_question": next_q,
        "done": next_q is None,
        "just_completed": just_completed,
        "active_unit_id": state.get("active_unit_id"),
        "progress": state.get("progress", {}),
    })


if __name__ == "__main__":
    app.run(debug=True)
