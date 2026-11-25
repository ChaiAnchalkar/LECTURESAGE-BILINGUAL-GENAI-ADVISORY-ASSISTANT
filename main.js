// LectureSage Frontend Application Logic

let currentFlashcards = [];
let currentCardIndex = 0;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  fetchStatus();
  initChat();
  initFlashcards();
  initQuiz();
  initSidebar();
  initConfigModal();
});

// --- Tab Switching ---
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");

      tabBtns.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(target)?.classList.add("active");

      // Auto-load flashcards when switching to flashcards tab if empty
      if (target === "tab-flashcards" && currentFlashcards.length === 0) {
        loadFlashcards();
      }
    });
  });
}

// --- Status & Document Ingestion ---
async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    document.getElementById("totalSlides").textContent = data.total_slides || 0;
    const sources = data.sources || [];
    document.getElementById("sourceName").textContent = sources.length > 0 ? sources.join(", ") : "None";
    document.getElementById("llmEngine").textContent = data.llm_provider || "Simulator";
  } catch (err) {
    console.error("Failed to fetch status:", err);
  }
}

function initSidebar() {
  const btnLoadSample = document.getElementById("btnLoadSample");
  const fileUpload = document.getElementById("fileUpload");
  const uploadHint = document.getElementById("uploadHint");

  btnLoadSample.addEventListener("click", async () => {
    btnLoadSample.disabled = true;
    btnLoadSample.textContent = "Loading CS 101...";
    try {
      const res = await fetch("/api/load-sample", { method: "POST" });
      const data = await res.json();
      alert(data.message || "Loaded CS 101 sample course!");
      await fetchStatus();
      loadFlashcards();
    } catch (err) {
      alert("Failed to load sample course: " + err);
    } finally {
      btnLoadSample.disabled = false;
      btnLoadSample.innerHTML = "<span>⚡</span> Load CS 101 Sample Deck";
    }
  });

  fileUpload.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    uploadHint.textContent = `Uploading ${file.name}...`;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        alert(data.message);
        await fetchStatus();
        loadFlashcards();
      } else {
        alert("Upload error: " + (data.error || "Unknown"));
      }
    } catch (err) {
      alert("Upload failed: " + err);
    } finally {
      uploadHint.textContent = "Supports lecture slides and notes";
      fileUpload.value = "";
    }
  });
}

// --- Chat & Grounded Q&A ---
function initChat() {
  const chatForm = document.getElementById("chatForm");
  const queryInput = document.getElementById("queryInput");
  const chatFeed = document.getElementById("chatFeed");

  // Quick chip buttons
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      queryInput.value = chip.getAttribute("data-prompt");
      chatForm.dispatchEvent(new Event("submit"));
    });
  });

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    const mode = document.querySelector('input[name="qa-mode"]:checked').value;

    // Append user message
    appendMessage("user", query);
    queryInput.value = "";

    // Append loading placeholder
    const loadingCard = appendMessage("system", "<em>Searching lecture slides and verifying citations...</em>");

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, mode, top_k: 3 })
      });
      const data = await res.json();

      loadingCard.remove();

      let formattedText = formatMarkdown(data.answer);
      let citationsHtml = "";

      if (data.citations && data.citations.length > 0) {
        citationsHtml = `<div class="citations-panel"><strong>Verified Citations:</strong><div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-top:0.3rem;">`;
        data.citations.forEach(c => {
          citationsHtml += `<span class="citation-pill">📌 Slide ${c.slide_num}: ${c.title} (${Math.round((c.score || 0)*100)}% match)</span>`;
        });
        citationsHtml += `</div></div>`;
      }

      appendMessage("system", formattedText + citationsHtml);
    } catch (err) {
      loadingCard.remove();
      appendMessage("system", `<span style="color:#ef4444;">Error processing request: ${err.message}</span>`);
    }

    chatFeed.scrollTop = chatFeed.scrollHeight;
  });
}

function appendMessage(sender, htmlContent) {
  const chatFeed = document.getElementById("chatFeed");
  const card = document.createElement("div");
  card.className = `message-card ${sender}`;

  const avatar = sender === "user" ? "🧑‍🎓" : "🤖";
  card.innerHTML = `
    <div class="avatar">${avatar}</div>
    <div class="bubble">${htmlContent}</div>
  `;
  chatFeed.appendChild(card);
  chatFeed.scrollTop = chatFeed.scrollHeight;
  return card;
}

function formatMarkdown(text) {
  if (!text) return "";
  let formatted = text
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/^• (.*?)(?=<br>|$)/gm, "• $1");
  return formatted;
}

