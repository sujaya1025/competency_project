import os
from groq import Groq


class ExplainabilityAgent:
    def __init__(self, api_key=None, model="llama-3.1-8b-instant"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = model

    def build_explainability_prompt(self, domain_reports):
        lines = ["Student Deterministic Competency Summary (Current Session Only)", ""]
        for domain, data in domain_reports.items():
            attempted = int(data.get("attempted", 0) or 0)
            if attempted <= 0:
                continue

            lines.extend(
                [
                    f"{domain.capitalize()}:",
                    f"- Learning Index (LI): {float(data.get('li', 0.0)):.3f}",
                    f"- Trend: {float(data.get('trend', 0.0)):+.3f}",
                    f"- Competency Index (CI): {float(data.get('ci', 0.0)):.3f}",
                    f"- Questions Attempted: {attempted}",
                    f"- Accuracy: {float(data.get('accuracy', 0.0)):.1f}%",
                    f"- Average Time: {float(data.get('avg_time', 0.0)):.2f} seconds",
                    f"- Difficulty: {int(data.get('difficulty_used', 1))} -> {int(data.get('difficulty_next', 1))}",
                    (
                        "- Behavioral Flags: "
                        f"guessing={int(data.get('behavior_counts', {}).get('guessing', 0))}, "
                        f"overthinking={int(data.get('behavior_counts', {}).get('overthinking', 0))}"
                    ),
                    "",
                ]
            )

        lines.extend(
            [
                "Provide:",
                "1. Strength analysis",
                "2. Weakness analysis",
                "3. Learning recommendations",
                "4. Behavioral insights based on time vs accuracy and behavior flags",
                "5. Overall competency interpretation using LI, Trend and CI",
            ]
        )
        return "\n".join(lines)

    def generate_explanation(self, domain_reports):
        if not isinstance(domain_reports, dict):
            return "No session data available for explanation."

        filtered = {}
        total_attempted = 0
        for domain, data in domain_reports.items():
            attempted = int((data or {}).get("attempted", 0) or 0)
            if attempted <= 0:
                continue
            filtered[domain] = data
            total_attempted += attempted

        if total_attempted == 0:
            return "No session data available for explanation."

        prompt_text = self.build_explainability_prompt(filtered)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert educational psychologist and adaptive assessment analyst. "
                            "Provide precise, professional, structured explanations. "
                            "Use deterministic terms only: Learning Index, Trend, Competency Index, "
                            "difficulty changes, and behavior flags."
                        ),
                    },
                    {"role": "user", "content": prompt_text},
                ],
                temperature=0.4,
                max_tokens=400,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[Error generating explanation: {e}]"
