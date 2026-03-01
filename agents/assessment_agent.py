import time


class AssessmentAgent:
    def __init__(self, domain, question_loader, student_profile, difficulty_agent, competency_agent):
        self.domain = domain
        self.question_loader = question_loader
        self.student_profile = student_profile
        self.difficulty_agent = difficulty_agent
        self.competency_agent = competency_agent

    def conduct_assessment(self, num_questions, session_start_time, session_duration=3600, student_answers=None):
        for _ in range(num_questions):
            elapsed = time.time() - session_start_time
            if elapsed >= session_duration:
                print(
                    f"\n[Info] Session time limit reached ({int(session_duration/60)} mins). "
                    f"Ending {self.domain} assessment."
                )
                break

            state = self.student_profile.get_domain_state(self.domain)
            fixed_difficulty = state["session_difficulty"]

            question = self.question_loader.get_question(domain=self.domain, difficulty=fixed_difficulty)
            if not question:
                continue

            print(f"\n[{self.domain.upper()}] (Question {state['session_attempted'] + 1})")
            print(question["Question"])
            print(f"A. {question['Option A']}")
            print(f"B. {question['Option B']}")
            print(f"C. {question['Option C']}")
            print(f"D. {question['Option D']}")

            start_time = time.time()
            user_answer = input("Your answer (A/B/C/D): ").strip().upper()
            time_taken = time.time() - start_time

            is_correct = (
                question.get(f"Option {user_answer}") == question["Answer"]
                if user_answer in ["A", "B", "C", "D"]
                else False
            )

            qid = question.get("QuestionID") or question.get("Question", "")[:80]
            scored = self.competency_agent.record_submission(
                domain=self.domain,
                question_id=qid,
                is_correct=is_correct,
                time_taken=time_taken,
            )

            if student_answers is not None:
                student_answers.append(
                    {
                        "question_id": qid,
                        "answer": user_answer,
                        "is_correct": is_correct,
                        "time_taken": round(time_taken, 3),
                        "ps_i": scored["ps_i"],
                        "behavior_flag": scored["behavior_flag"],
                    }
                )

    def generate_report(self):
        report = self.competency_agent.compute_domain_session_metrics(self.domain)
        return report
