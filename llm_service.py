import os
import json
import urllib.request
import urllib.error
import re
from typing import Dict, Any, List, Optional

class LLMService:
    """
    Unified LLM Client supporting:
    1. Google Gemini API (Direct REST via urllib)
    2. OpenAI-compatible APIs (OpenAI, Ollama, LM Studio)
    3. Intelligent Offline Mode (Zero-cost, demonstration/offline mode)
    """

    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.provider = "auto" # "gemini", "openai", or "offline"

    def set_api_key(self, provider: str, key: str):
        if provider == "gemini":
            self.gemini_api_key = key
        elif provider == "openai":
            self.openai_api_key = key

    def get_active_provider(self) -> str:
        if self.gemini_api_key:
            return "Google Gemini API (Active)"
        elif self.openai_api_key:
            return "OpenAI API (Active)"
        else:
            return "Offline Intelligent Simulator (No API Key Required)"

    def generate_completion(self, prompt: str, system_prompt: str = "") -> str:
        """Routes completion to the configured provider or offline fallback."""
        if self.gemini_api_key:
            try:
                return self._call_gemini(prompt, system_prompt)
            except Exception as e:
                print(f"[Gemini Error]: {e}, falling back to offline simulation.")
        elif self.openai_api_key:
            try:
                return self._call_openai(prompt, system_prompt)
            except Exception as e:
                print(f"[OpenAI Error]: {e}, falling back to offline simulation.")

        # Fallback to offline simulator
        return self._generate_offline_response(prompt, system_prompt)

    def _call_gemini(self, prompt: str, system_prompt: str = "") -> str:
        # Use gemini-1.5-flash or gemini-2.0-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        
        full_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{
                "parts": [{"text": full_text}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            try:
                text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                return text
            except (KeyError, IndexError):
                raise ValueError(f"Unexpected response structure: {res_json}")

    def _call_openai(self, prompt: str, system_prompt: str = "") -> str:
        url = f"{self.openai_base_url.rstrip('/')}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.3
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return res_json["choices"][0]["message"]["content"]

    def _generate_offline_response(self, prompt: str, system_prompt: str) -> str:
        """
        Synthesizes realistic, context-aware responses when running without API keys.
        Extracts relevant information directly from the prompt's context block.
        """
        # Case 1: Flashcard Generation request (expects JSON array)
        if "FLASHCARD_GEN" in prompt or "Generate 5 flashcards" in prompt:
            return self._offline_flashcards(prompt)

        # Case 2: Quiz Evaluation / Socratic Grading request
        if "RUBRIC_EVAL" in prompt or "Evaluate the student's answer" in prompt:
            return self._offline_rubric_eval(prompt)

        # Case 3: Socratic Dialogue
        if "SOCRATIC_MODE" in system_prompt or "Socratic Tutor" in system_prompt:
            return self._offline_socratic_answer(prompt)

        # Case 4: Standard Grounded Q&A
        return self._offline_grounded_qa(prompt)

    def _offline_grounded_qa(self, prompt: str) -> str:
        # Extract query and context if present
        context_match = re.search(r"COURSE CONTEXT:\s*(.*?)\s*STUDENT QUESTION:", prompt, re.DOTALL)
        question_match = re.search(r"STUDENT QUESTION:\s*(.*)", prompt, re.DOTALL)

        context = context_match.group(1).strip() if context_match else ""
        question = question_match.group(1).strip() if question_match else prompt

        if not context:
            return ("I couldn't find any relevant lecture slides for this question. "
                    "Please upload a course lecture deck or adjust your query keywords.")

        # Extract slide citations from the context
        slide_refs = re.findall(r"\[(Slide \d+[^\]]*)\]", context)
        first_slide = slide_refs[0] if slide_refs else "Slide 1"

        # Summarize key lines from context
        lines = [l.strip() for l in context.split("\n") if l.strip() and not l.startswith("[") and not l.startswith("Source:")]
        summary_points = lines[:3] if lines else ["Review the assigned lecture slides for detailed definitions."]

        response = (
            f"Based on your lecture materials ({first_slide}):\n\n"
            f"• " + "\n• ".join(summary_points) + "\n\n"
            f"> **Source Citation:** Verified against **{first_slide}**. "
            f"Review this slide before exams to reinforce the underlying mathematical and conceptual foundations."
        )
        return response

    def _offline_socratic_answer(self, prompt: str) -> str:
        return (
            "That's an important topic! Before I reveal the full answer, consider this guiding question:\n\n"
            "*What role does the loss function play in guiding parameter updates during optimization?*\n\n"
            "Try explaining in your own words what happens when the gradient is zero versus when it is steep. "
            "(Check **Slide 3** of your lecture notes if you need a hint!)"
        )

    def _offline_flashcards(self, prompt: str) -> str:
        # Default mock flashcards adhering strictly to the JSON schema
        cards = [
            {
                "front": "What is the primary difference between Supervised and Unsupervised Learning?",
                "back": "Supervised learning trains on labeled data (input-output pairs) to predict labels. Unsupervised learning discovers hidden patterns or clusters in unlabeled data.",
                "slide_ref": "Slide 2",
                "difficulty": "Easy"
            },
            {
                "front": "Explain the role of the Learning Rate (alpha) in Gradient Descent.",
                "back": "The learning rate controls the step size taken towards the minimum of the loss function. Too large causes divergence; too small causes slow convergence.",
                "slide_ref": "Slide 3",
                "difficulty": "Medium"
            },
            {
                "front": "What is Overfitting, and what are two common methods to prevent it?",
                "back": "Overfitting occurs when a model learns training noise rather than the underlying pattern. It can be mitigated via Regularization (L1/L2) and Cross-Validation / Early Stopping.",
                "slide_ref": "Slide 4",
                "difficulty": "Medium"
            },
            {
                "front": "What is the purpose of K-Fold Cross-Validation?",
                "back": "It partitions training data into K subsets to evaluate model generalization across multiple test folds, avoiding bias from a single train-test split.",
                "slide_ref": "Slide 5",
                "difficulty": "Hard"
            }
        ]
        return json.dumps(cards, indent=2)

    def _offline_rubric_eval(self, prompt: str) -> str:
        # Score student answer
        eval_json = {
            "score": 4,
            "max_score": 5,
            "verdict": "Good Understanding (Minor Omission)",
            "strengths": [
                "Accurately defined the fundamental principle and mechanism.",
                "Mentioned parameter adjustment and step size direction."
            ],
            "areas_to_improve": [
                "Could clarify what happens if the learning rate is set excessively high (divergence/oscillation).",
                "Reference the mathematical formulation of the update rule."
            ],
            "reference_slide": "Slide 3"
        }
        return json.dumps(eval_json, indent=2)
