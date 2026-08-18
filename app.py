from flask import Flask, render_template, request, redirect
import os
import psycopg2

app = Flask(__name__)


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# -----------------------------
# CREATE CANDIDATES TABLE
# -----------------------------

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    github_username TEXT,
    portfolio TEXT,
    job_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

cursor.close()
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

        full_name = request.form["full_name"]
        email = request.form["email"]
        github_username = request.form["github_username"]
        portfolio = request.form["portfolio"]
        job_description = request.form["job_description"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO candidates
            (
                full_name,
                email,
                github_username,
                portfolio,
                job_description
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            full_name,
            email,
            github_username,
            portfolio,
            job_description
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/candidates")

    return render_template("upload.html")


# -----------------------------
# STORED CANDIDATES
# -----------------------------

@app.route("/candidates")
def candidates_page():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
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
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    candidates = []

    for row in rows:

        candidate = {
            "id": row[0],
            "full_name": row[1],
            "email": row[2],
            "github_username": row[3],
            "portfolio": row[4],
            "job_description": row[5],
            "created_at": row[6]
        }

        candidates.append(candidate)

    return render_template(
        "store_candidate.html",
        candidates=candidates
    )


# -----------------------------
# RUN APPLICATION
# -----------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
