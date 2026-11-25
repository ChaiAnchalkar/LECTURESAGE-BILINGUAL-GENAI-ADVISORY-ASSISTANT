# 🎓 LectureSage
### Multimodal Course Companion & Socratic Exam Prep Assistant

> **A Generative AI & Large Language Model project for higher education and university learning.**

LectureSage transforms passive lecture slides, syllabi, and academic notes into an active, hallucination-resistant learning environment. It features grounded Q&A with slide citations, automated Anki-ready flashcard decks, and an interactive **Socratic "Grill Me"** exam evaluation mode using LLM-as-a-Judge.

---

## 🌟 Key GenAI Concepts Implemented

1. **Grounded RAG with Explicit Attribution:**
   - Queries retrieve relevant slide chunks via TF-IDF / dense cosine vector similarity.
   - Prevents hallucinations by strictly grounding answers in the course material and citing exact slide numbers (e.g. `[Slide 3]`).

2. **Dual-Mode Prompt Engineering (Factual vs. Socratic):**
   - **Factual Mode:** Delivers concise, comprehensive explanations with verifiable citations.
   - **Socratic Mode:** Withholds direct answers and asks guided questions to build deep conceptual intuition before exams.

3. **Structured Output Enforcement (`JSON Schema`):**
   - Generates high-yield conceptual flashcards formatted in strict JSON, complete with front/back text, difficulty ratings, and slide references.
   - 1-click export to Anki-compatible `.tsv` format.

4. **LLM-as-a-Judge (Rubric-Based Evaluation):**
   - In "Grill Me" mode, students write free-text answers to open-ended exam questions.
   - The LLM grades the student's submission against the lecture notes on a 0–5 point scale, providing itemized strengths and missing concepts.

5. **Multi-Provider LLM Client with Zero-Dependency Simulator:**
   - Seamlessly connects to **Google Gemini API** or **OpenAI API**.
   - Includes an **Intelligent Offline Simulator** so the entire application can be demonstrated and tested offline without requiring any API keys.

---

## 🏗️ Project Architecture

```
lecturesage/
├── app.py                     # Flask web server & REST API
├── requirements.txt           # Dependencies
├── .env.example               # Environment template
├── README.md                  # Project documentation
│
├── backend/
│   ├── __init__.py
│   ├── document_loader.py     # Parses slides (.pdf, .txt, .md) and preserves slide boundaries
│   ├── vector_engine.py       # High-performance in-memory vector & hybrid retrieval
│   ├── llm_service.py         # Gemini / OpenAI REST client + Offline simulation engine
│   └── socratic_engine.py     # RAG prompt workflows, flashcard synthesis & rubric grading
│
├── sample_data/
│   └── cs101_machine_learning_fundamentals.txt # 8-slide realistic sample course deck
│
├── templates/
│   └── index.html             # Single-page web UI (Tabs for Q&A, Flashcards, Quizzer)
│
└── static/
    ├── css/style.css          # Modern dark/slate theme with 3D flip card animations
    └── js/main.js             # Client logic for chat, card flipping & quiz evaluation
```

---

## 🚀 Quick Start (Running Locally)

### 1. Requirements
* Python 3.10+
* Required libraries: `flask`, `scikit-learn`, `numpy`, `python-dotenv`

### 2. Launch the Application
```bash
# Navigate to the project folder
cd C:\Users\chait\.gemini\antigravity\scratch\lecturesage

# Start the Flask server
python app.py
```

### 3. Open in Browser
Visit **`http://127.0.0.1:5000`** in your browser.
* The sample **CS 101 Machine Learning** slide deck is loaded automatically.
* Click any quick prompt (e.g. *"Difference between Supervised vs Unsupervised?"*) to see grounded slide citations.
* Flip to the **Socratic Flashcards** tab to test concept retention and export to Anki.
* Try the **"Grill Me" Exam Prep** tab to receive rubric feedback on your explanations.

---

## 🔑 Adding Live LLM API Keys (Optional)

LectureSage runs in offline simulation mode by default. To connect live Gemini or OpenAI models:

1. Click **"⚙️ Configure API Key"** in the sidebar, or
2. Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   # OR
   OPENAI_API_KEY=your_openai_api_key_here
   ```

---

## 🎯 Societal & University Impact

* **Combats Advisor & TA Fatigue:** Frees professors and teaching assistants from answering repetitive syllabus and slide questions.
* **Active Learning vs. Passive Cramming:** Moves students away from passive re-reading toward active recall and Socratic dialogue.
* **Educational Equity:** Provides 24/7 personalized tutoring support to under-resourced students who cannot afford private tutoring.