// --- Flashcard Component ---
function initFlashcards() {
  const flipCard = document.getElementById("flipCard");
  const btnPrev = document.getElementById("btnPrevCard");
  const btnNext = document.getElementById("btnNextCard");
  const btnGenCards = document.getElementById("btnGenCards");

  flipCard.addEventListener("click", () => {
    flipCard.classList.toggle("flipped");
  });

  btnPrev.addEventListener("click", () => {
    if (currentCardIndex > 0) {
      currentCardIndex--;
      renderFlashcard();
    }
  });

  btnNext.addEventListener("click", () => {
    if (currentCardIndex < currentFlashcards.length - 1) {
      currentCardIndex++;
      renderFlashcard();
    }
  });

  btnGenCards.addEventListener("click", () => {
    loadFlashcards();
  });
}

async function loadFlashcards() {
  const flipCard = document.getElementById("flipCard");
  flipCard.classList.remove("flipped");
  document.getElementById("cardFrontText").textContent = "Generating flashcards from course slides...";

  try {
    const res = await fetch("/api/flashcards", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count: 5 })
    });
    const data = await res.json();
    if (data.flashcards && data.flashcards.length > 0) {
      currentFlashcards = data.flashcards;
      currentCardIndex = 0;
      renderFlashcard();
    } else {
      document.getElementById("cardFrontText").textContent = "No slides indexed. Please upload materials.";
    }
  } catch (err) {
    console.error("Flashcard generation error:", err);
  }
}

function renderFlashcard() {
  const flipCard = document.getElementById("flipCard");
  flipCard.classList.remove("flipped");

  if (currentFlashcards.length === 0) return;

  const card = currentFlashcards[currentCardIndex];
  document.getElementById("cardFrontText").textContent = card.front || "No Question";
  document.getElementById("cardBackText").textContent = card.back || "No Answer";
  document.getElementById("cardSlideRef").textContent = card.slide_ref || "Slide Reference";
  document.getElementById("cardSlideRefBack").textContent = card.slide_ref || "Slide Reference";
  document.getElementById("cardDifficulty").textContent = card.difficulty || "Medium";
  document.getElementById("cardCounter").textContent = `${currentCardIndex + 1} / ${currentFlashcards.length}`;
}

// --- Socratic "Grill Me" Quizzer ---
function initQuiz() {
  const btnSubmitQuiz = document.getElementById("btnSubmitQuiz");
  const studentAnswerInput = document.getElementById("studentAnswerInput");
  const evalCard = document.getElementById("evaluationCard");

  btnSubmitQuiz.addEventListener("click", async () => {
    const answer = studentAnswerInput.value.trim();
    if (!answer) {
      alert("Please enter your answer before evaluating.");
      return;
    }

    btnSubmitQuiz.disabled = true;
    btnSubmitQuiz.textContent = "Grading with Rubric...";

    const question = document.getElementById("quizQuestionText").textContent;

    try {
      const res = await fetch("/api/quiz/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, student_answer: answer })
      });
      const evalData = await res.json();

      document.getElementById("evalScore").textContent = evalData.score ?? 3;
      document.getElementById("evalVerdict").textContent = evalData.verdict || "Assessment Complete";
      document.getElementById("evalReference").textContent = "Graded against " + (evalData.reference_slide || "Course Slides");

      const strengthsList = document.getElementById("evalStrengths");
      strengthsList.innerHTML = "";
      (evalData.strengths || ["Accurately identified general intuition."]).forEach(s => {
        const li = document.createElement("li");
        li.textContent = s;
        strengthsList.appendChild(li);
      });

      const improveList = document.getElementById("evalImprovements");
      improveList.innerHTML = "";
      (evalData.areas_to_improve || ["Review mathematical update step."]).forEach(i => {
        const li = document.createElement("li");
        li.textContent = i;
        improveList.appendChild(li);
      });

      evalCard.classList.remove("hidden");
      evalCard.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      alert("Evaluation failed: " + err);
    } finally {
      btnSubmitQuiz.disabled = false;
      btnSubmitQuiz.textContent = "Evaluate with Rubric";
    }
  });
}

// --- Configuration Modal ---
function initConfigModal() {
  const modal = document.getElementById("configModal");
  const btnOpen = document.getElementById("btnOpenConfig");
  const btnClose = document.getElementById("btnCloseConfig");
  const btnCancel = document.getElementById("btnCancelConfig");
  const btnSave = document.getElementById("btnSaveConfig");
  const providerSelect = document.getElementById("apiProviderSelect");
  const apiKeyInput = document.getElementById("apiKeyInput");

  btnOpen.addEventListener("click", () => modal.classList.remove("hidden"));
  btnClose.addEventListener("click", () => modal.classList.add("hidden"));
  btnCancel.addEventListener("click", () => modal.classList.add("hidden"));

  btnSave.addEventListener("click", async () => {
    const provider = providerSelect.value;
    const key = apiKeyInput.value.trim();

    try {
      const res = await fetch("/api/set-api-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, key })
      });
      const data = await res.json();
      alert(data.message);
      await fetchStatus();
      modal.classList.add("hidden");
    } catch (err) {
      alert("Failed to save key: " + err);
    }
  });
}
