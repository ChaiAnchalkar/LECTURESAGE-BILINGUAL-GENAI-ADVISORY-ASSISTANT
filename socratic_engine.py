import json
import re
from typing import List, Dict, Any
from backend.llm_service import LLMService

class SocraticEngine:
    """
    Core reasoning engine for LectureSage:
    - Grounded Q&A with strict slide citations
    - Socratic guided dialogue
    - Structured Flashcard & Quiz synthesis
    - Rubric-based answer evaluation (LLM-as-a-Judge)
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def answer_query(self, query: str, context_chunks: List[Dict[str, Any]], mode: str = "direct") -> Dict[str, Any]:
        """
        Answers a student's query using retrieved slide context.
        mode can be 'direct' (factual with citations) or 'socratic' (guiding questions).
        """
        if not context_chunks:
            return {
                "answer": "No relevant lecture slides were found matching your query. Please upload lecture notes or refine your search terms.",
                "citations": []
            }

        # Build context block with explicit citation tags
        context_str = ""
        citations = []
        for c in context_chunks:
            slide_tag = f"Slide {c['slide_num']}: {c['title']} ({c['source']})"
            citations.append({
                "slide_num": c["slide_num"],
                "title": c["title"],
                "source": c["source"],
                "score": c.get("relevance_score", 0.0)
            })
            context_str += f"[{slide_tag}]\n{c['text']}\n\n"

        if mode == "socratic":
            system_prompt = (
                "You are LectureSage's Socratic Academic Coach. Your goal is to guide the student toward "
                "understanding the concept themselves rather than simply giving away the direct answer.\n"
                "RULES:\n"
                "1. Ask 1-2 thought-provoking, guiding questions based on the provided lecture slides.\n"
                "2. Reference the relevant Slide numbers (e.g. 'Take a look at Slide 4') as a hint.\n"
                "3. Be encouraging, concise, and academically rigorous."
            )
            prompt = (
                f"COURSE CONTEXT:\n{context_str}\n"
                f"STUDENT QUESTION:\n{query}\n\n"
                "Provide a Socratic guiding response to help the student solve this."
            )
        else:
            system_prompt = (
                "You are LectureSage, an authoritative academic course assistant. "
                "Answer the student's question accurately using ONLY the provided lecture context.\n"
                "RULES:\n"
                "1. Every factual claim MUST cite the corresponding slide number, e.g. [Slide 3].\n"
                "2. If the context doesn't contain the answer, explicitly state that it is not covered in the provided slides.\n"
                "3. Use clear bullet points and bold key terms."
            )
            prompt = (
                f"COURSE CONTEXT:\n{context_str}\n"
                f"STUDENT QUESTION:\n{query}\n\n"
                "Provide a grounded, comprehensive answer with exact slide citations."
            )

        raw_response = self.llm.generate_completion(prompt, system_prompt)
        return {
            "answer": raw_response,
            "citations": citations
        }

    def generate_flashcards(self, context_chunks: List[Dict[str, Any]], count: int = 5) -> List[Dict[str, Any]]:
        """
        Synthesizes a deck of conceptual flashcards based on the provided lecture materials.
        Returns a structured list of cards: [{front, back, slide_ref, difficulty}].
        """
        combined_text = "\n\n".join([f"[Slide {c['slide_num']}: {c['title']}]\n{c['text']}" for c in context_chunks[:10]])

        prompt = f"""
FLASHCARD_GEN: Generate {count} high-yield study flashcards from the lecture text below.
Format your output as a STRICT JSON ARRAY of objects with this schema:
[
  {{
    "front": "Conceptual question testing core principle",
    "back": "Clear, concise, and rigorous answer",
    "slide_ref": "Slide X",
    "difficulty": "Easy" | "Medium" | "Hard"
  }}
]

LECTURE MATERIAL:
{combined_text}

JSON OUTPUT ONLY:
"""
        response = self.llm.generate_completion(prompt, "You are a curriculum specialist who outputs ONLY valid JSON.")
        return self._clean_and_parse_json(response, default_fallback=self.llm._offline_flashcards(""))

    def evaluate_quiz_answer(self, question: str, reference_text: str, student_answer: str) -> Dict[str, Any]:
        """
        LLM-as-a-Judge: Evaluates a student's open-ended response against the lecture reference.
        """
        prompt = f"""
RUBRIC_EVAL: Evaluate the student's answer to the practice exam question using the lecture reference material as ground truth.

QUESTION:
{question}

LECTURE REFERENCE MATERIAL:
{reference_text}

STUDENT ANSWER:
{student_answer}

RUBRIC CRITERIA:
- Correctness of key concepts (0-3 points)
- Completeness and terminology (0-2 points)
Total Score: 0 to 5.

OUTPUT FORMAT: Strict JSON object with:
{{
  "score": 0 to 5 (integer),
  "max_score": 5,
  "verdict": "string summary",
  "strengths": ["bullet 1", "bullet 2"],
  "areas_to_improve": ["bullet 1", "bullet 2"],
  "reference_slide": "slide citation"
}}

JSON OUTPUT ONLY:
"""
        response = self.llm.generate_completion(prompt, "You are an impartial academic grader who outputs ONLY valid JSON.")
        default_obj = {
            "score": 3,
            "max_score": 5,
            "verdict": "Completed with partial accuracy",
            "strengths": ["Demonstrates basic familiarity with the topic."],
            "areas_to_improve": ["Review the specific mathematical update rule or definition."],
            "reference_slide": "Lecture Notes"
        }
        return self._clean_and_parse_json(response, default_fallback=default_obj)

    def _clean_and_parse_json(self, raw_str: str, default_fallback: Any) -> Any:
        """Strips markdown fences and parses JSON safely."""
        try:
            # Strip ```json ... ``` blocks
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw_str.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
            return json.loads(cleaned.strip())
        except Exception as e:
            print(f"JSON parsing error: {e}, using fallback.")
            if isinstance(default_fallback, str):
                try:
                    return json.loads(default_fallback)
                except Exception:
                    return []
            return default_fallback
