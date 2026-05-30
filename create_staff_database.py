import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash


def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL environment variable is required')
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS staff(
                    id SERIAL PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()


def insert_staff(email, password):
    hashed_pw = generate_password_hash(password)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO staff (email, password) VALUES (%s, %s)", (email, hashed_pw))
                conn.commit()
                return True
            except psycopg2.IntegrityError:
                conn.rollback()
                return False
    finally:
        conn.close()


def verify_staff(email, password):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM staff WHERE email = %s", (email,))
            row = cur.fetchone()
            if row and check_password_hash(row['password'], password):
                return True
            return False
    finally:
        conn.close()


def get_all_staff():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM staff")
            return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    insert_staff("teacher@example.com", "teacher1")
    insert_staff("teacher2@gmail.com", "teacher2")