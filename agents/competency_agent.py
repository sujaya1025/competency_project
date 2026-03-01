class CompetencyAgent:
    def __init__(self, student_profile, w_c=0.7, w_t=0.3, t_max=60.0, beta=0.6):
        self.student_profile = student_profile
        self.w_c = float(w_c)
        self.w_t = float(w_t)
        self.t_max = float(t_max)
        self.beta = float(beta)

    def compute_time_efficiency(self, time_taken):
        return max(0.0, 1.0 - (float(time_taken) / self.t_max))

    def compute_question_score(self, is_correct, time_taken):
        c_i = 1.0 if is_correct else 0.0
        te_i = self.compute_time_efficiency(time_taken)
        ps_i = (self.w_c * c_i) + (self.w_t * te_i)
        return max(0.0, min(1.0, ps_i))

    def detect_behavior_flag(self, is_correct, time_taken):
        if (not is_correct) and (float(time_taken) < 0.4 * self.t_max):
            return "guessing"
        if is_correct and (float(time_taken) > 0.8 * self.t_max):
            return "overthinking"
        return "normal"

    def record_submission(self, domain, question_id, is_correct, time_taken):
        ps_i = self.compute_question_score(is_correct=is_correct, time_taken=time_taken)
        behavior_flag = self.detect_behavior_flag(is_correct=is_correct, time_taken=time_taken)
        self.student_profile.log_question_submission(
            domain=domain,
            question_id=question_id,
            is_correct=is_correct,
            response_time=time_taken,
            score=ps_i,
            behavior_flag=behavior_flag,
        )
        return {"ps_i": round(ps_i, 4), "behavior_flag": behavior_flag}

    def compute_domain_session_metrics(self, domain):
        state = self.student_profile.get_domain_state(domain)
        attempted = state["session_attempted"]
        if attempted <= 0:
            return None

        li = sum(state["session_scores"]) / attempted
        previous_li = state["previous_li"]
        trend = (li - previous_li) if previous_li is not None else 0.0

        ci_previous = state["ci"]
        ci_new = li if ci_previous is None else (self.beta * li) + ((1.0 - self.beta) * ci_previous)

        avg_time = state["session_time"] / attempted
        accuracy = (state["session_correct"] / attempted) * 100.0

        behavior_counts = {"guessing": 0, "overthinking": 0, "normal": 0}
        for item in state["session_logs"]:
            flag = item.get("behavior_flag", "normal")
            behavior_counts[flag] = behavior_counts.get(flag, 0) + 1

        return {
            "domain": domain,
            "attempted": attempted,
            "li": round(li, 4),
            "trend": round(trend, 4),
            "ci_previous": round(ci_previous, 4),
            "ci": round(ci_new, 4),
            "avg_time": round(avg_time, 2),
            "accuracy": round(accuracy, 2),
            "difficulty_used": int(state["session_difficulty"]),
            "behavior_counts": behavior_counts,
        }

    def get_overall_competency(self):
        cis = [self.student_profile.domains[d]["ci"] for d in self.student_profile.domains]
        overall_ci = round(sum(cis) / len(cis), 4) if cis else 0.0
        return {"ci_overall": overall_ci}
