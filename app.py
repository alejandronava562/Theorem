# backend: app.py
# Assumes these existing files remain as-is in the same folder:
#   unit_generator.py, tutor_helper.py, env_loader.py
# This Flask layer only adapts the CLI flow into HTTP.
# No extra features beyond: choose topic, optional AI tutor, generate unit, take quiz, track coins.
# Flask API backend for learning app (topic → units → quiz → progress tracking)
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
from firestore_db import (
    init_firestore, get_firestore_client, upsert_user,
    save_learning_path, get_learning_path,
    save_progress, get_progress,
    save_session_state, get_session_state,
    get_all_topics_for_user, delete_user_data
)
from firebase_admin import credentials, auth

# Load .env if present (local/dev)
load_dotenv()
# Resolve Firebase credentials from env, file path, or local config
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
            return "path", os.path.abspath(expanded)
        # Try relative to project directory
        project_rel = os.path.join(os.path.dirname(__file__), expanded)
        if os.path.exists(project_rel):
            return "path", os.path.abspath(project_rel)

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

# Simple check to confirm Firestore connection is working
def _validate_firestore_connection() -> None:
    try:
        client = get_firestore_client()
        next(client.collections(), None)
        print("Firestore connection: OK")
    except Exception as exc:
        print(f"Warning: Firestore connectivity check failed: {exc}")


_validate_firestore_connection()
# Initialize Flask app and session secret
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "dev-secret-change-me"  # needed for session cookies

# In-memory per-session state
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Get or create unique session ID stored in cookie
def _get_session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = str(uuid.uuid4())
        session["sid"] = sid
    return sid

# Retrieve or initialize session state for current user
def _get_state() -> Dict[str, Any]:
    sid = _get_session_id()
    if sid not in SESSIONS:
        SESSIONS[sid] = {}
    return SESSIONS[sid]

# Helpers to extract lessons and quiz questions from unit content
def _extract_quiz_questions(lessoncontent: list) -> list:
    quizzes = [item for item in lessoncontent if item.get("TYPE") == "QUIZ"]
    if not quizzes:
        return []
    quiz = quizzes[0]
    return quiz.get("QUESTIONS", [])


def _extract_lessons(lessoncontent: list) -> list:
    return [item for item in lessoncontent if item.get("TYPE") == "LESSON"]

# Build AI tutor feedback for incorrect answers
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

# Start topic: load/generate learning path and initialize progress
@app.post("/api/start")
def start():
    data = request.get_json(force=True) or {}
    topic = (data.get("topic") or "").strip()
    username = (data.get("username") or "").strip() or None
    use_tutor = bool(data.get("use_tutor", True))

    # Use authenticated user info if available
    if not username:
        username = session.get("name") or None

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    uid = session.get("uid")

    # Try to load existing learning path
    learning_path = None
    unit_order = []
    unit_meta = {}

    if uid:
        try:
            saved_path = get_learning_path(uid, topic)
            if saved_path:
                learning_path = saved_path.get("learning_path")
                unit_order = saved_path.get("unit_order", [])
                unit_meta = saved_path.get("unit_meta", {})
        except Exception as exc:
            print(f"Warning: Failed to load saved learning path: {exc}")

    # Generate new path if not saved
    if not learning_path:
        pathway = generate_pathway(topic=topic)
        learning_path = extract_learning_path(pathway)
        unit_order, unit_meta_obj = flatten_units(learning_path)
        unit_meta = {unit_id: meta.to_dict() for unit_id, meta in unit_meta_obj.items()}

        # Save the generated path
        if uid:
            try:
                save_learning_path(uid, topic, learning_path, unit_meta, unit_order)
            except Exception as exc:
                print(f"Warning: Failed to save learning path: {exc}")

    # Build fresh progress, then overlay any saved progress from Firestore
    progress = init_progress(unit_order)
    saved_coins = 0
    saved_active_unit = None

    if uid:
        try:
            saved = get_progress(uid, topic)
            if saved:
                saved_units = saved.get("units", {})
                for uid_key, status_data in saved_units.items():
                    if uid_key in progress:
                        progress[uid_key] = status_data
                saved_coins = saved.get("coins", 0)
                saved_active_unit = saved.get("active_unit_id")
        except Exception as exc:
            print(f"Warning: Failed to load saved progress: {exc}")

    state = _get_state()
    state.clear()
    state.update(default_state())
    state["user"] = username
    state["uid"] = uid
    state["topic"] = topic
    state["use_tutor"] = use_tutor
    state["learning_path"] = learning_path
    state["unit_order"] = unit_order
    state["unit_meta"] = unit_meta
    state["progress"] = progress
    state["coins"] = saved_coins
    state["active_unit_id"] = saved_active_unit
    state["lessons"] = []
    state["questions"] = []
    state["q_index"] = 0

    return jsonify({
        "topic": topic,
        "use_tutor": use_tutor,
        "pathway": {"learning_path": learning_path},
        "progress": progress,
        "coins": saved_coins,
        "unit_order": unit_order,
        "unit_meta": unit_meta,
    })
    
# Return current session state (progress, question, coins, etc.)
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
# Firebase authentication: login
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

# Firebase authentication: logout
@app.post("/api/logout")
def auth_logout():
    session.clear()
    return jsonify({"status": "logged out"}), 200

