import tkinter as tk
from tkinter import messagebox
from time import time

# Backend imports
from agents.student_profile_agent import StudentProfileAgent
from agents.difficulty_adaptation_agent import DifficultyAdaptationAgent
from agents.competency_agent import CompetencyAgent
from agents.coordinator_agent import CoordinatorAgent

from agents.aptitude_agent import AptitudeAgent
from agents.reasoning_agent import ReasoningAgent
from agents.verbal_agent import VerbalAgent

from data.question_loader import QuestionLoader
from db.db_manager import DBManager

SESSION_DURATION = 3600  # 60 minutes
QUESTIONS_PER_DOMAIN = 15
DOMAINS = ["aptitude", "reasoning", "verbal"]

# ---------------- GUI Class ----------------
class AdaptiveGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Adaptive Competency Assessment")
        self.root.geometry("700x500")

        self.student_id = None
        self.session_start = None
        self.current_domain_index = 0
        self.current_question_index = 0
        self.question_order = []

        # Backend placeholders
        self.db_manager = DBManager()
        self.student_profile = None
        self.difficulty_agent = DifficultyAdaptationAgent()
        self.competency_agent = None
        self.question_loader = QuestionLoader("data/questions.json")
        self.agents = {}

        # GUI elements
        self.setup_start_frame()

    # ---------- Initial Frame ----------
    def setup_start_frame(self):
        self.start_frame = tk.Frame(self.root)
        self.start_frame.pack(fill="both", expand=True)

        tk.Label(self.start_frame, text="Enter Student ID:", font=("Arial", 14)).pack(pady=20)
        self.id_entry = tk.Entry(self.start_frame, font=("Arial", 14))
        self.id_entry.pack(pady=10)

        tk.Button(self.start_frame, text="Start Session", font=("Arial", 14),
                  command=self.start_session).pack(pady=20)

    # ---------- Start Session ----------
    def start_session(self):
        self.student_id = self.id_entry.get().strip()
        if not self.student_id:
            messagebox.showerror("Error", "Please enter a valid Student ID.")
            return

        # Initialize backend
        self.student_profile = StudentProfileAgent(student_id=self.student_id, db_manager=self.db_manager)
        self.competency_agent = CompetencyAgent(self.student_profile)

        # Domain agents
        self.agents = {
            "aptitude": AptitudeAgent(self.question_loader, self.student_profile,
                                      self.difficulty_agent, self.competency_agent),
            "reasoning": ReasoningAgent(self.question_loader, self.student_profile,
                                        self.difficulty_agent, self.competency_agent),
            "verbal": VerbalAgent(self.question_loader, self.student_profile,
                                  self.difficulty_agent, self.competency_agent)
        }

        # Setup question order
        self.question_order = []
        for domain in DOMAINS:
            self.question_order += [domain] * QUESTIONS_PER_DOMAIN
        self.current_question_index = 0
        self.session_start = time()

        self.start_frame.destroy()
        self.setup_question_frame()
        self.show_next_question()
        self.update_timer()

    # ---------- Question Frame ----------
    def setup_question_frame(self):
        self.q_frame = tk.Frame(self.root)
        self.q_frame.pack(fill="both", expand=True)

        self.timer_label = tk.Label(self.q_frame, text="Time left: 60:00", font=("Arial", 14))
        self.timer_label.pack(pady=10)

        self.q_label = tk.Label(self.q_frame, text="", font=("Arial", 14), wraplength=650, justify="left")
        self.q_label.pack(pady=20)

        self.selected_answer = tk.StringVar()
        self.radio_buttons = []
        for opt in ["A", "B", "C", "D"]:
            rb = tk.Radiobutton(self.q_frame, text="", variable=self.selected_answer, value=opt, font=("Arial", 12))
            rb.pack(anchor="w", padx=50)
            self.radio_buttons.append(rb)

        self.submit_btn = tk.Button(self.q_frame, text="Submit", font=("Arial", 14), command=self.submit_answer)
        self.submit_btn.pack(pady=20)

    # ---------- Show Next Question ----------
    def show_next_question(self):
        if self.current_question_index >= len(self.question_order):
            self.end_session()
            return

        domain = self.question_order[self.current_question_index]
        agent = self.agents[domain]

        # Check session time
        elapsed = time() - self.session_start
        if elapsed >= SESSION_DURATION:
            messagebox.showinfo("Time Up", "Session time limit reached.")
            self.end_session()
            return

        state = self.student_profile.get_domain_state(domain)
        difficulty = state["current_difficulty"]
        question = self.question_loader.get_question(domain, difficulty)
        if not question:
            self.current_question_index += 1
            self.show_next_question()
            return

        self.current_domain = domain
        self.current_question = question
        self.q_start_time = time()

        self.q_label.config(text=f"[{domain.upper()}] {question['Question']}")
        for i, opt in enumerate(["A", "B", "C", "D"]):
            self.radio_buttons[i].config(text=f"{opt}. {question[f'Option {opt}']}")
        self.selected_answer.set(None)

    # ---------- Submit Answer ----------
    def submit_answer(self):
        if not self.selected_answer.get():
            messagebox.showwarning("Warning", "Please select an answer.")
            return

        # Calculate time taken
        time_taken = time() - self.q_start_time
        # Check correctness
        user_answer = self.selected_answer.get()
        is_correct = (self.current_question.get(f"Option {user_answer}") == self.current_question["Answer"])

        self.student_profile.increment_attempt(
            domain=self.current_domain,
            is_correct=is_correct,
            response_time=time_taken,
        )

        # Update competency μ–σ
        self.competency_agent.update_belief(
            domain=self.current_domain,
            is_correct=is_correct,
            difficulty=self.student_profile.get_domain_state(self.current_domain)["current_difficulty"],
            time_taken=time_taken
        )

        # Update next difficulty
        updated_state = self.student_profile.get_domain_state(self.current_domain)
        new_diff = self.difficulty_agent.decide_next_difficulty(
            mu=updated_state["mu"],
            sigma=updated_state["sigma"],
            current_difficulty=updated_state["current_difficulty"]
        )
        self.student_profile.update_difficulty(self.current_domain, new_diff)

        # Move to next question
        self.current_question_index += 1
        self.show_next_question()

    # ---------- Timer ----------
    def update_timer(self):
        if not hasattr(self, 'timer_label') or not self.timer_label.winfo_exists():
            return  # stop timer if label destroyed

        elapsed = time() - self.session_start
        remaining = max(0, SESSION_DURATION - elapsed)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        self.timer_label.config(text=f"Time left: {mins:02d}:{secs:02d}")

        if remaining > 0:
            self.root.after(1000, self.update_timer)
        else:
            messagebox.showinfo("Time Up", "Session time limit reached.")
            self.end_session()

    # ---------- End Session ----------
    def end_session(self):
        if hasattr(self, 'q_frame') and self.q_frame.winfo_exists():
            self.q_frame.destroy()  # safely destroy frame

        # Inter-agent negotiation
        coordinator = CoordinatorAgent()
        for domain in DOMAINS:
            coordinator.collect_report(self.agents[domain].generate_report())

        global_bias = coordinator.negotiate()
        for domain in DOMAINS:
            state = self.student_profile.get_domain_state(domain)
            new_diff = max(1, min(3, state["current_difficulty"] + global_bias))
            self.student_profile.update_difficulty(domain, new_diff)

        # Save to DB (skip domains with zero attempts)
        total_attempted = 0
        for domain in DOMAINS:
            state = self.student_profile.get_domain_state(domain)
            sessions = state["attempted_questions"]
            if sessions == 0:
                continue
            total_attempted += sessions
            avg_time = state["avg_time"]
            self.db_manager.save_domain(
                self.student_id,
                domain,
                state["mu"],
                state["sigma"],
                sessions,
                avg_time
            )

        if total_attempted == 0:
            messagebox.showinfo("No questions attempted", "No questions attempted")
            return

        # Show competency report
        report_frame = tk.Frame(self.root)
        report_frame.pack(fill="both", expand=True)

        tk.Label(report_frame, text="=== Competency Report (μ–σ) ===", font=("Arial", 14)).pack(pady=10)
        for domain in DOMAINS:
            comp = self.competency_agent.get_domain_competency(domain)
            tk.Label(report_frame, text=f"{domain.capitalize()}: μ={comp['mu']} , σ={comp['sigma']}", font=("Arial", 12)).pack()

        overall = self.competency_agent.get_overall_competency()
        tk.Label(report_frame, text=f"\nOverall Competency → μ={overall['mu']} , σ={overall['sigma']}", font=("Arial", 12)).pack(pady=10)
        tk.Label(report_frame, text=f"[Coordinator] Global Difficulty Bias = {global_bias}", font=("Arial", 12)).pack(pady=10)
        tk.Label(report_frame, text="[Info] Student competency saved to database.", font=("Arial", 12)).pack(pady=10)


# ---------- Run GUI ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = AdaptiveGUI(root)
    root.mainloop()
