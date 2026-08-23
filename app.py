
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
            linkedin TEXT,
            portfolio TEXT,
            skills TEXT,
            experience TEXT,
            job_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    columns = conn.execute("""
        PRAGMA table_info(candidates)
    """).fetchall()

    existing_columns = [
        column["name"]
        for column in columns
    ]

    if "linkedin" not in existing_columns:

        conn.execute("""
            ALTER TABLE candidates
            ADD COLUMN linkedin TEXT
        """)

    if "skills" not in existing_columns:

        conn.execute("""
            ALTER TABLE candidates
            ADD COLUMN skills TEXT
        """)

    if "experience" not in existing_columns:

        conn.execute("""
            ALTER TABLE candidates
            ADD COLUMN experience TEXT
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

        full_name = request.form.get(
            "full_name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip()

        github_username = request.form.get(
            "github_username", ""
        ).strip()

        linkedin = request.form.get(
            "linkedin", ""
        ).strip()

        portfolio = request.form.get(
            "portfolio", ""
        ).strip()

        skills = request.form.get(
            "skills", ""
        ).strip()

        experience = request.form.get(
            "experience", ""
        ).strip()

        job_description = request.form.get(
            "job_description", ""
        ).strip()

        # Basic validation

        if not full_name or not email:

            return "Full name and email are required.", 400

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO candidates (
                full_name,
                email,
                github_username,
                linkedin,
                portfolio,
                skills,
                experience,
                job_description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name,
            email,
            github_username,
            linkedin,
            portfolio,
            skills,
            experience,
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
        linkedin,
        portfolio,
        skills,
        experience,
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

@app.route("/candidate/<int:candidate_id>/analyze", methods=["GET", "POST"])
def analyze_candidate(candidate_id):

    conn = get_db_connection()

    # Get candidate
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

    # Candidate doesn't exist
    if candidate is None:
        conn.close()
        return "Candidate not found.", 404

    # Get all jobs
    jobs = conn.execute("""
        SELECT
            id,
            job_title,
            job_description,
            required_skills
        FROM jobs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    # No jobs created yet
    if not jobs:
        return """
        <h2>No jobs available.</h2>
        <p>Create a job before analyzing a candidate.</p>
        <a href="/create-job">Create Job</a>
        """

    # Show job selection
    if request.method == "GET":

        return render_template(
            "analyze_candidate.html",
            candidate=candidate,
            jobs=jobs
        )

    # Selected job
    job_id = request.form.get("job_id")

    if not job_id:
        return "Please select a job.", 400

    conn = get_db_connection()

    job = conn.execute("""
        SELECT
            id,
            job_title,
            job_description,
            required_skills
        FROM jobs
        WHERE id = ?
    """, (job_id,)).fetchone()

    conn.close()

    if job is None:
        return "Job not found.", 404

    # -----------------------------
    # PREPARE SKILLS
    # -----------------------------

    required_skills = [
        skill.strip().lower()
        for skill in job["required_skills"].split(",")
        if skill.strip()
    ]

    # Combine candidate information
    candidate_text = " ".join([
    candidate["full_name"] or "",
    candidate["github_username"] or "",
    candidate["linkedin"] or "",
    candidate["portfolio"] or "",
    candidate["skills"] or "",
    candidate["experience"] or "",
    candidate["job_description"] or ""
]).lower()-------------------------
    # MATCH SKILLS
    # -----------------------------

    matched_skills = []
    missing_skills = []

    for skill in required_skills:

        if skill in candidate_text:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    # -----------------------------
    # CALCULATE MATCH
    # -----------------------------

    if required_skills:

        match_percentage = round(
            (len(matched_skills) / len(required_skills)) * 100
        )

    else:
        match_percentage = 0

    return render_template(
        "analysis_result.html",
        candidate=candidate,
        job=job,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        match_percentage=match_percentage
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
