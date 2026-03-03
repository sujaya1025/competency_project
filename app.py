
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from time import time

from agents.aptitude_agent import AptitudeAgent
from agents.competency_agent import CompetencyAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.difficulty_adaptation_agent import DifficultyAdaptationAgent
from agents.reasoning_agent import ReasoningAgent
from agents.student_profile_agent import StudentProfileAgent
from agents.verbal_agent import VerbalAgent
from data.question_loader import QuestionLoader
from db.db_manager import DBManager
from explainability_agent import ExplainabilityAgent

SESSION_DURATION = 3600
QUESTIONS_PER_DOMAIN = 15
DOMAINS = ["aptitude", "reasoning", "verbal"]

FONT_FAMILY = "Arial"
BG_COLOR = "#f4f6fb"
CARD_BG = "#ffffff"
CARD_BORDER = "#d4dbe7"
ACCENT = "#1f4e79"
ACTIVE_TAB_BG = "#d8e9ff"


class DBManagerAdapter:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def load_domain(self, student_id, domain_name):
        return self.db_manager.load_domain(student_id, domain_name)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Adaptive Competency Assessment")
        self.geometry("1080x720")
        self.configure(bg=BG_COLOR)

        self.db_manager = DBManager()
        self.profile_db_adapter = DBManagerAdapter(self.db_manager)
        self.current_student_id = None
        self.current_student_name = None

        container = tk.Frame(self, bg=BG_COLOR)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for frame_class in (
            LoginFrame,
            SignupFrame,
            DashboardFrame,
            AssessmentFrame,
            ResultsFrame,
            ExplainabilityFrame,
        ):
            frame = frame_class(parent=container, controller=self)
            self.frames[frame_class] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_frame(LoginFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

    def on_close(self):
        try:
            self.db_manager.close()
        finally:
            self.destroy()


class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        tk.Label(self, text="Login", font=(FONT_FAMILY, 24, "bold"), bg=BG_COLOR, fg=ACCENT).pack(pady=24)

        card = tk.Frame(self, bg=CARD_BG, bd=1, relief="solid", highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(pady=8, ipadx=20, ipady=20)

        form = tk.Frame(card, bg=CARD_BG)
        form.pack(padx=20, pady=8)

        tk.Label(form, text="Email", font=(FONT_FAMILY, 12), bg=CARD_BG).grid(row=0, column=0, sticky="w", pady=8, padx=8)
        self.email_entry = tk.Entry(form, width=35, font=(FONT_FAMILY, 12))
        self.email_entry.grid(row=0, column=1, pady=8, padx=8)

        tk.Label(form, text="Password", font=(FONT_FAMILY, 12), bg=CARD_BG).grid(row=1, column=0, sticky="w", pady=8, padx=8)
        self.password_entry = tk.Entry(form, width=35, show="*", font=(FONT_FAMILY, 12))
        self.password_entry.grid(row=1, column=1, pady=8, padx=8)

        tk.Button(card, text="Login", width=18, font=(FONT_FAMILY, 12), command=self.handle_login, bg=ACCENT, fg="white").pack(pady=10)
        tk.Button(
            card,
            text="Go to Signup",
            width=18,
            font=(FONT_FAMILY, 12),
            command=lambda: controller.show_frame(SignupFrame),
        ).pack(pady=4)

    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            messagebox.showerror("Error", "Please enter email and password.")
            return

        student_id = self.controller.db_manager.authenticate_student(email, password)
        if not student_id:
            messagebox.showerror("Login Failed", "Invalid email or password.")
            return

        self.controller.current_student_id = student_id
        student_info = self.controller.db_manager.get_student_info(student_id)
        self.controller.current_student_name = student_info[0] if student_info else None

        self.password_entry.delete(0, tk.END)
        self.controller.show_frame(DashboardFrame)


class SignupFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        tk.Label(self, text="Create Account", font=(FONT_FAMILY, 24, "bold"), bg=BG_COLOR, fg=ACCENT).pack(pady=24)

        card = tk.Frame(self, bg=CARD_BG, bd=1, relief="solid", highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(pady=8, ipadx=20, ipady=20)

        form = tk.Frame(card, bg=CARD_BG)
        form.pack(padx=20, pady=8)

        tk.Label(form, text="Student ID", font=(FONT_FAMILY, 12), bg=CARD_BG).grid(row=0, column=0, sticky="w", pady=8, padx=8)
        self.student_id_entry = tk.Entry(form, width=35, font=(FONT_FAMILY, 12))
        self.student_id_entry.grid(row=0, column=1, pady=8, padx=8)

        tk.Label(form, text="Name", font=(FONT_FAMILY, 12), bg=CARD_BG).grid(row=1, column=0, sticky="w", pady=8, padx=8)
        self.name_entry = tk.Entry(form, width=35, font=(FONT_FAMILY, 12))
        self.name_entry.grid(row=1, column=1, pady=8, padx=8)

        tk.Label(form, text="Email", font=(FONT_FAMILY, 12), bg=CARD_BG).grid(row=2, column=0, sticky="w", pady=8, padx=8)
        self.email_entry = tk.Entry(form, width=35, font=(FONT_FAMILY, 12))
        self.email_entry.grid(row=2, column=1, pady=8, padx=8)

        tk.Label(form, text="Password", font=(FONT_FAMILY, 12), bg=CARD_BG).grid(row=3, column=0, sticky="w", pady=8, padx=8)
        self.password_entry = tk.Entry(form, width=35, show="*", font=(FONT_FAMILY, 12))
        self.password_entry.grid(row=3, column=1, pady=8, padx=8)

        tk.Button(card, text="Create Account", width=18, font=(FONT_FAMILY, 12), command=self.handle_signup, bg=ACCENT, fg="white").pack(pady=10)
        tk.Button(
            card,
            text="Back to Login",
            width=18,
            font=(FONT_FAMILY, 12),
            command=lambda: controller.show_frame(LoginFrame),
        ).pack(pady=4)

    def handle_signup(self):
        student_id = self.student_id_entry.get().strip()
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not all([student_id, name, email, password]):
            messagebox.showerror("Error", "All fields are required.")
            return

        created = self.controller.db_manager.create_student(student_id, name, email, password)
        if not created:
            messagebox.showerror("Signup Failed", "Student ID or email already exists.")
            return

        messagebox.showinfo("Success", "Account created successfully. Please login.")
        self.clear_form()
        self.controller.show_frame(LoginFrame)

    def clear_form(self):
        self.student_id_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        wrapper = tk.Frame(self, bg=BG_COLOR)
        wrapper.pack(fill="both", expand=True, padx=30, pady=24)

        self.welcome_label = tk.Label(wrapper, text="Welcome", font=(FONT_FAMILY, 22, "bold"), bg=BG_COLOR, fg=ACCENT)
        self.welcome_label.pack(anchor="w", pady=(0, 14))

        top_row = tk.Frame(wrapper, bg=BG_COLOR)
        top_row.pack(fill="x", pady=(0, 14))

        start_card = tk.Frame(top_row, bg=CARD_BG, bd=1, relief="solid", highlightbackground=CARD_BORDER, highlightthickness=1)
        start_card.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=8)

        tk.Label(start_card, text="Assessment", font=(FONT_FAMILY, 14, "bold"), bg=CARD_BG, fg=ACCENT).pack(anchor="w", padx=16, pady=(12, 8))
        tk.Label(start_card, text="Start a new adaptive session.", font=(FONT_FAMILY, 11), bg=CARD_BG).pack(anchor="w", padx=16)
        tk.Button(
            start_card,
            text="Start Assessment",
            width=20,
            font=(FONT_FAMILY, 12),
            command=self.start_assessment,
            bg=ACCENT,
            fg="white",
        ).pack(anchor="w", padx=16, pady=14)

        logout_card = tk.Frame(top_row, bg=CARD_BG, bd=1, relief="solid", highlightbackground=CARD_BORDER, highlightthickness=1)
        logout_card.pack(side="left", fill="y", padx=(8, 0), ipadx=10, ipady=10)
        tk.Label(logout_card, text="Account", font=(FONT_FAMILY, 14, "bold"), bg=CARD_BG, fg=ACCENT).pack(pady=(10, 8))
        tk.Button(logout_card, text="Logout", width=14, font=(FONT_FAMILY, 12), command=self.handle_logout).pack(pady=(0, 8))

        sessions_card = tk.Frame(wrapper, bg=CARD_BG, bd=1, relief="solid", highlightbackground=CARD_BORDER, highlightthickness=1)
        sessions_card.pack(fill="both", expand=True)

        tk.Label(sessions_card, text="Previous Sessions", font=(FONT_FAMILY, 14, "bold"), bg=CARD_BG, fg=ACCENT).pack(anchor="w", padx=16, pady=(12, 8))

        self.sessions_list = tk.Listbox(sessions_card, width=95, height=18, font=("Consolas", 10), bd=0)
        self.sessions_list.pack(padx=16, pady=(0, 16), fill="both", expand=True)

    def on_show(self):
        student_id = self.controller.current_student_id
        if not student_id:
            self.controller.show_frame(LoginFrame)
            return

        student_name = self.controller.current_student_name or "Student"
        self.welcome_label.config(text=f"Welcome, {student_name} ({student_id})")
        self.load_sessions()

    def start_assessment(self):
        student_id = self.controller.current_student_id
        if not student_id:
            messagebox.showerror("Error", "Please login first.")
            self.controller.show_frame(LoginFrame)
            return

        assessment_frame = self.controller.frames[AssessmentFrame]
        assessment_frame.start_assessment(student_id)
        self.controller.show_frame(AssessmentFrame)

    def load_sessions(self):
        self.sessions_list.delete(0, tk.END)

        sessions = self.controller.db_manager.get_student_sessions(self.controller.current_student_id)
        if not sessions:
            self.sessions_list.insert(tk.END, "No previous sessions found.")
            return

        self.sessions_list.insert(tk.END, "Session ID | Date                | Overall CI")
        self.sessions_list.insert(tk.END, "--------------------------------------------------------")

        for session_id, date, overall_ci in sessions:
            ci_text = f"{overall_ci:.3f}" if overall_ci is not None else "N/A"
            line = f"{session_id:<10} | {date:<19} | {ci_text:<10}"
            self.sessions_list.insert(tk.END, line)

    def handle_logout(self):
        self.controller.current_student_id = None
        self.controller.current_student_name = None
        self.controller.show_frame(LoginFrame)


class AssessmentFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        self.student_id = None
        self.session_start = None
        self.timer_job = None
        self.session_active = False
        self.session_ended = False

        self.student_profile = None
        self.difficulty_agent = None
        self.competency_agent = None
        self.question_loader = None
        self.agents = {}

        self.question_order = []
        self.next_question_index = 0
        self.current_question_index = None
        self.question_history = []
        self.session_reports = {}

        self.selected_answer = tk.StringVar(value="")

        wrapper = tk.Frame(self, bg=BG_COLOR)
        wrapper.pack(fill="both", expand=True, padx=24, pady=18)

        header = tk.Frame(wrapper, bg=BG_COLOR)
        header.pack(fill="x", pady=(0, 10))

        tk.Label(header, text="Adaptive Assessment",
                 font=(FONT_FAMILY, 22, "bold"),
                 bg=BG_COLOR, fg=ACCENT).pack(side="left")

        self.timer_label = tk.Label(
            header,
            text="Time left: 60:00",
            font=(FONT_FAMILY, 12, "bold"),
            bg="#edf2ff",
            fg=ACCENT,
            padx=12,
            pady=6,
            relief="solid",
            bd=1,
        )
        self.timer_label.pack(side="right")

        self.progress_label = tk.Label(
            wrapper,
            text="Progress: 0/45",
            font=(FONT_FAMILY, 12, "bold"),
            bg=BG_COLOR
        )
        self.progress_label.pack(anchor="w", pady=(0, 14))

        q_card = tk.Frame(wrapper, bg=CARD_BG, bd=1,
                          relief="solid", highlightbackground=CARD_BORDER,
                          highlightthickness=1)
        q_card.pack(fill="x", padx=90, pady=(0, 16), ipady=16)

        self.q_label = tk.Label(
            q_card,
            text="Click Start Assessment from Dashboard to begin.",
            font=(FONT_FAMILY, 14, "bold"),
            wraplength=760,
            justify="left",
            bg=CARD_BG,
        )
        self.q_label.pack(anchor="w", padx=26, pady=(18, 14))

        self.option_frame = tk.Frame(q_card, bg=CARD_BG)
        self.option_frame.pack(fill="x", padx=26, pady=(0, 8))

        self.radio_buttons = []
        for opt in ["A", "B", "C", "D"]:
            rb = tk.Radiobutton(
                self.option_frame,
                text="",
                variable=self.selected_answer,
                value=opt,
                font=(FONT_FAMILY, 12),
                anchor="w",
                justify="left",
                bg=CARD_BG,
            )
            rb.pack(fill="x", pady=4)
            self.radio_buttons.append(rb)

        nav_frame = tk.Frame(wrapper, bg=BG_COLOR)
        nav_frame.pack(pady=2)

        self.submit_btn = tk.Button(
            nav_frame,
            text="Submit Answer",
            width=18,
            font=(FONT_FAMILY, 12),
            command=self.submit_answer,
            bg=ACCENT,
            fg="white",
        )
        self.submit_btn.grid(row=0, column=0, padx=8)

        self.submit_test_btn = tk.Button(
            nav_frame,
            text="Submit Test",
            width=18,
            font=(FONT_FAMILY, 12),
            command=self.submit_test,
            bg="#aa2e25",
            fg="white",
        )
        self.submit_test_btn.grid(row=0, column=1, padx=8)

    # -------------------------
    # SESSION START
    # -------------------------

    def start_assessment(self, student_id):
        self.student_id = student_id
        self.session_start = time()
        self.session_active = True
        self.session_ended = False

        self.student_profile = StudentProfileAgent(
            student_id=self.student_id,
            db_manager=self.controller.profile_db_adapter,
        )
        self.student_profile.reset_session_metrics()

        self.difficulty_agent = DifficultyAdaptationAgent()
        self.competency_agent = CompetencyAgent(self.student_profile)
        self.question_loader = QuestionLoader("data/questions.json")

        self.agents = {
            "aptitude": AptitudeAgent(self.question_loader, self.student_profile,
                                      self.difficulty_agent, self.competency_agent),
            "reasoning": ReasoningAgent(self.question_loader, self.student_profile,
                                        self.difficulty_agent, self.competency_agent),
            "verbal": VerbalAgent(self.question_loader, self.student_profile,
                                  self.difficulty_agent, self.competency_agent),
        }

        self.question_order = []
        for domain in DOMAINS:
            self.question_order += [domain] * QUESTIONS_PER_DOMAIN

        self.next_question_index = 0
        self.question_history = []
        self.selected_answer.set("")

        self.load_next_question()
        self.update_timer()

    # -------------------------
    # LOAD NEXT QUESTION
    # -------------------------

    def load_next_question(self):
        if not self.session_active:
            return

        if self.next_question_index >= len(self.question_order):
            self.end_assessment("completed")
            return

        elapsed = time() - self.session_start
        if elapsed >= SESSION_DURATION:
            self.end_assessment("timeout")
            return

        domain = self.question_order[self.next_question_index]
        state = self.student_profile.get_domain_state(domain)
        difficulty = state["session_difficulty"]

        question = self.question_loader.get_question(domain, difficulty)
        if not question:
            self.next_question_index += 1
            self.load_next_question()
            return

        self.current_question = {
            "domain": domain,
            "question": question,
            "difficulty": difficulty,
            "start_time": time()
        }

        self.next_question_index += 1
        self.render_question()

    def render_question(self):
        q = self.current_question["question"]
        domain = self.current_question["domain"]
        difficulty = self.current_question["difficulty"]

        self.q_label.config(
            text=f"[{domain.upper()} | Difficulty {difficulty}] {q['Question']}"
        )

        for i, opt in enumerate(["A", "B", "C", "D"]):
            self.radio_buttons[i].config(text=f"{opt}. {q[f'Option {opt}']}")

        self.selected_answer.set("")
        self.progress_label.config(
            text=f"Progress: {self.next_question_index}/{len(self.question_order)}"
        )

    # -------------------------
    # SUBMIT ANSWER
    # -------------------------

    def submit_answer(self):
        if not self.session_active:
            return

        selected = self.selected_answer.get().strip()
        if selected not in ["A", "B", "C", "D"]:
            messagebox.showwarning("Warning", "Please select an answer.")
            return

        record = self.current_question
        question = record["question"]

        time_taken = time() - record["start_time"]
        is_correct = question.get(f"Option {selected}") == question["Answer"]

        self.competency_agent.record_submission(
            domain=record["domain"],
            question_id=question.get("Question", "")[:80],
            is_correct=is_correct,
            time_taken=time_taken,
        )

        self.load_next_question()

    # -------------------------
    # TIMER
    # -------------------------

    def update_timer(self):
        if not self.session_active:
            return

        elapsed = time() - self.session_start
        remaining = max(0, SESSION_DURATION - elapsed)

        mins = int(remaining // 60)
        secs = int(remaining % 60)
        self.timer_label.config(text=f"Time left: {mins:02d}:{secs:02d}")

        if remaining > 0:
            self.timer_job = self.after(1000, self.update_timer)
        else:
            self.end_assessment("timeout")

    # -------------------------
    # END SESSION
    # -------------------------

    def submit_test(self):
        self.end_assessment("manual")

    def end_assessment(self, reason):
        if self.session_ended:
            return

        self.session_active = False
        self.session_ended = True

        messagebox.showinfo("Assessment Complete", "Submitting test...")

        overall_ci = self.student_profile.get_overall_ci()
        session_id = self.controller.db_manager.create_session(
            self.student_id, overall_ci
        )

        self.controller.show_frame(ResultsFrame)
class ResultsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller
        self.results_data = None

        wrapper = tk.Frame(self, bg=BG_COLOR)
        wrapper.pack(fill="both", expand=True, padx=30, pady=22)

        tk.Label(
            wrapper,
            text="Assessment Results",
            font=(FONT_FAMILY, 22, "bold"),
            bg=BG_COLOR,
            fg=ACCENT,
        ).pack(anchor="w", pady=(0, 12))

        card = tk.Frame(
            wrapper,
            bg=CARD_BG,
            bd=1,
            relief="solid",
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True)

        self.overall_label = tk.Label(
            card,
            text="No results available.",
            font=(FONT_FAMILY, 13, "bold"),
            bg=CARD_BG,
            fg=ACCENT,
            justify="left",
        )
        self.overall_label.pack(anchor="w", padx=18, pady=(14, 8))

        self.summary_label = tk.Label(
            card,
            text="",
            font=(FONT_FAMILY, 12),
            bg=CARD_BG,
            justify="left",
        )
        self.summary_label.pack(anchor="w", padx=18, pady=(0, 12))

        table = tk.Frame(card, bg=CARD_BG)
        table.pack(fill="x", padx=18)

        # Updated headers (Removed Trend, Difficulty, Behavior)
        headers = ["Domain", "LI", "CI", "Questions", "Avg Time"]

        for i, head in enumerate(headers):
            lbl = tk.Label(
                table,
                text=head,
                font=(FONT_FAMILY, 12, "bold"),
                bg="#edf2ff",
                relief="solid",
                bd=1,
                padx=8,
                pady=8,
            )
            lbl.grid(row=0, column=i, sticky="nsew")
            table.grid_columnconfigure(i, weight=1)

        self.table_rows = {}

        for row_idx, domain in enumerate(DOMAINS, start=1):
            domain_lbl = tk.Label(
                table,
                text=domain.capitalize(),
                font=(FONT_FAMILY, 11),
                bg=CARD_BG,
                relief="solid",
                bd=1,
                padx=8,
                pady=8,
            )
            domain_lbl.grid(row=row_idx, column=0, sticky="nsew")

            self.table_rows[domain] = []

            # Now only 4 columns after Domain
            for col in range(1, 5):
                cell = tk.Label(
                    table,
                    text="-",
                    font=(FONT_FAMILY, 11),
                    bg=CARD_BG,
                    relief="solid",
                    bd=1,
                    padx=8,
                    pady=8,
                )
                cell.grid(row=row_idx, column=col, sticky="nsew")
                self.table_rows[domain].append(cell)

        btn_row = tk.Frame(card, bg=CARD_BG)
        btn_row.pack(pady=18)

        tk.Button(
            btn_row,
            text="View Explainability",
            width=20,
            font=(FONT_FAMILY, 12),
            command=self.open_explainability,
            bg=ACCENT,
            fg="white",
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            btn_row,
            text="Back to Dashboard",
            width=20,
            font=(FONT_FAMILY, 12),
            command=lambda: controller.show_frame(DashboardFrame),
        ).grid(row=0, column=1, padx=8)

    def set_results(self, results_data):
        self.results_data = results_data
        self.render_results()

    def open_explainability(self):
        explainability_frame = self.controller.frames[ExplainabilityFrame]
        explainability_frame.set_results_data(self.results_data)
        self.controller.show_frame(ExplainabilityFrame)

    def render_results(self):
        if not self.results_data:
            self.overall_label.config(text="No results available.")
            self.summary_label.config(text="")
            return

        overall = self.results_data["overall"]
        coordinator = self.results_data.get("coordinator", {})
        student_id = self.results_data["student_id"]
        session_id = self.results_data["session_id"]

        self.overall_label.config(
            text=(
                f"Student: {student_id}   Session: {session_id}\n"
                f"Overall Competency Index (CI): {overall['ci_overall']:.4f}"
            )
        )

        self.summary_label.config(
            text=(
                f"Domains Attempted: {coordinator.get('domains_attempted', 0)}   "
                f"Avg LI: {coordinator.get('avg_li', 0.0):.3f}   "
                f"Avg Accuracy: {coordinator.get('avg_accuracy', 0.0):.2f}%   "
                f"Avg Time: {coordinator.get('avg_time', 0.0):.2f}s"
            )
        )

        for domain in DOMAINS:
            data = self.results_data["domains"].get(
                domain,
                {
                    "li": 0.0,
                    "ci": 0.0,
                    "attempted": 0,
                    "avg_time": 0.0,
                },
            )

            cells = self.table_rows[domain]

            cells[0].config(text=f"{data['li']:.3f}")
            cells[1].config(text=f"{data['ci']:.3f}")
            cells[2].config(text=f"{data['attempted']}")
            cells[3].config(text=f"{data['avg_time']:.2f}")

class ExplainabilityFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller
        self.results_data = None
        self.explainability_agent = ExplainabilityAgent()

        card = tk.Frame(self, bg=CARD_BG, bd=1, relief="solid", highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(padx=40, pady=40, fill="both", expand=True)

        tk.Label(card, text="Explainability", font=(FONT_FAMILY, 22, "bold"), bg=CARD_BG, fg=ACCENT).pack(pady=25)

        self.output_text = ScrolledText(
            card,
            wrap="word",
            font=(FONT_FAMILY, 11),
            height=20,
            bd=1,
            relief="solid",
        )
        self.output_text.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        self.output_text.insert(
            "1.0",
            "Click 'Generate Explanation' to produce an explainability report from session data.",
        )
        self.output_text.config(state=tk.DISABLED)

        btn_row = tk.Frame(card, bg=CARD_BG)
        btn_row.pack(pady=10)

        tk.Button(
            btn_row,
            text="Generate Explanation",
            width=20,
            font=(FONT_FAMILY, 12),
            command=self.generate_explanation,
            bg=ACCENT,
            fg="white",
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            btn_row,
            text="Back to Results",
            width=20,
            font=(FONT_FAMILY, 12),
            command=lambda: controller.show_frame(ResultsFrame),
        ).grid(row=0, column=1, padx=8)

    def set_results_data(self, results_data):
        self.results_data = results_data
        self._set_output("Session data loaded. Click 'Generate Explanation'.")

    def _set_output(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.config(state=tk.DISABLED)

    def _build_explanation_payload(self):
        if not self.results_data:
            return None
        domain_reports = {}

        for domain, data in self.results_data.get("domains", {}).items():
            attempted = int(data.get("attempted", 0) or 0)
            if attempted <= 0:
                continue

            domain_reports[domain] = {
                "li": data.get("li", 0.0),
                "trend": data.get("trend", 0.0),
                "ci": data.get("ci", 0.0),
                "attempted": attempted,
                "avg_time": data.get("avg_time", 0.0),
                "accuracy": data.get("accuracy", 0.0),
                "difficulty_used": data.get("difficulty_used", 1),
                "difficulty_next": data.get("difficulty_next", 1),
                "behavior_counts": data.get("behavior_counts", {}),
            }

        return domain_reports

    def generate_explanation(self):
        domain_reports = self._build_explanation_payload()
        if not domain_reports:
            messagebox.showerror("Error", "No results data available for explainability.")
            return

        total_attempted = sum(int(d.get("attempted", 0) or 0) for d in domain_reports.values())
        if total_attempted == 0:
            self._set_output("No session data available for explanation.")
            return

        self._set_output("Generating explanation... Please wait.")

        try:
            explanation = self.explainability_agent.generate_explanation(domain_reports)
            self._set_output(explanation)
        except Exception as exc:
            self._set_output("Failed to generate explanation.")
            messagebox.showerror("Explainability Error", f"Failed to generate explanation:\n{exc}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
