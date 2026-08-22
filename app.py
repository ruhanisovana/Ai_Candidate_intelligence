
from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

DATABASE = "candidates.db"


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)

    # Allows us to access columns by name
    conn.row_factory = sqlite3.Row

    return conn


# -----------------------------
# CREATE DATABASE TABLE
# -----------------------------

def init_db():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            github_username TEXT,
            portfolio TEXT,
            job_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title TEXT NOT NULL,
    job_description TEXT NOT NULL,
    required_skills TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

    conn.commit()
    conn.close()


# -----------------------------
# HOME PAGE
# -----------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -----------------------------
# UPLOAD CANDIDATE
# -----------------------------

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        github_username = request.form.get(
            "github_username", ""
        ).strip()
        portfolio = request.form.get(
            "portfolio", ""
        ).strip()
        job_description = request.form.get(
            "job_description", ""
        ).strip()

        # Basic validation
        if not full_name or not email:
            return "Full name and email are required."

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO candidates (
                full_name,
                email,
                github_username,
                portfolio,
                job_description
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            full_name,
            email,
            github_username,
            portfolio,
            job_description
        ))

        conn.commit()
        conn.close()

        return redirect("/candidates")

    return render_template("upload.html")


# -----------------------------
# STORED CANDIDATES
# -----------------------------

@app.route("/candidates")
def candidates_page():

    conn = get_db_connection()

    candidates = conn.execute("""
        SELECT
            id,
            full_name,
            email,
            github_username,
            portfolio,
            job_description,
            created_at
        FROM candidates
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "store_candidate.html",
        candidates=candidates
    )


# -----------------------------
# CANDIDATE DETAILS
# -----------------------------

@app.route("/candidate/<int:candidate_id>")
def candidate_detail(candidate_id):

    conn = get_db_connection()

    candidate = conn.execute("""
        SELECT
            id,
            full_name,
            email,
            github_username,
            portfolio,
            job_description,
            created_at
        FROM candidates
        WHERE id = ?
    """, (candidate_id,)).fetchone()

    conn.close()

    if candidate is None:
        return "Candidate not found.", 404

    return render_template(
    "candidate_details.html",
    candidate=candidate
    )


# -----------------------------
# DELETE CANDIDATE
# -----------------------------

@app.route("/candidate/<int:candidate_id>/delete", methods=["POST"])
def delete_candidate(candidate_id):

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM candidates
        WHERE id = ?
    """, (candidate_id,))

    conn.commit()
    conn.close()

    return redirect("/candidates")


# -----------------------------
# INITIALIZE DATABASE
# -----------------------------

init_db()

@app.route("/create-job", methods=["GET", "POST"])
def create_job():

    if request.method == "POST":

        job_title = request.form["job_title"]
        job_description = request.form["job_description"]
        required_skills = request.form["required_skills"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO jobs
            (
                job_title,
                job_description,
                required_skills
            )
            VALUES (?, ?, ?)
        """, (
            job_title,
            job_description,
            required_skills
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/jobs")

    return render_template("create_job.html")

@app.route("/jobs")
def jobs_page():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            job_title,
            job_description,
            required_skills,
            created_at
        FROM jobs
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    jobs = []

    for row in rows:

        jobs.append({
            "id": row[0],
            "job_title": row[1],
            "job_description": row[2],
            "required_skills": row[3],
            "created_at": row[4]
        })

    return render_template(
        "jobs.html",
        jobs=jobs
    )
# -----------------------------
# RUN APPLICATION
# -----------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
