from agents.assessment_agent import AssessmentAgent

class ReasoningAgent(AssessmentAgent):
    def __init__(self, question_loader, student_profile,
                 difficulty_agent, competency_agent):
        super().__init__(
            domain="reasoning",
            question_loader=question_loader,
            student_profile=student_profile,
            difficulty_agent=difficulty_agent,
            competency_agent=competency_agent
        )
