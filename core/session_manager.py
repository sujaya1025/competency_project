import time

from agents.student_profile_agent import StudentProfileAgent
from agents.difficulty_adaptation_agent import DifficultyAdaptationAgent
from agents.competency_agent import CompetencyAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.aptitude_agent import AptitudeAgent
from agents.reasoning_agent import ReasoningAgent
from agents.verbal_agent import VerbalAgent

from data.question_loader import QuestionLoader
from db.db_manager import DBManager
from explainability_agent import ExplainabilityAgent


SESSION_DURATION = 3600
DOMAINS = ["aptitude", "reasoning", "verbal"]


class SessionManager:
    def __init__(self):
        print("=== Adaptive Competency Assessment Started ===")
        self.student_id = input("Enter Student ID: ").strip()

        self.db_manager = DBManager()
        self.question_loader = QuestionLoader("data/questions.json")

        self.student_profile = StudentProfileAgent(student_id=self.student_id, db_manager=self.db_manager)
        self.student_profile.reset_session_metrics()

        self.difficulty_agent = DifficultyAdaptationAgent()
        self.competency_agent = CompetencyAgent(self.student_profile)
        self.coordinator = CoordinatorAgent()

        self.agents = {
            "aptitude": AptitudeAgent(self.question_loader, self.student_profile, self.difficulty_agent, self.competency_agent),
            "reasoning": ReasoningAgent(self.question_loader, self.student_profile, self.difficulty_agent, self.competency_agent),
            "verbal": VerbalAgent(self.question_loader, self.student_profile, self.difficulty_agent, self.competency_agent),
        }
        self.explain_agent = ExplainabilityAgent()

    def start_session(self):
        session_start = time.time()

        for domain in DOMAINS:
            self.agents[domain].conduct_assessment(
                num_questions=15,
                session_start_time=session_start,
                session_duration=SESSION_DURATION,
            )

        session_results = {}
        total_attempted = 0

        for domain in DOMAINS:
            summary = self.competency_agent.compute_domain_session_metrics(domain)
            if not summary:
                continue

            total_attempted += summary["attempted"]
            next_difficulty = self.difficulty_agent.decide_next_difficulty(
                learning_index=summary["li"],
                current_difficulty=summary["difficulty_used"],
            )
            summary["difficulty_next"] = next_difficulty
            session_results[domain] = summary
            self.coordinator.collect_report(summary)
            self.student_profile.apply_session_outcome(
                domain=domain,
                li=summary["li"],
                trend=summary["trend"],
                ci_new=summary["ci"],
                next_difficulty=next_difficulty,
            )

        if total_attempted == 0:
            print("\n[Info] No questions attempted")
            return

        overall_ci = self.student_profile.get_overall_ci()
        session_id = self.db_manager.create_session(self.student_id, overall_ci)

        for domain, summary in session_results.items():
            self.db_manager.save_session_result(
                session_id=session_id,
                student_id=self.student_id,
                domain=domain,
                li=summary["li"],
                trend=summary["trend"],
                ci=summary["ci"],
                difficulty_used=summary["difficulty_used"],
                difficulty_next=summary["difficulty_next"],
                attempted=summary["attempted"],
                avg_time=summary["avg_time"],
            )

            state = self.student_profile.get_domain_state(domain)
            for log in state["session_logs"]:
                self.db_manager.save_question_log(
                    session_id=session_id,
                    student_id=self.student_id,
                    domain=domain,
                    question_id=log["question_id"],
                    correctness=log["correctness"],
                    time_taken=log["time_taken"],
                    ps_i=log["ps_i"],
                    behavior_flag=log["behavior_flag"],
                )

        self.db_manager.update_student_profile(
            self.student_id,
            ci_by_domain={d: self.student_profile.domains[d]["ci"] for d in DOMAINS},
            ci_overall=overall_ci,
            difficulty_by_domain={d: self.student_profile.domains[d]["current_difficulty"] for d in DOMAINS},
        )

        print("\n=== Session Results ===")
        for domain in DOMAINS:
            if domain not in session_results:
                continue
            s = session_results[domain]
            print(
                f"{domain.capitalize()}: LI={s['li']:.3f}, Trend={s['trend']:+.3f}, "
                f"CI={s['ci']:.3f}, Diff {s['difficulty_used']}->{s['difficulty_next']}"
            )
        print(f"Overall CI: {overall_ci:.3f}")
