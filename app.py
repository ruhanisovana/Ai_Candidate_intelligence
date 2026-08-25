from flask import Flask, render_template, request, redirect
import sqlite3
import re
import requests
from urllib.parse import urlparse

app = Flask(__name__)

DATABASE = "candidates.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db_connection()

    # -----------------------------------------------------
    # CANDIDATES TABLE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CHECK EXISTING COLUMNS
    # -----------------------------------------------------

    columns = conn.execute("""
        PRAGMA table_info(candidates)
    """).fetchall()

    existing_columns = [
        column["name"]
        for column in columns
    ]

    # Add LinkedIn if old database doesn't have it
    if "linkedin" not in existing_columns:

        conn.execute("""
            ALTER TABLE candidates
            ADD COLUMN linkedin TEXT
        """)

    # Add Skills if old database doesn't have it
    if "skills" not in existing_columns:

        conn.execute("""
            ALTER TABLE candidates
            ADD COLUMN skills TEXT
        """)

    # Add Experience if old database doesn't have it
    if "experience" not in existing_columns:

        conn.execute("""
            ALTER TABLE candidates
            ADD COLUMN experience TEXT
        """)

    # -----------------------------------------------------
    # JOBS TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            job_description TEXT NOT NULL,
            required_skills TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS candidate_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        url TEXT NOT NULL,
        source_type TEXT DEFAULT 'unknown',
        status TEXT DEFAULT 'pending',
        title TEXT,
        description TEXT,
        technologies TEXT,
        evidence TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
    )
""")

    conn.commit()
    conn.close()


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# UPLOAD CANDIDATE
# =========================================================

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

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not full_name or not email:

            return "Full name and email are required.", 400

        # -------------------------------------------------
        # SAVE CANDIDATE
        # -------------------------------------------------

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

                # -------------------------------------------------
        # SAVE CANDIDATE
        # -------------------------------------------------

        candidate_id = conn.execute("""
            SELECT last_insert_rowid()
        """).fetchone()[0]

        # -------------------------------------------------
        # SAVE CANDIDATE SOURCES
        # -------------------------------------------------

        source_urls = [
            github_username,
            linkedin,
            portfolio
        ]

        for url in source_urls:

            if url:

                conn.execute("""
                    INSERT INTO candidate_sources (
                        candidate_id,
                        url,
                        source_type,
                        status
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    candidate_id,
                    url,
                    "unknown",
                    "pending"
                ))

        conn.commit()
        conn.close()

        return redirect("/candidates")

    return render_template("upload.html")


# =========================================================
# STORED CANDIDATES
# =========================================================

@app.route("/candidates")
def candidates_page():

    conn = get_db_connection()

    candidates = conn.execute("""
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
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "store_candidate.html",
        candidates=candidates
    )


# =========================================================
# CANDIDATE DETAILS
# =========================================================

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


# =========================================================
# DELETE CANDIDATE
# =========================================================

@app.route(
    "/candidate/<int:candidate_id>/delete",
    methods=["POST"]
)
def delete_candidate(candidate_id):

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM candidates
        WHERE id = ?
    """, (candidate_id,))

    conn.commit()
    conn.close()

    return redirect("/candidates")


# =========================================================
# CREATE JOB
# =========================================================

