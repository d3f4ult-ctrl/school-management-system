from flask import Flask, render_template, url_for, redirect, request, session, flash
import os
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
import psycopg2.extras
from create_student_database import SUBJECTS

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL environment variable is required')
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def execute_fetchone(query, params=()):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()
    finally:
        conn.close()


def execute_fetchall(query, params=()):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def execute_commit(query, params=()):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()
    finally:
        conn.close()

def verify_user(table, email, password):
    row = execute_fetchone(f"SELECT * FROM {table} WHERE email = %s", (email,))
    if row and check_password_hash(row['password'], password):
        return row
    return None

def verify_student(table, student_id):
    return execute_fetchone(f"SELECT * FROM {table} WHERE student_id = %s", (student_id,))

def insert_admin(email, password):
    existing = execute_fetchone('SELECT * FROM admins WHERE email = %s', (email,))
    if existing:
        return False
    hashed_password = generate_password_hash(password)
    execute_commit('INSERT INTO admins (email, password) VALUES (%s, %s)', (email, hashed_password))
    return True

def insert_staff(email, password):
    existing = execute_fetchone('SELECT * FROM staff WHERE email = %s', (email,))
    if existing:
        return False
    hashed_password = generate_password_hash(password)
    execute_commit('INSERT INTO staff (email, password) VALUES (%s, %s)', (email, hashed_password))
    return True

def insert_student(student_id):
    existing = execute_fetchone('SELECT * FROM students WHERE student_id = %s', (student_id,))
    if existing:
        return False
    execute_commit('INSERT INTO students (student_id) VALUES (%s)', (student_id,))
    return True

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/view_results')
def view_results():
    rows = execute_fetchall("SELECT student_id, subject, score FROM results ORDER BY student_id")

    students = {}
    for row in rows:
        sid = row["student_id"]
        if sid not in students:
            students[sid] = {subj: "-" for subj in SUBJECTS}
        students[sid][row["subject"]] = row["score"]

    return render_template('view_results.html', students=students, subjects=SUBJECTS)

@app.route('/add_admin', methods=["GET", "POST"])
def add_admin():
    if request.method == 'POST':
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if not email or not password:
            flash("Email and password are required")
            return redirect(url_for("add_admin"))
        success = insert_admin(email, password)
        
        if success:
            flash(f"Admin {email} created successfully")
            return redirect(url_for('add_admin'))
        else:
            flash("Email already exists")
            return redirect(url_for('add_admin'))
    return render_template("add_admin.html")

@app.route('/add_staff', methods=["GET", "POST"])
def add_staff():
    if request.method == 'POST':
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if not email or not password:
            flash("Email and password are required")
            return redirect(url_for("add_staff"))
        success = insert_staff(email, password)
        
        if success:
            flash(f"Staff {email} created successfully")
            return redirect(url_for('add_staff'))
        else:
            flash("Email already exists")
            return redirect(url_for('add_staff'))
    return render_template("add_staff.html")

@app.route('/add_student', methods=["GET", "POST"])
def add_student():
    if request.method == 'POST':
        student_id = request.form["student_id"].strip()
        if not student_id:
            flash("Student ID is required")
            return redirect(url_for("add_student"))
        success = insert_student(student_id)
        
        if success:
            flash(f"Student with ID {student_id} created successfully")
            return redirect(url_for('add_student'))
        else:
            flash("Student ID already exists")
            return redirect(url_for('add_student'))
    return render_template("add_student.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = verify_user('admin.db', 'admins', email, password)
        if user:
            session['user_role'] = 'admin'
            session['email'] = user['email']
            return redirect(url_for('management'))
        flash('Invalid email or password')
    return render_template('admin_login.html')

@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = verify_user('staff.db', 'staff', email, password)
        if user:
            session['user_role'] = 'staff'
            session['email'] = user['email']
            return redirect(url_for('management'))
        flash('Invalid email or password')
    return render_template('staff_login.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        user = verify_student('student.db', 'students', student_id)
        if user:
            session['user_role'] = 'student'
            session['student_id'] = user['student_id']
            return redirect(url_for('management'))
        flash('Invalid student id')
    return render_template('student_login.html')

@app.route('/management')
def management():
    if 'user_role' not in session:
        flash('Please login first')
        return redirect(url_for('index'))
    
    if session['user_role'] == 'admin':
        return render_template('admin_dashboard.html')
    
    elif session['user_role'] == 'teacher':
        return render_template('teacher_login.html')
    
    elif session['user_role'] == 'student':
        return render_template('student_dashboard.html')
    
    else:
        flash('Access denied')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5800)