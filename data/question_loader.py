# data/question_loader.py
import json
import random

class QuestionLoader:
    def __init__(self, json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            self.questions = json.load(f)

    def get_question(self, domain, difficulty):
        """
        Fetch a single question matching domain & difficulty
        """
        filtered = [
            q for q in self.questions
            if q["Domain"].lower() == domain.lower()
            and int(q["Difficulty"]) == int(difficulty)
        ]

        if not filtered:
            # fallback: any question from the domain
            filtered = [q for q in self.questions if q["Domain"].lower() == domain.lower()]

        if not filtered:
            return None

        return random.choice(filtered)

    def get_questions_by_domain(self, domain):
        """
        Fetch all questions of a domain (for explainability / summaries)
        """
        return [q for q in self.questions if q["Domain"].lower() == domain.lower()]
