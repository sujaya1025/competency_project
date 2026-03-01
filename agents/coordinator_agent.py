class CoordinatorAgent:
    def __init__(self):
        self.reports = []

    def collect_report(self, report):
        if report and int(report.get("attempted", 0) or 0) > 0:
            self.reports.append(report)

    def summarize(self):
        if not self.reports:
            return {
                "domains_attempted": 0,
                "avg_li": 0.0,
                "avg_time": 0.0,
                "avg_accuracy": 0.0,
            }

        n = len(self.reports)
        return {
            "domains_attempted": n,
            "avg_li": round(sum(r["li"] for r in self.reports) / n, 4),
            "avg_time": round(sum(r["avg_time"] for r in self.reports) / n, 2),
            "avg_accuracy": round(sum(r["accuracy"] for r in self.reports) / n, 2),
        }
