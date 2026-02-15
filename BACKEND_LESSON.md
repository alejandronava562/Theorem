# Theorem Backend: A Complete Lesson

> This document is a full walkthrough of how the Theorem backend works — from the moment a user opens the app to the moment they finish a quiz. Every file, every endpoint, every decision is explained here.

---

## Table of Contents

1. [The Big Picture](#1-the-big-picture)
2. [How the Files Fit Together](#2-how-the-files-fit-together)
3. [App Startup: What Happens Before Any User Arrives](#3-app-startup-what-happens-before-any-user-arrives)
4. [Authentication: Google Sign-In Flow](#4-authentication-google-sign-in-flow)
5. [Starting a Topic: The Learning Path Pipeline](#5-starting-a-topic-the-learning-path-pipeline)
6. [The Learning Path Data Structure](#6-the-learning-path-data-structure)
7. [Starting a Unit: AI Content Generation](#7-starting-a-unit-ai-content-generation)
8. [The Quiz Loop: Answering Questions](#8-the-quiz-loop-answering-questions)
9. [The AI Tutor: Feedback on Wrong Answers](#9-the-ai-tutor-feedback-on-wrong-answers)
10. [Progress Tracking and Persistence](#10-progress-tracking-and-persistence)
11. [Session Management: Two Layers](#11-session-management-two-layers)
12. [The Coin System](#12-the-coin-system)
13. [Data Flow Diagrams](#13-data-flow-diagrams)
14. [File Reference](#14-file-reference)
15. [Key Concepts Glossary](#15-key-concepts-glossary)

---

## 1. The Big Picture

Theorem is an AI-powered learning app. A user picks a math topic (like "Algebra"), and the app uses OpenAI to:

1. **Generate a learning path** — a structured curriculum with levels, units, and skills
2. **Generate lesson content** — short text lessons for each unit
3. **Generate quiz questions** — multiple-choice questions to test understanding
4. **Provide AI tutor feedback** — explanations when answers are wrong

The backend is a **Flask web server** (Python) that:
- Serves the frontend HTML/CSS/JS
- Talks to **OpenAI** to generate content
- Talks to **Firebase** for user authentication
- Talks to **Firestore** (a database) to save progress
- Keeps temporary session state **in memory** while users are active

```
┌──────────┐     HTTP      ┌──────────────┐     API     ┌──────────┐
│ Browser  │ ◄──────────► │  Flask App   │ ◄─────────► │  OpenAI  │
│ (JS/HTML)│               │  (app.py)    │             │  (GPT)   │
└──────────┘               └──────┬───────┘             └──────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼                           ▼
             ┌─────────────┐            ┌─────────────┐
             │  Firebase   │            │  Firestore  │
             │  Auth       │            │  Database   │
             └─────────────┘            └─────────────┘
```

---

## 2. How the Files Fit Together

Here is every backend Python file and its one-line purpose:

| File | Role |
|------|------|
| `app.py` | The main server. All HTTP endpoints live here. |
| `firestore_db.py` | Database layer. Reads/writes to Firestore. |
| `session_state.py` | Defines the shape of a user's session data. |
| `path_generator.py` | Asks OpenAI to create a learning path outline. |
| `learning_path.py` | Processes the AI's response into usable data structures. |
| `unit_generator.py` | Asks OpenAI to create lessons and quiz questions. |
| `tutor_helper.py` | Asks OpenAI to explain wrong answers. |
| `env_loader.py` | Loads API keys from `.env` files. |

Think of it as a pipeline:

```
env_loader.py          (loads config)
     │
     ▼
app.py                 (receives HTTP requests)
     │
     ├──► path_generator.py    (AI: "make me a curriculum")
     │         │
     │         ▼
     │    learning_path.py     (parse + flatten the curriculum)
     │
     ├──► unit_generator.py    (AI: "make me a lesson + quiz")
     │
     ├──► tutor_helper.py      (AI: "explain this wrong answer")
     │
     ├──► session_state.py     (in-memory state template)
     │
     └──► firestore_db.py      (persistent storage)
```

---

## 3. App Startup: What Happens Before Any User Arrives

When you run `python app.py`, several things happen before the server starts accepting requests.

### Step 1: Load Environment Variables

```python
from dotenv import load_dotenv
load_dotenv()
```

This reads the `.env` file and makes variables like `OPENAI_API_KEY` and `GOOGLE_APPLICATION_CREDENTIALS` available via `os.getenv()`.

### Step 2: Initialize Firebase Admin SDK

Firebase Admin SDK is used **server-side** to verify Google sign-in tokens. The app supports three ways to provide credentials (in priority order):

1. **`FIREBASE_SERVICE_ACCOUNT_JSON`** — the full JSON as a string (used on Render/production)
2. **`GOOGLE_APPLICATION_CREDENTIALS`** — a file path to the service account JSON
3. **`service-account.json`** — a file in the project directory (fallback)

```python
def _resolve_firebase_credentials():
    # Try JSON string from env var first
    firebase_creds_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if firebase_creds_json:
        return "info", json.loads(firebase_creds_json)

    # Try file path from env var
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.exists(expanded):
        return "path", expanded

    # Try local file
    local_path = os.path.join(os.path.dirname(__file__), "service-account.json")
    if os.path.exists(local_path):
        return "path", local_path

    return None, None
```

**Why three methods?** Different environments need different approaches. On your local machine, a file path is easiest. On a cloud platform like Render, you can't upload files easily, so you paste the JSON into an environment variable instead.

### Step 3: Initialize Firestore

Firestore is Google's NoSQL database. It's initialized with the same credentials:

```python
if cred_type == "info":
    init_firestore(credentials_info=cred_value)
elif cred_type == "path":
    init_firestore(credentials_path=cred_value)
```

A quick connectivity check runs to confirm it's working:

```python
def _validate_firestore_connection():
    client = get_firestore_client()
    next(client.collections(), None)  # Try to list collections
    print("Firestore connection: OK")
```

### Step 4: Create the Flask App

```python
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "dev-secret-change-me"
SESSIONS: Dict[str, Dict[str, Any]] = {}
```

- `static_folder="static"` tells Flask where CSS/JS files live
- `secret_key` is used to sign session cookies (should be a real secret in production)
- `SESSIONS` is a Python dictionary that holds every active user's state **in memory**

---

## 4. Authentication: Google Sign-In Flow

Authentication is a two-part process: the **frontend** handles the Google popup, the **backend** verifies the token.

### The Flow

```
1. User clicks "Sign in with Google"
2. Firebase JS SDK opens a Google popup
3. User signs in → Firebase returns an ID token (a long JWT string)
4. Frontend sends that token to POST /api/auth
5. Backend verifies the token with Firebase Admin SDK
6. Backend stores user info in the Flask session cookie
7. Backend saves/updates user profile in Firestore
```

### The Endpoint: `POST /api/auth`

```python
@app.post("/api/auth")
def auth_login():
    data = request.get_json(force=True) or {}
    id_token = data.get("idToken")

    # Firebase Admin SDK verifies the token is real and not expired
    decoded = auth.verify_id_token(id_token)

    uid = decoded.get("uid")        # Unique Firebase user ID
    email = decoded.get("email")
    name = decoded.get("name")
    picture = decoded.get("picture") # Google profile photo URL

    # Save to Firestore
    upsert_user(uid, email, name, picture)

    # Save to Flask session (cookie)
    session["uid"] = uid
    session["email"] = email
    session["name"] = name

    return jsonify({"uid": uid, "email": email, "name": name})
```

**Key concept: `auth.verify_id_token()`** — This is the security gate. The frontend could send any string, but Firebase Admin SDK cryptographically verifies that the token was really issued by Google for your Firebase project. If someone tries to fake a token, this call throws an error.

### Why `upsert_user`?

"Upsert" means "update or insert." The first time a user signs in, we create their profile in Firestore. Every subsequent time, we just update `last_login`:

```python
def upsert_user(uid, email, display_name, photo_url=None):
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    user_data = {
        'email': email,
        'display_name': display_name,
        'photo_url': photo_url,
        'last_login': firestore.SERVER_TIMESTAMP
    }

    if not user_doc.exists:
        user_data['created_at'] = firestore.SERVER_TIMESTAMP  # Only on first create

    user_ref.set(user_data, merge=True)  # merge=True = upsert behavior
```

### Other Auth Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/logout` | Clears the Flask session cookie |
| `GET /api/check-auth` | Returns whether the session has a valid `uid` |

---

## 5. Starting a Topic: The Learning Path Pipeline

When the user picks a topic like "Algebra" and clicks "Start Learning", the frontend calls `POST /api/start`. This is the most complex endpoint because it orchestrates multiple systems.

### The Full Flow

```
POST /api/start { topic: "Algebra", username: "Alex" }
     │
     ├──► Check Firestore: does a saved learning path exist?
     │         │
     │    YES ─┤──► Use the saved path (skip AI generation)
     │         │
     │    NO ──┤──► Call path_generator.py → OpenAI generates curriculum
     │         │──► Parse with learning_path.py
     │         └──► Save to Firestore for next time
     │
     ├──► Build progress map (which units are locked/unlocked/completed)
     │         │
     │         └──► Check Firestore for saved progress and merge it in
     │
     ├──► Store everything in the in-memory SESSIONS dict
     │
     └──► Return JSON to frontend
```

### Why Check Firestore First?

Generating a learning path costs money (OpenAI API call) and takes time. If the user already started "Algebra" last week, we reuse the same path so they can continue where they left off.

```python
if uid:
    saved_path = get_learning_path(uid, topic)
    if saved_path:
        learning_path = saved_path.get("learning_path")
        unit_order = saved_path.get("unit_order", [])
        unit_meta = saved_path.get("unit_meta", {})

if not learning_path:
    # No saved path — generate a new one
    pathway = generate_pathway(topic=topic)
    learning_path = extract_learning_path(pathway)
    # ... save it to Firestore
```

### The AI Call: `generate_pathway()`

This function in `path_generator.py` sends a carefully crafted prompt to OpenAI:

```python
def generate_pathway(topic, model="gpt-4o-mini"):
    system_prompt = """
    You are a Duolingo-style curriculum designer.
    Output ONLY valid JSON. No markdown, no commentary.
    Constraints:
      - Exactly 5 levels (1-5)
      - Exactly 2 units per level (10 total)
      - 3 skills per unit
      - Skills are short phrases (2-6 words)
    """

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},  # Force JSON output
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a learning path for: {topic}"}
        ]
    )

    return json.loads(response.choices[0].message.content)
```

**Key detail: `response_format={"type": "json_object"}`** — This tells OpenAI to only output valid JSON. Without this, the AI might wrap the JSON in markdown code blocks or add commentary, which would break `json.loads()`.

### Processing the Path: `learning_path.py`

The AI returns nested JSON. `learning_path.py` transforms it into flat, easy-to-use structures:

```python
def flatten_units(learning_path):
    """
    Input (nested):
      levels: [
        { level: 1, units: [{ unit: 1, title: "Numbers" }, { unit: 2, title: "Adding" }] },
        { level: 2, units: [{ unit: 1, title: "Carry" }] }
      ]

    Output (flat):
      unit_order = ["L1U1", "L1U2", "L2U1"]
      unit_meta  = {
        "L1U1": UnitMeta(unit=1, title="Numbers", skills=[...]),
        "L1U2": UnitMeta(unit=2, title="Adding", skills=[...]),
        ...
      }
    """
```

**Unit IDs** follow the pattern `L{level}U{unit}` — so Level 2, Unit 1 becomes `"L2U1"`. This makes it easy to reference units everywhere.

### Building Progress

`init_progress()` creates the initial progress map where only the first unit is unlocked:

```python
def init_progress(unit_order):
    # Result: { "L1U1": {"status": "unlocked"}, "L1U2": {"status": "locked"}, ... }
    progress = {}
    for i, uid in enumerate(unit_order):
        progress[uid] = {"status": "unlocked" if i == 0 else "locked"}
    return progress
```

If the user has saved progress in Firestore, it gets **merged over** the fresh defaults:

```python
saved = get_progress(uid, topic)
if saved:
    saved_units = saved.get("units", {})
    for uid_key, status_data in saved_units.items():
        if uid_key in progress:
            progress[uid_key] = status_data  # Override with saved status
```

This means completed units stay completed and the user picks up where they left off.

---

## 6. The Learning Path Data Structure

Understanding this structure is crucial. Here's what the AI generates and how it flows through the system:

```json
{
  "learning_path": {
    "subject": "Algebra",
    "description": "A guide to algebraic concepts...",
    "levels": [
      {
        "level": 1,
        "title": "Introduction to Algebra",
        "goal": "Understand basic algebraic terms.",
        "units": [
          {
            "unit": 1,
            "title": "Algebraic Expressions",
            "skills": ["Identify variables", "Write expressions", "Evaluate expressions"]
          },
          {
            "unit": 2,
            "title": "Basic Equations",
            "skills": ["Solve one-step equations", "Check solutions", "Translate words to equations"]
          }
        ]
      },
      {
        "level": 2,
        "title": "Working with Variables",
        "goal": "Manipulate equations involving variables.",
        "units": [...]
      }
    ]
  }
}
```

After `flatten_units()`, this becomes:

| Unit ID | Title | Skills | Status |
|---------|-------|--------|--------|
| L1U1 | Algebraic Expressions | Identify variables, Write expressions, Evaluate expressions | unlocked |
| L1U2 | Basic Equations | Solve one-step equations, Check solutions, ... | locked |
| L2U1 | Combining Like Terms | ... | locked |
| ... | ... | ... | locked |

---

## 7. Starting a Unit: AI Content Generation

When the user clicks a unit node on the learning path, the frontend calls `POST /api/unit/start`. This triggers another OpenAI call to generate the actual lesson content.

### The Endpoint

```python
@app.post("/api/unit/start")
def start_unit():
    unit_id = data.get("unit_id")  # e.g., "L1U1"

    # Safety checks
    if progress.get(unit_id, {}).get("status") == "locked":
        return jsonify({"error": "Unit is locked"}), 403

    # Get unit metadata (title and skills)
    unit_meta = state.get("unit_meta", {}).get(unit_id)

    # Generate content via OpenAI
    unit_json = generate_unit(
        topic=state.get("topic"),
        unit_title=unit_meta.get("title"),
        skills=unit_meta.get("skills"),
    )
```

### The AI Call: `generate_unit()`

This function in `unit_generator.py` asks OpenAI to produce both a lesson and a quiz:

```python
def generate_unit(topic, model="gpt-4o-mini", unit_title=None, skills=None):
    system_prompt = """
    You produce a single study-unit as JSON.
    LESSON1CONTENT must have EXACTLY 2 items:
      1. A LESSON (120-220 words)
      2. A QUIZ with exactly 5 questions (A/B/C/D, one correct)
    """
```

The response looks like:

```json
{
  "LESSON1CONTENT": [
    {
      "TYPE": "LESSON",
      "TEXT": "An algebraic expression combines numbers, variables..."
    },
    {
      "TYPE": "QUIZ",
      "QUESTIONS": [
        {
          "QUESTION_NUMBER": "1",
          "QUESTION": "What is a variable?",
          "OPTIONS": {
            "A": "A fixed number",
            "B": "A symbol representing an unknown value",
            "C": "An equation",
            "D": "A mathematical operation"
          },
          "CORRECT_ANSWER": "B"
        }
      ]
    }
  ]
}
```

### Extracting Lessons and Questions

Back in `app.py`, two helper functions separate the content:

```python
def _extract_lessons(lessoncontent):
    return [item for item in lessoncontent if item.get("TYPE") == "LESSON"]

def _extract_quiz_questions(lessoncontent):
    quizzes = [item for item in lessoncontent if item.get("TYPE") == "QUIZ"]
    return quizzes[0].get("QUESTIONS", []) if quizzes else []
```

The state gets updated:

```python
state["active_unit_id"] = unit_id
state["lessons"] = lessons          # ["An algebraic expression combines..."]
state["questions"] = questions      # [{ QUESTION: "...", OPTIONS: {...}, CORRECT_ANSWER: "B" }, ...]
state["q_index"] = 0               # Start at first question
```

---

## 8. The Quiz Loop: Answering Questions

The quiz is a back-and-forth between frontend and backend. Each answer is one API call.

### The Endpoint: `POST /api/answer`

```python
@app.post("/api/answer")
def answer():
    user_answer = data.get("answer").strip().upper()  # "A", "B", "C", or "D"

    questions = state.get("questions", [])
    q_index = state.get("q_index", 0)

    # Safety: don't go past the last question
    if q_index >= len(questions):
        return jsonify({"error": "Quiz already finished", "done": True}), 400

    # Check the answer
    q = questions[q_index]
    correct = (user_answer == q.get("CORRECT_ANSWER"))

    # Update coins
    if correct:
        state["coins"] = state.get("coins", 0) + 10
    else:
        state["coins"] = max(state.get("coins", 0) - 5, 0)  # Never below 0

    # Move to next question
    state["q_index"] = q_index + 1
```

### Unit Completion

When the last question is answered, the unit is marked as completed and the next unit is unlocked:

```python
if next_q is None:  # No more questions
    active_unit_id = state.get("active_unit_id")
    state["progress"][active_unit_id]["status"] = "completed"

    # Unlock the next unit in sequence
    nxt = next_unit_id(state.get("unit_order", []), active_unit_id)
    if nxt and state["progress"][nxt].get("status") != "completed":
        state["progress"][nxt]["status"] = "unlocked"
```

`next_unit_id()` simply finds the current unit in the order list and returns the one after it:

```python
def next_unit_id(unit_order, current_id):
    idx = unit_order.index(current_id)
    if idx + 1 < len(unit_order):
        return unit_order[idx + 1]
    return None
```

---

## 9. The AI Tutor: Feedback on Wrong Answers

When the user answers wrong **and** has the tutor enabled, the backend asks OpenAI to explain why:

```python
if (not correct) and state.get("use_tutor"):
    feedback = _build_tutor_feedback(q, user_answer)
```

### Building the Tutor Prompt

```python
def _build_tutor_feedback(question_data, user_answer):
    # Format the question for the AI
    prompt = f"Question: {question_text}\nOptions:\n{option_lines}\n"

    context = (
        "Please explain the user's mistake in JSON.\n"
        f"User answered: {user_answer} ({user_text}). "
        f"Correct answer: {correct_letter} ({correct_text}). "
        "Give a short recap of the concept."
    )

    return ai_tutor_reply(question=prompt, context=context)
```

### The AI Tutor Call: `ai_tutor_reply()`

```python
def ai_tutor_reply(question, context, model="gpt-4o-mini"):
    system_prompt = """
    You are a friendly study-buddy AI tutor.
    Always respond ONLY with valid JSON:
    {
      "message": "<short encouraging message>",
      "explanation": "<2-4 sentence explanation>",
      "user_answer": "<what the user chose>",
      "correct_answer": "<the right answer>"
    }
    """
```

The tutor is designed to be **encouraging**, not punishing. It explains the concept, not just says "wrong."

---

## 10. Progress Tracking and Persistence

Progress tracking has **two layers**: short-term (in-memory) and long-term (Firestore).

### Layer 1: In-Memory (`SESSIONS` dict)

```python
SESSIONS: Dict[str, Dict[str, Any]] = {}
```

This is a Python dictionary keyed by session ID. It holds everything about the user's current session: their topic, progress, current quiz questions, coin count, etc.

**Advantage:** Fast. No database calls needed during a quiz.
**Disadvantage:** Lost when the server restarts. This is why Firestore is needed.

### Layer 2: Firestore (Persistent)

Firestore stores three types of data per user per topic:

```
users/{uid}/
    learning_paths/{topic}    ← The AI-generated curriculum
    progress/{topic}          ← Unit statuses and coins
    sessions/{topic}          ← Full session snapshot (for mid-quiz resume)
```

### When Does Saving Happen?

The frontend triggers saves at key moments:

| Moment | What's Saved |
|--------|-------------|
| Topic started | Learning path (if newly generated) |
| Unit started | Progress (unit statuses, coins) |
| Answer submitted | Progress + session state |
| Auto-save timer | Every 30 seconds (if active) |

### The Save Endpoints

**`POST /api/save-progress`** — Saves the lightweight progress data:
```python
save_progress(uid, topic, units={
    "L1U1": {"status": "completed"},
    "L1U2": {"status": "unlocked"},
    ...
}, coins=50, active_unit_id="L1U2")
```

**`POST /api/save-session`** — Saves a full session snapshot (for mid-quiz recovery):
```python
save_session_state(uid, topic, {
    "progress": {...},
    "coins": 50,
    "active_unit_id": "L1U2",
    "lessons": ["lesson text..."],
    "questions": [{...}, {...}],
    "q_index": 3
})
```

### The Restore Flow

When `/api/start` is called for a topic the user has already started:

1. Load the saved learning path (skip AI generation)
2. Build a fresh progress map with `init_progress()`
3. Load saved progress from Firestore
4. Merge saved statuses over the fresh defaults
5. Restore the saved coin count

```python
progress = init_progress(unit_order)  # All locked except first
saved = get_progress(uid, topic)
if saved:
    for uid_key, status_data in saved.get("units", {}).items():
        if uid_key in progress:
            progress[uid_key] = status_data  # Completed stays completed
    saved_coins = saved.get("coins", 0)
```

### Resuming a Quiz Mid-Way

If a user leaves during a quiz, the frontend saves quiz state to `localStorage`. When they return:

1. Frontend finds saved quiz data in localStorage
2. Frontend calls `POST /api/unit/resume` with the saved questions and index
3. Backend restores its in-memory state to match

```python
@app.post("/api/unit/resume")
def resume_unit():
    state["active_unit_id"] = unit_id
    state["questions"] = questions    # The full question list
    state["q_index"] = q_index       # Where they left off
    state["lessons"] = lessons
    state["coins"] = coins
```

This is needed because the backend's in-memory `SESSIONS` dict doesn't survive server restarts, but the frontend's localStorage does.

---

## 11. Session Management: Two Layers

### Flask Session (Cookie)

Flask's `session` object stores a small amount of data in a **signed cookie**:

```python
session["uid"] = uid
session["email"] = email
session["name"] = name
```

This cookie travels with every request, so the backend always knows **who** is making the request. It's signed with `app.secret_key` so users can't tamper with it.

### In-Memory Session (`SESSIONS` dict)

The heavy data (learning paths, questions, progress) lives in the `SESSIONS` dictionary:

```python
def _get_state():
    sid = _get_session_id()          # From the cookie
    if sid not in SESSIONS:
        SESSIONS[sid] = {}
    return SESSIONS[sid]
```

Each user gets a unique session ID (UUID), stored in their cookie. The `SESSIONS` dict maps that ID to their full state.

### The `session_state.py` Template

This file defines the "shape" of a session:

```python
def default_state():
    return {
        "user": None,
        "topic": None,
        "use_tutor": False,
        "learning_path": None,
        "coins": 0,
        "progress": {},
        "unit_order": [],
        "unit_meta": {},
        "active_unit_id": None,
        "lessons": [],
        "questions": [],
        "q_index": 0
    }
```

When a new topic is started, the state is reset to these defaults and then populated:

```python
state = _get_state()
state.clear()
state.update(default_state())
state["user"] = username
state["topic"] = topic
# ... fill in the rest
```

---

## 12. The Coin System

Coins are a simple gamification mechanic:

| Event | Coins |
|-------|-------|
| Correct answer | +10 |
| Wrong answer | -5 (minimum 0) |

```python
if correct:
    state["coins"] = state.get("coins", 0) + 10
else:
    state["coins"] = max(state.get("coins", 0) - 5, 0)
```

Coins persist across units within a topic and are saved to Firestore so they survive between sessions.

---

## 13. Data Flow Diagrams

### Full User Journey

```
┌─────────────────────────────────────────────────────────┐
│                    USER JOURNEY                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Open app                                            │
│     └──► GET / → serves index.html                      │
│                                                         │
│  2. Sign in with Google                                 │
│     └──► POST /api/auth → verify token → save user      │
│                                                         │
│  3. Pick a topic ("Algebra")                            │
│     └──► POST /api/start                                │
│           ├── Check Firestore for saved path             │
│           ├── If none: OpenAI generates path             │
│           ├── Save path to Firestore                     │
│           ├── Build/restore progress                     │
│           └── Return path + progress + coins             │
│                                                         │
│  4. Click a unit (L1U1)                                 │
│     └──► POST /api/unit/start                           │
│           ├── OpenAI generates lesson + quiz              │
│           └── Return lessons + first question            │
│                                                         │
│  5. Answer questions (repeat 5x)                        │
│     └──► POST /api/answer                               │
│           ├── Check answer, update coins                 │
│           ├── If wrong + tutor: OpenAI explains          │
│           ├── If last question: mark unit completed      │
│           ├── Unlock next unit                           │
│           └── Save progress to Firestore                 │
│                                                         │
│  6. Continue to next unit or come back later             │
│     └──► Progress is saved — user can resume anytime     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Firestore Data Model

```
Firestore Database
│
└── users (collection)
    │
    └── {uid} (document)
        │   ├── email: "alex@gmail.com"
        │   ├── display_name: "Alex"
        │   ├── photo_url: "https://..."
        │   ├── created_at: <timestamp>
        │   └── last_login: <timestamp>
        │
        ├── learning_paths (subcollection)
        │   └── "Algebra" (document)
        │       ├── learning_path: { subject, description, levels: [...] }
        │       ├── unit_meta: { "L1U1": { title, skills }, ... }
        │       ├── unit_order: ["L1U1", "L1U2", "L2U1", ...]
        │       └── created_at / updated_at
        │
        ├── progress (subcollection)
        │   └── "Algebra" (document)
        │       ├── units: { "L1U1": { status: "completed" }, ... }
        │       ├── coins: 50
        │       ├── active_unit_id: "L2U1"
        │       └── updated_at
        │
        └── sessions (subcollection)
            └── "Algebra" (document)
                ├── progress: { ... }
                ├── coins: 50
                ├── active_unit_id: "L2U1"
                ├── lessons: [...]
                ├── questions: [...]
                ├── q_index: 3
                └── updated_at
```

---

## 14. File Reference

### `app.py` — The Server

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve the frontend HTML |
| `/api/start` | POST | Start or resume a topic |
| `/api/state` | GET | Get current session state |
| `/api/auth` | POST | Verify Google sign-in token |
| `/api/logout` | POST | Clear session |
| `/api/check-auth` | GET | Check if user is authenticated |
| `/api/topics` | GET | List user's started topics |
| `/api/save-progress` | POST | Save progress to Firestore |
| `/api/load-progress/<topic>` | GET | Load saved progress |
| `/api/save-session` | POST | Save full session state |
| `/api/load-session/<topic>` | GET | Load full session state |
| `/api/delete-data` | DELETE | Delete all user data |
| `/api/pathway` | GET | Get current learning path |
| `/api/progress` | GET | Get current progress from memory |
| `/api/unit/start` | POST | Generate and start a unit |
| `/api/unit/resume` | POST | Resume a quiz mid-way |
| `/api/answer` | POST | Submit a quiz answer |

### `firestore_db.py` — Database Layer

| Function | Purpose |
|----------|---------|
| `init_firestore()` | Initialize Firestore client |
| `get_firestore_client()` | Get the singleton client |
| `upsert_user()` | Create or update user profile |
| `get_user()` | Get user profile |
| `save_progress()` | Save unit statuses + coins |
| `get_progress()` | Load unit statuses + coins |
| `save_learning_path()` | Save AI-generated curriculum |
| `get_learning_path()` | Load saved curriculum |
| `save_session_state()` | Save full session snapshot |
| `get_session_state()` | Load full session snapshot |
| `delete_user_data()` | Delete all subcollections for a user |
| `get_all_topics_for_user()` | List all topics a user has started |

### `path_generator.py` — AI Curriculum Generator

| Function | Purpose |
|----------|---------|
| `generate_pathway(topic, model)` | Ask OpenAI to create a 5-level learning path |

### `learning_path.py` — Path Processing

| Function | Purpose |
|----------|---------|
| `extract_learning_path(pathway)` | Pull the learning_path object from AI response |
| `build_unit_id(level, unit)` | Create ID like "L2U3" |
| `flatten_units(learning_path)` | Convert nested levels → flat unit_order + unit_meta |
| `init_progress(unit_order)` | Create initial progress (first unlocked, rest locked) |
| `next_unit_id(unit_order, current)` | Get the next unit in sequence |

### `unit_generator.py` — AI Content Generator

| Function | Purpose |
|----------|---------|
| `generate_unit(topic, model, unit_title, skills)` | Generate lesson text + 5 quiz questions |
| `generate_quiz(topic, model)` | Generate standalone quiz (not used by web app) |

### `tutor_helper.py` — AI Tutor

| Function | Purpose |
|----------|---------|
| `ai_tutor_reply(question, context, model)` | Generate encouraging explanation for wrong answers |

### `session_state.py` — State Template

| Function | Purpose |
|----------|---------|
| `default_state()` | Return a blank session state dictionary |
| `hydrate(raw)` | Merge raw data with defaults |

### `env_loader.py` — Configuration

| Function | Purpose |
|----------|---------|
| `get_openai_api_key()` | Load OpenAI API key from env or .env file |

---

## 15. Key Concepts Glossary

| Term | Meaning |
|------|---------|
| **Flask** | A lightweight Python web framework. It maps URLs to Python functions. |
| **Endpoint / Route** | A URL pattern (like `/api/start`) that triggers a specific function. |
| **Session (Flask)** | A signed cookie that stores small data (uid, email) between requests. |
| **SESSIONS dict** | An in-memory Python dictionary holding full user state. Lost on restart. |
| **Firestore** | Google's NoSQL cloud database. Data organized as collections → documents. |
| **Firebase Auth** | Google's authentication service. Handles Google sign-in and token verification. |
| **ID Token** | A JWT (JSON Web Token) proving the user signed in via Google. |
| **`verify_id_token()`** | Server-side function that cryptographically validates an ID token. |
| **OpenAI API** | The AI service that generates learning paths, lessons, quizzes, and feedback. |
| **`gpt-4o-mini`** | A fast, cheap OpenAI model used for all content generation. |
| **`response_format: json_object`** | Forces OpenAI to return valid JSON instead of free-form text. |
| **Learning Path** | The AI-generated curriculum: 5 levels, 2 units each, 3 skills per unit. |
| **Unit ID** | A string like "L2U1" meaning Level 2, Unit 1. |
| **Progress Map** | A dictionary mapping unit IDs to statuses: `locked`, `unlocked`, or `completed`. |
| **Upsert** | "Update or Insert" — create if new, update if existing. |
| **merge=True** | Firestore option: update only the specified fields, don't overwrite the whole document. |
| **SERVER_TIMESTAMP** | Firestore sets this to the server's current time (more reliable than client time). |
| **Singleton** | A pattern where only one instance exists (used for the Firestore client). |
| **IIFE** | "Immediately Invoked Function Expression" — a JS pattern used by ProgressTracker. |
