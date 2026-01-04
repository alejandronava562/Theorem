document.addEventListener("DOMContentLoaded", () => {
  const topics = [
    { id: "addition", label: "Addition", description: "Let's add some fun!", icon: "➕" },
    { id: "subtraction", label: "Subtraction", description: "Take it away!", icon: "➖" },
    { id: "multiplication", label: "Multiplication", description: "Multiply the magic!", icon: "✖️" },
    { id: "division", label: "Division", description: "Share and divide!", icon: "➗" },
    { id: "fractions", label: "Fractions", description: "Slice it up!", icon: "🍕" },
    { id: "algebra", label: "Algebra", description: "Solve for X!", icon: "🧮" },
    { id: "triginometry", label: "Triginometry", description: "Sin,cos,tan!", icon: "🧮" },
    { id: "calculus", label: "Calculus", description: "Derivatives and More!, This is the easiest subject!", icon: "σ" },
  ];

  const welcomeScreen = document.querySelector("#welcome-screen");
  const topicsScreen = document.querySelector("#topics-screen");
  const form = document.querySelector("#welcome-form");
  const usernameInput = document.querySelector("#username");
  const usernameError = document.querySelector("#username-error");
  const continueBtn = document.querySelector("#continue-btn");
  const greetName = document.querySelector("#greet-name");
  const topicsGrid = document.querySelector("#topics-grid");
  const backBtn = document.querySelector("#back-btn");
  const startBtn = document.querySelector("#start-btn");
  const startStatus = document.querySelector("#start-status");
  const pathScreen = document.querySelector("#path-screen");
  const pathStatus = document.querySelector("#path-status");
  const pathSubject = document.querySelector("#path-subject")
  const pathDescription = document.querySelector("#path-desc");
  const pathTimeline = document.querySelector("#path-timeline");
  

  let selectedTopic = null;
  
  function setStep(step) {
    if (step === "welcome") {
      welcomeScreen.classList.add("active");
      topicsScreen.classList.remove("active");
      pathScreen.classList.remove("active");
      usernameInput.focus();
    } else if (step === "topics"){
      topicsScreen.classList.add("active");
      welcomeScreen.classList.remove("active");
      pathScreen.classList.remove("active");
      const firstCard = topicsGrid.querySelector(".topic-card");
      if (firstCard) firstCard.focus();
    } else if (step == "path") {
      pathScreen.classList.add("active");
      welcomeScreen.classList.remove("active");
      topicsScreen.classList.remove("active");
    }
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
    `
      )
      .join("");

    topicsGrid.querySelectorAll(".topic-card").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectTopic(btn.dataset.id);
      });
    });
  }

  function selectTopic(id) {
    selectedTopic = id;
    topicsGrid.querySelectorAll(".topic-card").forEach((btn) => {
      const isSelected = btn.dataset.id === id;
      btn.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
    startBtn.disabled = false;
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
    usernameError.textContent = "";
    greetName.textContent = val;
    setStep("topics");
  });

  backBtn.addEventListener("click", () => {
    setStep("welcome");
  });

  startBtn.addEventListener("click", async () => {
    if (!selectedTopic) return;
    startBtn.disabled = true;
    startStatus.textContent = "Generating Your Customized Lesson Path...";
    try {
      const res = await fetch("/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: selectedTopic, use_tutor: false }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to start");
      renderLearningPath(data.pathway)
      setStep("path")
    } catch (err) {
      startStatus.textContent = err.message;
      startBtn.disabled = false;
    }
  });

  renderTopics();
  usernameInput.focus();
  const timelineLineMarkup = '<div class="timeline-line"></div>';

  function buildLevelCard(level) {
    const card = document.createElement("section");
    card.className = "level-card";
    card.innerHTML = `
      <div class="level-badge">🏆</div>
      <div class="level-body">
        <div class="level-title">Level ${level.level} <span>${level.title}</span></div>
        <p class="level-subtitle">${level.goal}</p>
      </div>
    `;
    return card;
  }

  function renderLearningPath(pathway) {
    const lp = pathway?.learning_path || pathway?.learningPath || pathway;
    if (!lp) return;

    pathSubject.textContent = lp.subject || "";
    pathDescription.textContent = lp.description || "";

    pathTimeline.innerHTML = timelineLineMarkup;
    (lp.levels || []).forEach((level) => {
      pathTimeline.appendChild(buildLevelCard(level));
    });
  }
});