# Firebase authentication: session check
@app.get("/api/check-auth")
def check_auth():
    uid = session.get("uid")
    email = session.get("email")
    name = session.get("name")
    if uid:
        return jsonify({"authenticated": True, "uid": uid, "email": email, "name": name})
    else:
        return jsonify({"authenticated": False}), 200

# Get list of topics user has started
@app.get("/api/topics")
def get_topics():
    """Get list of topics the user has started."""
    uid = session.get("uid")
    if not uid:
        return jsonify({"topics": []}), 200

    try:
        topics = get_all_topics_for_user(uid)
        return jsonify({"topics": topics}), 200
    except Exception as exc:
        print(f"Warning: Failed to get topics: {exc}")
        return jsonify({"topics": []}), 200

# Save progress (units, coins, active unit) to Firestore
@app.post("/api/save-progress")
def save_progress_endpoint():
    """Save current session progress to Firestore."""
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(force=True) or {}
    topic = data.get("topic")
    progress = data.get("progress", {})
    coins = data.get("coins", 0)
    active_unit_id = data.get("active_unit_id")

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    try:
        save_progress(uid, topic, progress, coins, active_unit_id)
        return jsonify({"status": "saved"}), 200
    except Exception as exc:
        print(f"Warning: Failed to save progress: {exc}")
        return jsonify({"error": str(exc)}), 500

# Load saved progress for a topic
@app.get("/api/load-progress/<topic>")
def load_progress(topic):
    """Load saved progress for a topic."""
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        progress = get_progress(uid, topic)
        if progress:
            return jsonify(progress), 200
        else:
            return jsonify({"error": "No saved progress"}), 404
    except Exception as exc:
        print(f"Warning: Failed to load progress: {exc}")
        return jsonify({"error": str(exc)}), 500

# Save full session state for resume functionality
@app.post("/api/save-session")
def save_session_endpoint():
    """Save complete session state (for resume functionality)."""
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(force=True) or {}
    topic = data.get("topic")
    session_data = data.get("session", {})

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    try:
        save_session_state(uid, topic, session_data)
        return jsonify({"status": "saved"}), 200
    except Exception as exc:
        print(f"Warning: Failed to save session: {exc}")
        return jsonify({"error": str(exc)}), 500

# Load saved session state for a topic
@app.get("/api/load-session/<topic>")
def load_session(topic):
    """Load saved session state for a topic."""
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        session_state = get_session_state(uid, topic)
        if session_state:
            return jsonify(session_state), 200
        else:
            return jsonify({"error": "No saved session"}), 404
    except Exception as exc:
        print(f"Warning: Failed to load session: {exc}")
        return jsonify({"error": str(exc)}), 500

# Delete all user data from Firestore
@app.delete("/api/delete-data")
def delete_data():
    """Delete all saved user data (learning paths, progress, sessions)."""
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        deleted = delete_user_data(uid)
        return jsonify({"status": "deleted", "deleted": deleted}), 200
    except Exception as exc:
        print(f"Warning: Failed to delete user data: {exc}")
        return jsonify({"error": str(exc)}), 500

# Return current learning path
@app.get("/api/pathway")
def get_pathway():
    state = _get_state()
    if not state.get("learning_path"):
        return jsonify({"error": "No learning path generated yet"}), 404
    return jsonify({"learning_path": state["learning_path"]})
# Return progress, coins, and active unit
@app.get("/api/progress")
def get_progress_endpoint():
    state = _get_state()
    if not state.get("learning_path"):
        return jsonify({"error": "No learning path generated yet"}), 404
    return jsonify({
        "progress": state.get("progress", {}),
        "coins": state.get("coins", 0),
        "active_unit_id": state.get("active_unit_id"),
    })

# Generate and start a unit (lessons + quiz)
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
        "all_questions": questions,
        "coins": state.get("coins", 0),
        "progress": state.get("progress", {}),
    })

# Restore quiz state mid-progress
@app.post("/api/unit/resume")
def resume_unit():
    """Resume a quiz mid-way by restoring backend state from the frontend."""
    data = request.get_json(force=True) or {}
    unit_id = (data.get("unit_id") or "").strip()
    questions = data.get("questions", [])
    q_index = data.get("q_index", 0)
    lessons = data.get("lessons", [])
    coins = data.get("coins", 0)

    if not unit_id:
        return jsonify({"error": "unit_id is required"}), 400
    if not questions:
        return jsonify({"error": "questions are required"}), 400

    state = _get_state()
    if not state.get("learning_path"):
        return jsonify({"error": "Start a topic first"}), 400

    state["active_unit_id"] = unit_id
    state["questions"] = questions
    state["q_index"] = q_index
    state["lessons"] = lessons
    state["coins"] = coins

    progress = state.get("progress", {}) or {}
    progress.setdefault(unit_id, {})
    if progress[unit_id].get("status") != "completed":
        progress[unit_id]["status"] = "unlocked"
    state["progress"] = progress

    return jsonify({"status": "resumed", "q_index": q_index}), 200

# Process answer, update coins, advance quiz, unlock units
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
        state["coins"] = max(state.get("coins", 0) - 5, 0)

    feedback = None
    #if (not correct) and state.get("use_tutor"):
    if not correct:
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