@app.route("/create-job", methods=["GET", "POST"])
def create_job():

    if request.method == "POST":

        job_title = request.form.get(
            "job_title", ""
        ).strip()

        job_description = request.form.get(
            "job_description", ""
        ).strip()

        required_skills = request.form.get(
            "required_skills", ""
        ).strip()

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not job_title:
            return "Job title is required.", 400

        if not job_description:
            return "Job description is required.", 400

        if not required_skills:
            return "Required skills are required.", 400

        # -------------------------------------------------
        # SAVE JOB
        # -------------------------------------------------

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO jobs (
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
        conn.close()

        return redirect("/jobs")

    return render_template("create_job.html")


# =========================================================
# STORED JOBS
# =========================================================

@app.route("/jobs")
def jobs_page():

    conn = get_db_connection()

    jobs = conn.execute("""
        SELECT
            id,
            job_title,
            job_description,
            required_skills,
            created_at
        FROM jobs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "jobs.html",
        jobs=jobs
    )


# =========================================================
# ANALYZE A PUBLIC URL
#def analyze_url(url):
    """
    Analyze a candidate-provided public URL.

    Supports:
    - GitHub public profiles/repositories
    - LinkedIn URL verification
    - Public websites/portfolio pages
    """

    if not url:
        return {
            "url": "",
            "type": "unknown",
            "status": "not provided",
            "title": "",
            "description": "",
            "technologies": [],
            "evidence": [],
            "confidence": "None"
        }

    url = url.strip()

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return {
            "url": url,
            "type": "invalid",
            "status": "invalid URL",
            "title": "",
            "description": "",
            "technologies": [],
            "evidence": [],
            "confidence": "None"
        }

    hostname = parsed.netloc.lower()

    # =====================================================
    # GITHUB
    # =====================================================

    if "github.com" in hostname:

        return analyze_github_url(url)

    # =====================================================
    # LINKEDIN
    # =====================================================

    if "linkedin.com" in hostname:

        return {
            "url": url,
            "type": "linkedin",
            "status": "profile URL supplied",
            "title": "LinkedIn profile",
            "description": "",
            "technologies": [],
            "evidence": [
                "Candidate supplied a LinkedIn profile URL.",
                "Profile content was not independently scraped."
            ],
            "confidence": "Limited"
        }

    # =====================================================
    # PUBLIC WEBSITE
    # =====================================================

    return analyze_website(url) =========================================================

--------------------------------------
def analyze_github_url(url):

    parsed = urlparse(url)

    parts = [
        part
        for part in parsed.path.strip("/").split("/")
        if part
    ]

    if not parts:

        return {
            "url": url,
            "type": "github",
            "status": "GitHub username not found",
            "title": "",
            "description": "",
            "technologies": [],
            "evidence": [],
            "confidence": "Low"
        }

    username = parts[0]

    api_url = f"https://api.github.com/users/{username}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Candidate-Intelligence/1.0"
    }

    try:

        # -------------------------------------------------
        # GET PROFILE
        # -------------------------------------------------

        profile_response = requests.get(
            api_url,
            headers=headers,
            timeout=10
        )

        if profile_response.status_code != 200:

            return {
                "url": url,
                "type": "github",
                "status": f"GitHub HTTP {profile_response.status_code}",
                "title": "",
                "description": "",
                "technologies": [],
                "evidence": [
                    "GitHub profile could not be retrieved."
                ],
                "confidence": "Low"
            }

        profile = profile_response.json()

        # -------------------------------------------------
        # GET REPOSITORIES
        # -------------------------------------------------

        repos_response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={
                "per_page": 100,
                "sort": "updated"
            },
            headers=headers,
            timeout=10
        )

        repositories = []

        if repos_response.status_code == 200:
            repositories = repos_response.json()

        # -------------------------------------------------
        # ANALYZE LANGUAGES
        # -------------------------------------------------

        languages = set()

        repository_evidence = []

        for repo in repositories:

            language = repo.get("language")

            if language:
                languages.add(language)

            repository_evidence.append({
                "name": repo.get("name"),
                "description": repo.get("description") or "",
                "language": language or "Unknown",
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "html_url": repo.get("html_url")
            })

        # -------------------------------------------------
        # TECHNOLOGY KEYWORDS
        # -------------------------------------------------

        technology_keywords = [
            "python",
            "flask",
            "django",
            "fastapi",
            "javascript",
            "typescript",
            "react",
            "node.js",
            "node",
            "html",
            "css",
            "sql",
            "sqlite",
            "postgresql",
            "mysql",
            "mongodb",
            "java",
            "c",
            "c++",
            "docker",
            "git",
            "api",
            "rest",
            "graphql"
        ]

        searchable_text = ""

        for repo in repository_evidence:

            searchable_text += " "
            searchable_text += repo["name"] or ""
            searchable_text += " "
            searchable_text += repo["description"] or ""
            searchable_text += " "
            searchable_text += repo["language"] or ""

        searchable_text = searchable_text.lower()

        technologies = []

        for technology in technology_keywords:

            if technology.lower() in searchable_text:
                technologies.append(technology)

        # Add GitHub languages
        for language in languages:

            if language.lower() not in [
                item.lower()
                for item in technologies
            ]:
                technologies.append(language)

        # -------------------------------------------------
        # EVIDENCE
        # -------------------------------------------------

        evidence = []

        evidence.append(
            f"GitHub username: {username}"
        )

        evidence.append(
            f"Public repositories found: {len(repositories)}"
        )

        if languages:

            evidence.append(
                "Detected repository languages: "
                + ", ".join(sorted(languages))
            )

        if technologies:

            evidence.append(
                "Detected technologies: "
                + ", ".join(sorted(technologies))
            )

        if profile.get("bio"):

            evidence.append(
                f"GitHub bio: {profile['bio']}"
            )

        evidence.append(
            f"Public followers: {profile.get('followers', 0)}"
        )

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        if repositories and technologies:
            confidence = "High"

        elif repositories:
            confidence = "Medium"

        else:
            confidence = "Low"

        return {
            "url": url,
            "type": "github",
            "status": "analyzed",
            "title": profile.get("name") or username,
            "description": profile.get("bio") or "",
            "technologies": sorted(technologies),
            "evidence": evidence,
            "repositories": repository_evidence,
            "confidence": confidence
        }

    except requests.RequestException:

        return {
            "url": url,
            "type": "github",
            "status": "GitHub request failed",
            "title": "",
            "description": "",
            "technologies": [],
            "evidence": [
                "Could not connect to GitHub."
            ],
            "confidence": "Low"
            }
=============================================

def analyze_website(url):

    try:

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent":
                "Mozilla/5.0 AI-Candidate-Intelligence/1.0"
            }
        )

        if response.status_code != 200:

            return {
                "url": url,
                "type": "website",
                "status": f"HTTP {response.status_code}",
                "title": "",
                "description": "",
                "technologies": [],
                "evidence": [
                    f"Website returned HTTP {response.status_code}."
                ],
                "confidence": "Low"
            }

        html = response.text

        # -------------------------------------------------
        # BASIC HTML ANALYSIS
        # -------------------------------------------------

        title = ""

        title_match = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            re.IGNORECASE | re.DOTALL
        )

        if title_match:

            title = re.sub(
                r"\s+",
                " ",
                title_match.group(1)
            ).strip()

        # -------------------------------------------------
        # TECHNOLOGY DETECTION
        # -------------------------------------------------

        technology_patterns = {

            "Python": [
                "python"
            ],

            "Flask": [
                "flask"
            ],

            "Django": [
                "django"
            ],

            "JavaScript": [
                "javascript",
                ".js"
            ],

            "TypeScript": [
                "typescript"
            ],

            "React": [
                "react"
            ],

            "Node.js": [
                "node.js",
                "nodejs"
            ],

            "HTML": [
                "<html",
                "<!doctype html"
            ],

            "CSS": [
                "<style",
                ".css"
            ],

            "Bootstrap": [
                "bootstrap"
            ],

            "Tailwind": [
                "tailwind"
            ],

            "API": [
                "api",
                "/api/"
            ]
        }

        html_lower = html.lower()

        technologies = []

        for technology, patterns in technology_patterns.items():

            for pattern in patterns:

                if pattern.lower() in html_lower:

                    technologies.append(technology)
                    break

        # -------------------------------------------------
        # EVIDENCE
        # -------------------------------------------------

        evidence = [
            "Public webpage successfully accessed.",
            f"HTTP status: {response.status_code}",
            f"Page size: {len(html)} characters."
        ]

        if title:

            evidence.append(
                f"Page title: {title}"
            )

        if technologies:

            evidence.append(
                "Detected technologies: "
                + ", ".join(technologies)
            )

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        if technologies:
            confidence = "Medium"
        else:
            confidence = "Low"

        return {
            "url": url,
            "type": "website",
            "status": "analyzed",
            "title": title,
            "description": "",
            "technologies": technologies,
            "evidence": evidence,
            "confidence": confidence
        }

    except requests.RequestException:

        return {
            "url": url,
            "type": "website",
            "status": "could not access",
            "title": "",
            "description": "",
            "technologies": [],
            "evidence": [
                "Website could not be accessed."
            ],
            "confidence": "Low"
        }

@app.route(
    "/candidate/<int:candidate_id>/analyze",
    methods=["GET", "POST"]
)
def analyze_candidate(candidate_id):

    # =====================================================
    # GET CANDIDATE
    # =====================================================

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

    # -----------------------------------------------------
    # CANDIDATE NOT FOUND
    # -----------------------------------------------------

    if candidate is None:

        conn.close()

        return "Candidate not found.", 404

    # =====================================================
    # GET JOBS
    # =====================================================

    jobs = conn.execute("""
        SELECT
            id,
            job_title,
            job_description,
            required_skills,
            created_at
        FROM jobs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    # =====================================================
    # NO JOBS
    # =====================================================

    if not jobs:

        return """
        <h2>No jobs available.</h2>

        <p>
            Create a job before analyzing a candidate.
        </p>

        <a href="/create-job">
            Create Job
        </a>
        """

    # =====================================================
    # GET REQUEST
    # SHOW JOB SELECTION
    # =====================================================

    if request.method == "GET":

        return render_template(
            "analyze_candidate.html",
            candidate=candidate,
            jobs=jobs
        )

    # =====================================================
    # POST REQUEST
    # GET SELECTED JOB
    # =====================================================

    job_id = request.form.get("job_id")

    if not job_id:

        return "Please select a job.", 400

    conn = get_db_connection()

    job = conn.execute("""
        SELECT
            id,
            job_title,
            job_description,
            required_skills,
            created_at
        FROM jobs
        WHERE id = ?
    """, (job_id,)).fetchone()

    conn.close()

    # =====================================================
    # JOB NOT FOUND
    # =====================================================

    if job is None:

        return "Job not found.", 404

    # =====================================================
    # 1. ANALYZE CANDIDATE SOURCES
    # =====================================================

    # =====================================================
# ANALYZE ALL CANDIDATE SOURCES
# =====================================================

conn = get_db_connection()

source_rows = conn.execute("""
    SELECT
        id,
        url,
        source_type,
        status,
        title,
        description,
        technologies,
        evidence
    FROM candidate_sources
    WHERE candidate_id = ?
    ORDER BY id ASC
""", (candidate_id,)).fetchall()

conn.close()

source_analyses = []

for source in source_rows:

    analysis = analyze_url(
        source["url"]
    )

    source_analyses.append(analysis)

    # =====================================================
    # 2. PREPARE REQUIRED SKILLS
    # =====================================================

    required_skills = [
        skill.strip().lower()
        for skill in job["required_skills"].split(",")
        if skill.strip()
    ]

    # =====================================================
    # 3. COMBINE CANDIDATE INFORMATION
    # =====================================================

    # =====================================================
# BUILD EVIDENCE TEXT
# =====================================================

candidate_text_parts = [
    candidate["full_name"] or "",
    candidate["skills"] or "",
    candidate["experience"] or "",
    candidate["job_description"] or ""
]

for analysis in source_analyses:

    candidate_text_parts.append(
        analysis.get("title", "")
    )

    candidate_text_parts.append(
        analysis.get("description", "")
    )

    candidate_text_parts.extend(
        analysis.get("technologies", [])
    )

    candidate_text_parts.extend(
        analysis.get("evidence", [])
    )

candidate_text = " ".join(
    candidate_text_parts
).lower()
    # 4. MATCH REQUIRED SKILLS
    # =====================================================

    matched_skills = []

    missing_skills = []

    for skill in required_skills:

        pattern = (
            r"(?<!\w)"
            + re.escape(skill)
            + r"(?!\w)"
        )

        if re.search(pattern, candidate_text):

            matched_skills.append(skill)

        else:

            missing_skills.append(skill)

    # =====================================================
    # 5. CALCULATE MATCH PERCENTAGE
    # =====================================================

    if required_skills:

        match_percentage = round(
            (
                len(matched_skills)
                /
                len(required_skills)
            ) * 100
        )

    else:

        match_percentage = 0

    # =====================================================
    # 6. COLLECT AVAILABLE SOURCES
    # =====================================================

    sources = [
        github_analysis,
        linkedin_analysis,
        portfolio_analysis
    ]

    available_sources = [
        source
        for source in sources
        if source.get("url")
    ]

    # =====================================================
    # 7. EVIDENCE LEVEL
    # =====================================================

    if len(available_sources) >= 2:

        evidence_level = "Good"

    elif len(available_sources) == 1:

        evidence_level = "Limited"

    else:

        evidence_level = "Insufficient"

    # =====================================================
    # 8. OVERALL ASSESSMENT
    # =====================================================

    if match_percentage >= 80:

        overall_assessment = (
            "Strong potential match"
        )

    elif match_percentage >= 60:

        overall_assessment = (
            "Moderate potential match"
        )

    elif match_percentage >= 40:

        overall_assessment = (
            "Partial match"
        )

    else:

        overall_assessment = (
            "Low requirement match"
        )

    # =====================================================
    # 9. SEND ANALYSIS TO RESULT PAGE
    # =====================================================

    return render_template(
        "analysis_result.html",

        candidate=candidate,

        job=job,

        matched_skills=matched_skills,

        missing_skills=missing_skills,

        match_percentage=match_percentage,

        github_analysis=github_analysis,

        linkedin_analysis=linkedin_analysis,

        portfolio_analysis=portfolio_analysis,

        available_sources=available_sources,

        evidence_level=evidence_level,

        overall_assessment=overall_assessment
    )


# =========================================================
# INITIALIZE DATABASE
# =========================================================

init_db()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
      )
