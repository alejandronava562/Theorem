document.addEventListener("DOMContentLoaded", () => {
  const topics = [
    { id: "addition", label: "Addition", description: "Let’s add some fun!", icon: "➕" },
    { id: "subtraction", label: "Subtraction", description: "Take it away!", icon: "➖" },
    { id: "multiplication", label: "Multiplication", description: "Multiply the magic!", icon: "✖️" },
    { id: "division", label: "Division", description: "Share and divide!", icon: "➗" },
    { id: "fractions", label: "Fractions", description: "Slice it up!", icon: "🥧" },
    { id: "algebra", label: "Algebra", description: "Solve for X!", icon: "𝑥" },
    { id: "trigonometry", label: "Trigonometry", description: "Sin, cos, tan!", icon: "📐" },
    { id: "calculus", label: "Calculus", description: "Derivatives and more!", icon: "∫" },
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

  const timelineLineMarkup = '<div class="timeline-line"></div>';

  let username = "";
  let selectedTopicId = null;
  let current = {
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
  };

  function setStep(step) {
    [welcomeScreen, topicsScreen, pathScreen, lessonScreen, quizScreen].forEach((el) =>
      el.classList.remove("active"),
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

    const topic = topics.find((t) => t.id === selectedTopicId)?.label || selectedTopicId;
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
      setCoins(0);

      renderLearningPath(current.learningPath, current.progress, current.unitMeta);
      setStep("path");
    } catch (err) {
      startStatus.textContent = err.message;
      startBtn.disabled = false;
    }
  }

  async function startUnit(unitId) {
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
      setCoins(data.coins);

      unitSession.unitId = data.unit_id;
      unitSession.unitMeta = data.unit_meta;
      unitSession.lessons = data.lessons || [];
      unitSession.currentQuestion = data.question || null;
      unitSession.pendingNextQuestion = null;
      unitSession.done = false;

      renderUnitLesson(unitSession.unitMeta, unitSession.lessons);
      setStep("lesson");
    } catch (err) {
      pathStatus.textContent = err.message;
    }
  }

  function renderUnitLesson(unitMeta, lessons) {
    unitTitleEl.textContent = unitMeta?.title ? `Unit: ${unitMeta.title}` : "Unit";
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

  async function submitAnswer(letter) {
    quizStatus.textContent = "";
    setOptionsEnabled(false);
    try {
      const res = await fetch("/api/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: letter }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to submit answer");

      current.progress = data.progress || current.progress;
      setCoins(data.coins);

      const correctness = data.correct ? "Correct! +10" : "Not quite. -5";
      let feedbackText = correctness;
      if (data.feedback?.message) feedbackText += `\n\n${data.feedback.message}`;
      if (data.feedback?.explanation) feedbackText += `\n${data.feedback.explanation}`;
      quizFeedbackEl.textContent = feedbackText;

      unitSession.pendingNextQuestion = data.next_question || null;
      unitSession.done = Boolean(data.done);

      if (unitSession.done) {
        quizNextBtn.textContent = "Back to Path";
      }
      quizNextBtn.disabled = false;
    } catch (err) {
      quizStatus.textContent = err.message;
      setOptionsEnabled(true);
    }
  }

  function goToNextFromQuiz() {
    if (unitSession.done) {
      renderLearningPath(current.learningPath, current.progress, current.unitMeta);
      setStep("path");
      return;
    }
    unitSession.currentQuestion = unitSession.pendingNextQuestion;
    unitSession.pendingNextQuestion = null;
    renderQuestion(unitSession.currentQuestion);
    setOptionsEnabled(true);
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

  backBtn.addEventListener("click", () => setStep("welcome"));
  startBtn.addEventListener("click", startTopic);
  pathBackBtn.addEventListener("click", () => {
    startBtn.disabled = selectedTopicId == null;
    startStatus.textContent = "";
    setStep("topics");
  });

  lessonBackBtn.addEventListener("click", () => {
    renderLearningPath(current.learningPath, current.progress, current.unitMeta);
    setStep("path");
  });
  quizBackBtn.addEventListener("click", () => {
    renderLearningPath(current.learningPath, current.progress, current.unitMeta);
    setStep("path");
  });

  startQuizBtn.addEventListener("click", () => {
    if (!unitSession.currentQuestion) {
      lessonStatus.textContent = "No quiz loaded yet.";
      return;
    }
    renderQuestion(unitSession.currentQuestion);
    setOptionsEnabled(true);
    setStep("quiz");
  });

  quizNextBtn.addEventListener("click", goToNextFromQuiz);

  renderTopics();
  usernameInput.focus();
});
