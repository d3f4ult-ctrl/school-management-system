import os
import psycopg2
import psycopg2.extras

SUBJECTS = ["English", "Math", "Physics", "Chemistry", "Biology", "Civic Education", "French"]


def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL environment variable is required')
    return psycopg2.connect(DATABASE_URL)


def init_db():
    subjects_list = "', '".join(SUBJECTS)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students(
                    id SERIAL PRIMARY KEY,
                    student_id TEXT NOT NULL UNIQUE
                )
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS results(
                    id SERIAL PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
                    CHECK (subject IN ('{subjects_list}'))
                )
            """)
        conn.commit()
    finally:
        conn.close()


def insert_result(student_id, subject, score):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO results (student_id, subject, score) VALUES (%s, %s, %s)",
                        (student_id, subject, score))
        conn.commit()
    finally:
        conn.close()


def get_all_results():
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT student_id, subject, score FROM results ORDER BY student_id")
            return cur.fetchall()
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    insert_result("S001", "English", 92)
    insert_result("S001", "Math", 99)
    insert_result("S001", "Physics", 99)
    insert_result("S001", "Chemistry", 98)
    insert_result("S001", "Biology", 95)
    insert_result("S001", "Civic Education", 100)
    insert_result("S001", "French", 100)
    insert_result("S002", "English", 85)
    insert_result("S002", "Math", 88)
    insert_result("S002", "Physics", 90)
    insert_result("s001", "Chemistry", 87)
    insert_result("S002", "Biology", 82)
    insert_result("S002", "Civic Education", 90)
    insert_result("S002", "French", 85)
