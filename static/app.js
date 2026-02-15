// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyClfLemHP4FoD3xwmEFCOhJ5Gh8AetTMHo",
  authDomain: "theorem-8a4e5.firebaseapp.com",
  projectId: "theorem-8a4e5",
  storageBucket: "theorem-8a4e5.firebasestorage.app",
  messagingSenderId: "508241176996",
  appId: "1:508241176996:web:f43f6e2325e68aededf931",
};

// Initialize Firebase (script-tag / compat SDK)
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const provider = new firebase.auth.GoogleAuthProvider();

document.addEventListener("DOMContentLoaded", () => {
  const googleSignInButton = document.querySelector("#google-signin-btn");
  const signOutButton = document.querySelector("#signout-btn");
  const authStatus = document.querySelector("#auth-status");
  const userInfo = document.querySelector("#user-info");
  const userName = document.querySelector("#user-name");
  const deleteDataSection = document.querySelector("#delete-data-section");
  const deleteDataBtn = document.querySelector("#delete-data-btn");
  const userAvatar = document.querySelector("#user-avatar");

  // AUTH HELPER FUNCTIONS
  function setAuthUI(user) {
    if (!googleSignInButton || !userInfo || !userName) return;
    if (user) {
      googleSignInButton.classList.add("hidden");
      userInfo.classList.remove("hidden");
      if (deleteDataSection) deleteDataSection.classList.remove("hidden");
      const displayName = user.displayName || user.email || "Signed In";
      userName.textContent = displayName;
      if (userAvatar) {
        const photo = user.photoURL || "";
        userAvatar.src = photo;
        userAvatar.style.display = photo ? "" : "none";
      }
      // Auto-fill username input
      if (usernameInput) {
        usernameInput.value = displayName;
        usernameInput.dispatchEvent(new Event("input", { bubbles: true }));
      }
    } else {
      googleSignInButton.classList.remove("hidden");
      userInfo.classList.add("hidden");
      if (deleteDataSection) deleteDataSection.classList.add("hidden");
      userName.textContent = "";
      if (userAvatar) {
        userAvatar.src = "";
        userAvatar.style.display = "none";
      }
    }
  }

  async function checkBackendAuth() {
    try {
      const res = await fetch("/api/check-auth");
      const data = await res.json();
      return data.authenticated ? data : null;
    } catch (err) {
      console.error("Failed to check auth:", err);
      return null;
    }
  }

  async function sendIdTokenToBackend(user) {
    const idToken = await user.getIdToken();
    const res = await fetch("/api/auth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Auth failed");
    return data;
  }

  // AUTH EVENT HANDLERS
  if (googleSignInButton) {
    googleSignInButton.addEventListener("click", async () => {
      if (authStatus) authStatus.textContent = "Signing in...";
      try {
        const result = await auth.signInWithPopup(provider);
        const authData = await sendIdTokenToBackend(result.user);
        current.uid = authData.uid;
        setAuthUI(result.user);
        // Ensure button is enabled after sign-in
        if (usernameInput && continueBtn) {
          const val = usernameInput.value.trim();
          continueBtn.disabled = val.length === 0;
        }
        if (authStatus) authStatus.textContent = "Signed in!";
      } catch (err) {
        if (authStatus)
          authStatus.textContent = err.message || "Sign in failed.";
      }
    });
  }

  if (signOutButton) {
    signOutButton.addEventListener("click", async () => {
      if (authStatus) authStatus.textContent = "Signing out...";
      try {
        await auth.signOut();
        await fetch("/api/logout", { method: "POST" });
        ProgressTracker.cleanup();
        current.uid = null;
        setAuthUI(null);
        if (authStatus) authStatus.textContent = "Signed out.";
      } catch (err) {
        if (authStatus)
          authStatus.textContent = err.message || "Sign out failed.";
      }
    });
  }

  if (deleteDataBtn) {
    deleteDataBtn.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to delete all saved progress? This cannot be undone.")) return;
      deleteDataBtn.disabled = true;
      deleteDataBtn.textContent = "Deleting...";
      try {
        const res = await fetch("/api/delete-data", { method: "DELETE" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to delete data");
        // Clear localStorage quiz data
        try {
          const keys = [];
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(QUIZ_STORAGE_PREFIX)) keys.push(key);
          }
          keys.forEach((k) => localStorage.removeItem(k));
        } catch (e) { /* ignore */ }
        ProgressTracker.cleanup();
        if (authStatus) authStatus.textContent = "All saved data deleted.";
      } catch (err) {
        if (authStatus) authStatus.textContent = err.message || "Delete failed.";
      } finally {
        deleteDataBtn.disabled = false;
        deleteDataBtn.textContent = "Delete all saved progress";
      }
    });
  }

  auth.onAuthStateChanged(async (user) => {
    setAuthUI(user);
    if (user) {
      const backendAuth = await checkBackendAuth();
      if (backendAuth) {
        current.uid = backendAuth.uid;
      } else {
        // Backend session doesn't match Firebase, re-authenticate
        const idToken = await user.getIdToken();
        try {
          const res = await fetch("/api/auth", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ idToken }),
          });
          const data = await res.json();
          if (res.ok) current.uid = data.uid;
        } catch (err) {
          console.error("Failed to sync backend auth:", err);
        }
      }
    } else {
      current.uid = null;
    }
  });

  // Initialize progress tracking
  ProgressTracker.init();

  const topics = [
    {
      id: "addition",
      label: "Addition",
      description: "Let’s add some fun!",
      icon: "➕",
    },
    {
      id: "subtraction",
      label: "Subtraction",
      description: "Take it away!",
      icon: "➖",
    },
    {
      id: "multiplication",
      label: "Multiplication",
      description: "Multiply the magic!",
      icon: "✖️",
    },
    {
      id: "division",
      label: "Division",
      description: "Share and divide!",
      icon: "➗",
    },
    {
      id: "fractions",
      label: "Fractions",
      description: "Slice it up!",
      icon: "🥧",
    },
    { id: "algebra", label: "Algebra", description: "Solve for X!", icon: "𝑥" },
    {
      id: "trigonometry",
      label: "Trigonometry",
      description: "Sin, cos, tan!",
      icon: "📐",
    },
    {
      id: "calculus",
      label: "Calculus",
      description: "Derivatives and more!",
      icon: "∫",
    },
  ];

  const welcomeScreen = document.querySelector("#welcome-screen");
  const topicsScreen = document.querySelector("#topics-screen");
  const pathScreen = document.querySelector("#path-screen");
  const lessonScreen = document.querySelector("#lesson-screen");
  const quizScreen = document.querySelector("#quiz-screen");

  const form = document.querySelector("#welcome-form");
  const usernameInput = document.querySelector("#username");
  const usernameError = document.querySelector("#username-error");
  const continueBtn = document.querySelector("#continue-btn");
  const greetName = document.querySelector("#greet-name");

  const topicsGrid = document.querySelector("#topics-grid");
  const backBtn = document.querySelector("#back-btn");
  const startBtn = document.querySelector("#start-btn");
  const startStatus = document.querySelector("#start-status");

  const pathBackBtn = document.querySelector("#path-back-btn");
  const pathStatus = document.querySelector("#path-status");
  const pathSubject = document.querySelector("#path-subject");
  const pathDescription = document.querySelector("#path-desc");
  const pathTimeline = document.querySelector("#path-timeline");
  const coinCount = document.querySelector("#coin-count");

  const lessonBackBtn = document.querySelector("#lesson-back-btn");
  const lessonCoinCount = document.querySelector("#lesson-coin-count");
  const unitTitleEl = document.querySelector("#unit-title");
  const unitSkillsEl = document.querySelector("#unit-skills");
  const unitLessonsEl = document.querySelector("#unit-lessons");
  const startQuizBtn = document.querySelector("#start-quiz-btn");
  const lessonStatus = document.querySelector("#lesson-status");

  const quizBackBtn = document.querySelector("#quiz-back-btn");
  const quizCoinCount = document.querySelector("#quiz-coin-count");
  const quizQuestionEl = document.querySelector("#quiz-question");
  const quizOptionsEl = document.querySelector("#quiz-options");
  const quizFeedbackEl = document.querySelector("#quiz-feedback");
  const quizNextBtn = document.querySelector("#quiz-next-btn");
  const quizStatus = document.querySelector("#quiz-status");
  const unitLoadingOverlay = document.querySelector("#unit-loading-overlay");

  const timelineLineMarkup = '<div class="timeline-line"></div>';
  const QUIZ_STORAGE_PREFIX = "theorem.quizProgress";
  const QUIZ_STORAGE_TTL_MS = 24 * 60 * 60 * 1000;

  let username = "";
  let selectedTopicId = null;
  let current = {
    uid: null,
    topic: null,
    learningPath: null,
    progress: {},
    unitMeta: {},
    unitOrder: [],
    activeUnitId: null,
    coins: 0,
  };
  let unitSession = {
    unitId: null,
    unitMeta: null,
    lessons: [],
    currentQuestion: null,
    pendingNextQuestion: null,
    done: false,
    feedbackText: "",
    awaitingNext: false,
  };
  let isAnswerSubmitting = false;
  let isUnitLoading = false;

  function safeLocalStorageGet(key) {
    try {
      return localStorage.getItem(key);
    } catch (err) {
      return null;
    }
  }

  function safeLocalStorageSet(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (err) {
      // Ignore storage errors (quota/private mode)
    }
  }

  function safeLocalStorageRemove(key) {
    try {
      localStorage.removeItem(key);
    } catch (err) {
      // Ignore storage errors
    }
  }

  function getQuizStorageKey(unitId) {
    const topicKey = encodeURIComponent(current.topic || "unknown");
    return `${QUIZ_STORAGE_PREFIX}.${topicKey}.${unitId}`;
  }

  function loadQuizProgress(unitId) {
    const key = getQuizStorageKey(unitId);
    const raw = safeLocalStorageGet(key);
    if (!raw) return null;
    try {
      const data = JSON.parse(raw);
      if (!data || data.unitId !== unitId) {
        safeLocalStorageRemove(key);
        return null;
      }
      if (data.savedAt && Date.now() - data.savedAt > QUIZ_STORAGE_TTL_MS) {
        safeLocalStorageRemove(key);
        return null;
      }
      if (data.done) {
        safeLocalStorageRemove(key);
        return null;
      }
      if (!data.currentQuestion || !Array.isArray(data.lessons)) {
        safeLocalStorageRemove(key);
        return null;
      }
      return data;
    } catch (err) {
      safeLocalStorageRemove(key);
      return null;
    }
  }

  function clearQuizProgress(unitId) {
    if (!unitId) return;
    safeLocalStorageRemove(getQuizStorageKey(unitId));
  }

  function persistQuizProgress() {
    if (!unitSession.unitId) return;
    if (unitSession.done) {
      clearQuizProgress(unitSession.unitId);
      return;
    }
    const payload = {
      savedAt: Date.now(),
      unitId: unitSession.unitId,
      unitMeta: unitSession.unitMeta,
      lessons: unitSession.lessons,
      currentQuestion: unitSession.currentQuestion,
      pendingNextQuestion: unitSession.pendingNextQuestion,
      done: unitSession.done,
      feedbackText: unitSession.feedbackText || "",
      awaitingNext: Boolean(unitSession.awaitingNext),
      // Store full quiz state for backend resume
      allQuestions: unitSession.allQuestions || [],
      qIndex: unitSession.qIndex || 0,
      coins: current.coins || 0,
    };
    safeLocalStorageSet(
      getQuizStorageKey(unitSession.unitId),
      JSON.stringify(payload),
    );
  }

  function setUnitLoading(isLoading) {
    if (!unitLoadingOverlay) return;
    unitLoadingOverlay.classList.toggle("hidden", !isLoading);
    unitLoadingOverlay.setAttribute("aria-hidden", String(!isLoading));
  }

  function setStep(step) {
    [welcomeScreen, topicsScreen, pathScreen, lessonScreen, quizScreen].forEach(
      (el) => el.classList.remove("active"),
    );
    if (step === "welcome") welcomeScreen.classList.add("active");
    if (step === "topics") topicsScreen.classList.add("active");
    if (step === "path") pathScreen.classList.add("active");
    if (step === "lesson") lessonScreen.classList.add("active");
    if (step === "quiz") quizScreen.classList.add("active");
  }

  function setCoins(coins) {
    current.coins = coins ?? current.coins ?? 0;
    coinCount.textContent = String(current.coins);
    lessonCoinCount.textContent = String(current.coins);
    quizCoinCount.textContent = String(current.coins);
  }

  function renderTopics() {
    topicsGrid.innerHTML = topics
      .map(
        (t) => `
      <button class="topic-card" data-id="${t.id}" aria-pressed="false">
        <div class="topic-icon">${t.icon}</div>
        <h3 class="topic-title">${t.label}</h3>
        <p class="topic-desc">${t.description}</p>
      </button>
    `,
      )
      .join("");

    topicsGrid.querySelectorAll(".topic-card").forEach((btn) => {
      btn.addEventListener("click", () => selectTopic(btn.dataset.id));
    });
  }

  function selectTopic(id) {
    selectedTopicId = id;
    topicsGrid.querySelectorAll(".topic-card").forEach((btn) => {
      const isSelected = btn.dataset.id === id;
      btn.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
    startBtn.disabled = false;
  }

  function buildLevelCard(level) {
    const card = document.createElement("section");
    card.className = "level-card";
    card.innerHTML = `
      <div class="level-badge">🏁</div>
      <div class="level-body">
        <div class="level-title">Level ${level.level} <span>${level.title}</span></div>
        <p class="level-subtitle">${level.goal}</p>
      </div>
    `;
    return card;
  }

  function buildUnitNode(unitId, unitMeta, status) {
    const node = document.createElement("div");
    node.className = `unit-node ${status || ""}`.trim();
    const unitNumber = unitMeta.unit || "?";
    const title = unitMeta.title || "Unit";
    const locked = status === "locked";
    node.innerHTML = `
      <button class="unit-icon" ${locked ? "disabled" : ""} data-unit-id="${unitId}" aria-label="Unit ${unitNumber}: ${title}">
        ${unitNumber}
      </button>
      <div class="unit-label">Unit ${unitNumber}: ${title}</div>
    `;
    const btn = node.querySelector("button.unit-icon");
    btn.addEventListener("click", () => startUnit(unitId));
    return node;
  }

  function renderLearningPath(learningPath, progress, unitMetaMap) {
    const lp = learningPath?.learning_path || learningPath;
    if (!lp) return;

    pathSubject.textContent = lp.subject || "";
    pathDescription.textContent = lp.description || "";

    pathTimeline.innerHTML = timelineLineMarkup;
    (lp.levels || []).forEach((level) => {
      pathTimeline.appendChild(buildLevelCard(level));
      (level.units || []).forEach((u) => {
        const unitId = `L${level.level}U${u.unit}`;
        const unitMeta = unitMetaMap?.[unitId] || {
          unit: u.unit,
          title: u.title,
          skills: u.skills,
        };
        const status = progress?.[unitId]?.status || "locked";
        pathTimeline.appendChild(buildUnitNode(unitId, unitMeta, status));
      });
    });
  }

  async function startTopic() {
    if (!selectedTopicId) return;
    startBtn.disabled = true;
    startStatus.textContent = "Generating your learning path…";
    pathStatus.textContent = "";

    const topic =
      topics.find((t) => t.id === selectedTopicId)?.label || selectedTopicId;
    try {
      const res = await fetch("/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, username, use_tutor: false }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to start");

      current.learningPath = data.pathway;
      current.progress = data.progress || {};
      current.unitMeta = data.unit_meta || {};
      current.unitOrder = data.unit_order || [];
      current.topic = topic;
      current.activeUnitId = null;
      setCoins(data.coins || 0);

      renderLearningPath(
        current.learningPath,
        current.progress,
        current.unitMeta,
      );
      setStep("path");

      // Save progress to Firestore
      if (current.uid) {
        ProgressTracker.saveProgress({
          topic: topic,
          progress: current.progress,
          coins: current.coins,
          activeUnitId: current.activeUnitId,
        });
      }
    } catch (err) {
      startStatus.textContent = err.message;
      startBtn.disabled = false;
    }
  }

  async function startUnit(unitId) {
    if (isUnitLoading) return;
    const saved = loadQuizProgress(unitId);
    if (saved && saved.allQuestions && saved.allQuestions.length > 0) {
      unitSession.unitId = saved.unitId;
      unitSession.unitMeta =
        saved.unitMeta || current.unitMeta?.[unitId] || null;
      unitSession.lessons = saved.lessons || [];
      unitSession.currentQuestion = saved.currentQuestion || null;
      unitSession.pendingNextQuestion = saved.pendingNextQuestion || null;
      unitSession.done = Boolean(saved.done);
      unitSession.feedbackText = saved.feedbackText || "";
      unitSession.awaitingNext = Boolean(saved.awaitingNext);
      unitSession.allQuestions = saved.allQuestions || [];
      unitSession.qIndex = saved.qIndex || 0;
      current.activeUnitId = saved.unitId;

      // Sync backend so /api/answer works
      try {
        await fetch("/api/unit/resume", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            unit_id: saved.unitId,
            questions: saved.allQuestions,
            q_index: saved.qIndex,
            lessons: saved.lessons,
            coins: saved.coins || current.coins || 0,
          }),
        });
      } catch (err) {
        console.error("Failed to resume backend quiz state:", err);
      }

      renderUnitLesson(unitSession.unitMeta, unitSession.lessons);
      setStep("lesson");
      persistQuizProgress();
      return;
    }
    // If saved data exists but has no questions, clear it and start fresh
    if (saved) {
      clearQuizProgress(unitId);
    }
    isUnitLoading = true;
    setUnitLoading(true);
    lessonStatus.textContent = "";
    quizStatus.textContent = "";
    quizFeedbackEl.textContent = "";
    quizNextBtn.disabled = true;
    try {
      const res = await fetch("/api/unit/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ unit_id: unitId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to start unit");

      current.progress = data.progress || current.progress;
      current.activeUnitId = data.unit_id;
      setCoins(data.coins);

      unitSession.unitId = data.unit_id;
      unitSession.unitMeta = data.unit_meta;
      unitSession.lessons = data.lessons || [];
      unitSession.currentQuestion = data.question || null;
      unitSession.pendingNextQuestion = null;
      unitSession.done = false;
      unitSession.feedbackText = "";
      unitSession.awaitingNext = false;
      unitSession.allQuestions = data.all_questions || [];
      unitSession.qIndex = 0;

      renderUnitLesson(unitSession.unitMeta, unitSession.lessons);
      setStep("lesson");
      persistQuizProgress();

      // Save unit progress to Firestore
      if (current.uid) {
        ProgressTracker.saveProgress({
          topic: current.topic,
          progress: current.progress,
          coins: current.coins,
          activeUnitId: current.activeUnitId,
        });
      }
    } catch (err) {
      pathStatus.textContent = err.message;
    } finally {
      isUnitLoading = false;
      setUnitLoading(false);
    }
  }

  function renderUnitLesson(unitMeta, lessons) {
    unitTitleEl.textContent = unitMeta?.title
      ? `Unit: ${unitMeta.title}`
      : "Unit";
    unitSkillsEl.innerHTML = "";
    (unitMeta?.skills || []).forEach((skill) => {
      const pill = document.createElement("span");
      pill.className = "skill-pill";
      pill.textContent = skill;
      unitSkillsEl.appendChild(pill);
    });
    unitLessonsEl.innerHTML = "";
    (lessons || []).forEach((text) => {
      const p = document.createElement("p");
      p.className = "lesson-text";
      p.textContent = text;
      unitLessonsEl.appendChild(p);
    });
  }

  function renderQuestion(question) {
    quizFeedbackEl.textContent = "";
    quizNextBtn.textContent = "Next";
    quizNextBtn.disabled = true;
    quizOptionsEl.innerHTML = "";

    if (!question) {
      quizQuestionEl.textContent = "No question available.";
      return;
    }

    quizQuestionEl.textContent = question.QUESTION || "";
    const options = question.OPTIONS || {};
    ["A", "B", "C", "D"].forEach((letter) => {
      const btn = document.createElement("button");
      btn.className = "option-btn";
      btn.textContent = `${letter}. ${options[letter] || ""}`;
      btn.addEventListener("click", () => submitAnswer(letter));
      quizOptionsEl.appendChild(btn);
    });
  }

  function setOptionsEnabled(enabled) {
    quizOptionsEl.querySelectorAll("button.option-btn").forEach((btn) => {
      btn.disabled = !enabled;
    });
  }

  function syncQuizStateFromPending() {
    if (unitSession.awaitingNext) return;
    if (!unitSession.done && unitSession.pendingNextQuestion) {
      unitSession.currentQuestion = unitSession.pendingNextQuestion;
      unitSession.pendingNextQuestion = null;
    }
  }

  async function submitAnswer(letter) {
    if (isAnswerSubmitting) return;
    isAnswerSubmitting = true;
    quizStatus.textContent = "Checking answer...";
    quizBackBtn.disabled = true;
    setOptionsEnabled(false);
    try {
      const res = await fetch("/api/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: letter }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to submit answer");
      quizStatus.textContent = "";

      current.progress = data.progress || current.progress;
      setCoins(data.coins);

      const correctness = data.correct ? "Correct! +10" : "Not quite. -5";
      let feedbackText = correctness;
      if (data.feedback?.message)
        feedbackText += `\n\n${data.feedback.message}`;
      if (data.feedback?.explanation)
        feedbackText += `\n${data.feedback.explanation}`;
      quizFeedbackEl.textContent = feedbackText;
      unitSession.feedbackText = feedbackText;

      unitSession.pendingNextQuestion = data.next_question || null;
      unitSession.done = Boolean(data.done);
      if (unitSession.done) unitSession.pendingNextQuestion = null;
      unitSession.awaitingNext = true;
      unitSession.qIndex = (unitSession.qIndex || 0) + 1;
      current.activeUnitId = data.active_unit_id || current.activeUnitId;

      if (unitSession.done) {
        quizNextBtn.textContent = "Back to Path";
      }
      quizNextBtn.disabled = false;
      if (unitSession.done) {
        clearQuizProgress(unitSession.unitId);
      } else {
        persistQuizProgress();
      }

      // Save progress to Firestore on every answer
      if (current.uid) {
        ProgressTracker.saveProgress({
          topic: current.topic,
          progress: current.progress,
          coins: current.coins,
          activeUnitId: current.activeUnitId,
        });
        ProgressTracker.saveSession(current.topic, {
          progress: current.progress,
          coins: current.coins,
          active_unit_id: current.activeUnitId,
          lessons: unitSession.lessons,
          questions: unitSession.allQuestions,
          q_index: unitSession.qIndex,
        });
      }
    } catch (err) {
      quizStatus.textContent = err.message;
      setOptionsEnabled(true);
    } finally {
      isAnswerSubmitting = false;
      quizBackBtn.disabled = false;
    }
  }

  function goToNextFromQuiz() {
    if (unitSession.done) {
      renderLearningPath(
        current.learningPath,
        current.progress,
        current.unitMeta,
      );
      setStep("path");
      return;
    }
    unitSession.currentQuestion = unitSession.pendingNextQuestion;
    unitSession.pendingNextQuestion = null;
    unitSession.feedbackText = "";
    unitSession.awaitingNext = false;
    renderQuestion(unitSession.currentQuestion);
    setOptionsEnabled(true);
    persistQuizProgress();
  }

  form.addEventListener("input", () => {
    const val = usernameInput.value.trim();
    const valid = val.length > 0;
    continueBtn.disabled = !valid;
    usernameError.textContent = valid ? "" : "Please enter your name.";
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const val = usernameInput.value.trim();
    if (!val) {
      usernameError.textContent = "Please enter your name.";
      continueBtn.disabled = true;
      return;
    }
    username = val;
    greetName.textContent = val;
    setStep("topics");
  });

  // Check for existing backend auth on page load
  checkBackendAuth().then((backendAuth) => {
    if (backendAuth && backendAuth.name && usernameInput) {
      usernameInput.value = backendAuth.name;
      usernameInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
    // Trigger initial validation in case backend auth wasn't found
    if (usernameInput) {
      usernameInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });

  backBtn.addEventListener("click", () => setStep("welcome"));
  startBtn.addEventListener("click", startTopic);
  pathBackBtn.addEventListener("click", () => {
    startBtn.disabled = selectedTopicId == null;
    startStatus.textContent = "";
    setStep("topics");
  });

  lessonBackBtn.addEventListener("click", () => {
    renderLearningPath(
      current.learningPath,
      current.progress,
      current.unitMeta,
    );
    setStep("path");
  });
  quizBackBtn.addEventListener("click", () => {
    syncQuizStateFromPending();
    persistQuizProgress();
    renderLearningPath(
      current.learningPath,
      current.progress,
      current.unitMeta,
    );
    setStep("path");
  });

  startQuizBtn.addEventListener("click", () => {
    syncQuizStateFromPending();
    if (!unitSession.currentQuestion) {
      lessonStatus.textContent = "No quiz loaded yet.";
      return;
    }
    renderQuestion(unitSession.currentQuestion);
    if (unitSession.awaitingNext) {
      quizFeedbackEl.textContent = unitSession.feedbackText || "";
      quizNextBtn.textContent = unitSession.done ? "Back to Path" : "Next";
      quizNextBtn.disabled = false;
      setOptionsEnabled(false);
    } else {
      setOptionsEnabled(true);
    }
    setStep("quiz");
  });

  quizNextBtn.addEventListener("click", goToNextFromQuiz);

  renderTopics();
  usernameInput.focus();
});
