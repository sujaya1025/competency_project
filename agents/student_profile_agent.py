class StudentProfileAgent:
    def __init__(self, student_id=None, db_manager=None):
        self.student_id = student_id
        self.db_manager = db_manager
        self.domains = {
            "aptitude": self._init_domain("aptitude"),
            "reasoning": self._init_domain("reasoning"),
            "verbal": self._init_domain("verbal"),
        }
        self.overall_ci = self._compute_overall_ci()

    def _init_domain(self, domain_name):
        state = {
            "ci": 0.0,
            "previous_li": None,
            "current_difficulty": 1,
            "session_difficulty": 1,
            "total_attempted": 0,
            "total_time": 0.0,
            "session_attempted": 0,
            "session_time": 0.0,
            "session_correct": 0,
            "session_scores": [],
            "session_logs": [],
            "avg_time": 0.0,
            "session_avg_time": 0.0,
        }

        if self.student_id and self.db_manager:
            data = self.db_manager.load_domain(self.student_id, domain_name)
            if data:
                ci, difficulty, previous_li, total_attempted, total_time = data
                state["ci"] = float(ci or 0.0)
                state["current_difficulty"] = int(difficulty or 1)
                state["session_difficulty"] = state["current_difficulty"]
                state["previous_li"] = previous_li if previous_li is not None else None
                state["total_attempted"] = int(total_attempted or 0)
                state["total_time"] = float(total_time or 0.0)

        attempts = state["total_attempted"]
        state["avg_time"] = (state["total_time"] / attempts) if attempts > 0 else 0.0
        return state

    def _compute_overall_ci(self):
        cis = [self.domains[d]["ci"] for d in self.domains]
        return round(sum(cis) / len(cis), 3) if cis else 0.0

    def get_domain_state(self, domain):
        state = self.domains[domain]
        total_attempts = state["total_attempted"]
        state["avg_time"] = (state["total_time"] / total_attempts) if total_attempts > 0 else 0.0
        session_attempts = state["session_attempted"]
        state["session_avg_time"] = (state["session_time"] / session_attempts) if session_attempts > 0 else 0.0
        return state

    def get_overall_ci(self):
        self.overall_ci = self._compute_overall_ci()
        return self.overall_ci

    def reset_session_metrics(self):
        for domain in self.domains:
            state = self.domains[domain]
            state["session_attempted"] = 0
            state["session_time"] = 0.0
            state["session_correct"] = 0
            state["session_scores"] = []
            state["session_logs"] = []
            state["session_avg_time"] = 0.0
            state["session_difficulty"] = state["current_difficulty"]

    def log_question_submission(self, domain, question_id, is_correct, response_time, score, behavior_flag):
        state = self.domains[domain]
        state["session_attempted"] += 1
        state["total_attempted"] += 1
        state["session_time"] += response_time
        state["total_time"] += response_time
        if is_correct:
            state["session_correct"] += 1
        state["session_scores"].append(float(score))
        state["session_logs"].append(
            {
                "question_id": str(question_id),
                "correctness": 1 if is_correct else 0,
                "time_taken": float(response_time),
                "ps_i": float(score),
                "behavior_flag": behavior_flag,
            }
        )

    def apply_session_outcome(self, domain, li, trend, ci_new, next_difficulty):
        state = self.domains[domain]
        state["previous_li"] = float(li)
        state["ci"] = float(ci_new)
        state["current_difficulty"] = int(next_difficulty)
        self.overall_ci = self._compute_overall_ci()
