document.addEventListener("DOMContentLoaded", () => {
    const topics = [
        {id: "addition", label: "Addition", description: "Learn basic addition", icon: "+"},
        {id: "calculus", label: "Calculus", description: "The subject right after addition, a sort of review", icon: "Ω"}
    ];
    const welcomeScreen = document.querySelector("#welcome-screen");
    const topicsScreen = document.querySelector("#topics-screen");
    const form = document.querySelector("#welcome-form");
    const usernameInput = document.querySelector("#username");
    const usernameError = document.querySelector("#username-error");
    const continueBtn = document.querySelector("#continue-btn");
    const topicsGrid = document.querySelector("#topics-grid");
    const backBtn = document.querySelector("#back-btn");
    const startBtn = document.querySelector("#start-btn");
    const startStatus = document.querySelector("#start-status");

    let selectedTopic = null;

    function setStep(step) {
        if (step == "welcome") {
            welcomeScreen.classList.add("active");
            topicsScreen.classList.remove("active");
            usernameInput.focus();
        } else {
            welcomeScreen.classList.remove("active");
            topicsScreen.classList.add("active");
            const firstCard = topicsGrid.querySelector(".topic-card")
            if (firstCard) {
                firstCard.focus()
            }
        }
    }

    form.addEventListener("input", () => {
        const val = usernameInput.value.trim();
        const valid = val.length > 0;
        continueBtn.disabled = !valid;
        usernameError.textContent = valid ? "" : "Please enter your name.";
    })
}
)