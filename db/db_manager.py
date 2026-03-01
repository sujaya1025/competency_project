import sqlite3
from datetime import datetime
import bcrypt


DOMAINS = ["aptitude", "reasoning", "verbal"]


class DBManager:
    def __init__(self, db_name="adaptive_assessment.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._ensure_student_profile_columns()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date TEXT NOT NULL,
                overall_ci REAL DEFAULT 0.0,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
            """
        )
        self._ensure_sessions_columns()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                li REAL NOT NULL,
                trend REAL NOT NULL,
                ci REAL NOT NULL,
                difficulty_used INTEGER NOT NULL,
                difficulty_next INTEGER NOT NULL,
                attempted INTEGER NOT NULL,
                avg_time REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS question_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                question_id TEXT NOT NULL,
                correctness INTEGER NOT NULL,
                time_taken REAL NOT NULL,
                ps_i REAL NOT NULL,
                behavior_flag TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
            """
        )
        self.conn.commit()

    def _ensure_student_profile_columns(self):
        self.cursor.execute("PRAGMA table_info(students)")
        columns = {row[1] for row in self.cursor.fetchall()}
        required = [
            ("CI_A", "REAL DEFAULT 0.0"),
            ("CI_R", "REAL DEFAULT 0.0"),
            ("CI_V", "REAL DEFAULT 0.0"),
            ("CI_overall", "REAL DEFAULT 0.0"),
            ("difficulty_A", "INTEGER DEFAULT 1"),
            ("difficulty_R", "INTEGER DEFAULT 1"),
            ("difficulty_V", "INTEGER DEFAULT 1"),
        ]
        for name, ddl in required:
            if name not in columns:
                self.cursor.execute(f"ALTER TABLE students ADD COLUMN {name} {ddl}")

    def _ensure_sessions_columns(self):
        self.cursor.execute("PRAGMA table_info(sessions)")
        columns = {row[1] for row in self.cursor.fetchall()}
        if "overall_ci" not in columns:
            self.cursor.execute("ALTER TABLE sessions ADD COLUMN overall_ci REAL DEFAULT 0.0")

    # ---------------------------
    # AUTH
    # ---------------------------

    def create_student(self, student_id, name, email, password):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            self.cursor.execute(
                """
                INSERT INTO students (student_id, name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (student_id, name, email, hashed.decode(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_student(self, email, password):
        self.cursor.execute("SELECT student_id, password_hash FROM students WHERE email=?", (email,))
        result = self.cursor.fetchone()
        if result:
            student_id, stored_hash = result
            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                return student_id
        return None

    def get_student_info(self, student_id):
        self.cursor.execute("SELECT name, email, created_at FROM students WHERE student_id=?", (student_id,))
        return self.cursor.fetchone()

    # ---------------------------
    # PROFILE + SESSION DATA
    # ---------------------------

    def load_domain(self, student_id, domain_name):
        ci_col = {"aptitude": "CI_A", "reasoning": "CI_R", "verbal": "CI_V"}[domain_name]
        diff_col = {"aptitude": "difficulty_A", "reasoning": "difficulty_R", "verbal": "difficulty_V"}[domain_name]

        self.cursor.execute(
            f"SELECT {ci_col}, {diff_col} FROM students WHERE student_id=?",
            (student_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            return None
        ci, difficulty = row

        self.cursor.execute(
            """
            SELECT li
            FROM session_results
            WHERE student_id=? AND domain=?
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
            """,
            (student_id, domain_name),
        )
        prev_row = self.cursor.fetchone()
        previous_li = prev_row[0] if prev_row else None

        self.cursor.execute(
            """
            SELECT COALESCE(SUM(attempted), 0), COALESCE(SUM(attempted * avg_time), 0.0)
            FROM session_results
            WHERE student_id=? AND domain=?
            """,
            (student_id, domain_name),
        )
        totals = self.cursor.fetchone() or (0, 0.0)
        return (float(ci or 0.0), int(difficulty or 1), previous_li, int(totals[0] or 0), float(totals[1] or 0.0))

    def update_student_profile(self, student_id, ci_by_domain, ci_overall, difficulty_by_domain):
        self.cursor.execute(
            """
            UPDATE students
            SET CI_A=?, CI_R=?, CI_V=?, CI_overall=?, difficulty_A=?, difficulty_R=?, difficulty_V=?
            WHERE student_id=?
            """,
            (
                float(ci_by_domain.get("aptitude", 0.0)),
                float(ci_by_domain.get("reasoning", 0.0)),
                float(ci_by_domain.get("verbal", 0.0)),
                float(ci_overall),
                int(difficulty_by_domain.get("aptitude", 1)),
                int(difficulty_by_domain.get("reasoning", 1)),
                int(difficulty_by_domain.get("verbal", 1)),
                student_id,
            ),
        )
        self.conn.commit()

    def create_session(self, student_id, overall_ci):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO sessions (student_id, date, overall_ci) VALUES (?, ?, ?)",
            (student_id, now, float(overall_ci)),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def save_session_result(
        self,
        session_id,
        student_id,
        domain,
        li,
        trend,
        ci,
        difficulty_used,
        difficulty_next,
        attempted,
        avg_time,
    ):
        self.cursor.execute(
            """
            INSERT INTO session_results
            (session_id, student_id, domain, li, trend, ci, difficulty_used, difficulty_next, attempted, avg_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(session_id),
                student_id,
                domain,
                float(li),
                float(trend),
                float(ci),
                int(difficulty_used),
                int(difficulty_next),
                int(attempted),
                float(avg_time),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        self.conn.commit()

    def save_question_log(self, session_id, student_id, domain, question_id, correctness, time_taken, ps_i, behavior_flag):
        self.cursor.execute(
            """
            INSERT INTO question_logs
            (session_id, student_id, domain, question_id, correctness, time_taken, ps_i, behavior_flag, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(session_id),
                student_id,
                domain,
                str(question_id),
                int(correctness),
                float(time_taken),
                float(ps_i),
                behavior_flag,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        self.conn.commit()

    def get_student_sessions(self, student_id):
        self.cursor.execute(
            """
            SELECT session_id, date, overall_ci
            FROM sessions
            WHERE student_id=?
            ORDER BY date DESC
            """,
            (student_id,),
        )
        return self.cursor.fetchall()

    # Compatibility wrapper for old call sites
    def save_domain_result(self, *args, **kwargs):
        if len(args) >= 10:
            return self.save_session_result(*args, **kwargs)
        raise ValueError("save_domain_result signature changed. Use save_session_result.")

    def close(self):
        self.conn.close()
