
from flask import Flask, render_template, request, redirect
import sqlite3
import re
import requests
from urllib.parse import urlparse
from html import unescape

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
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db_connection()

    # -----------------------------------------------------
    # CANDIDATES
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
    # CHECK OLD CANDIDATE COLUMNS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # JOBS
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

    # -----------------------------------------------------
    # CANDIDATE SOURCES
    # -----------------------------------------------------

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

            FOREIGN KEY (candidate_id)
                REFERENCES candidates(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# HELPER
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = unescape(text)

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# UPLOAD CANDIDATE
# =========================================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        github_username = request.form.get(
            "github_username",
            ""
        ).strip()

        linkedin = request.form.get(
            "linkedin",
            ""
        ).strip()

        portfolio = request.form.get(
            "portfolio",
            ""
        ).strip()

        skills = request.form.get(
            "skills",
            ""
        ).strip()

        experience = request.form.get(
            "experience",
            ""
        ).strip()

        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not full_name:

            return (
                "Full name is required.",
                400
            )

        if not email:

            return (
                "Email is required.",
                400
            )

        # -------------------------------------------------
        # SAVE CANDIDATE
        # -------------------------------------------------

        conn = get_db_connection()

        cursor = conn.execute("""
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

        candidate_id = cursor.lastrowid

        # -------------------------------------------------
        # SAVE SOURCES
        # -------------------------------------------------

        source_urls = [

            github_username,

            linkedin,

            portfolio
        ]

        for url in source_urls:

            if not url:

                continue

            # If user entered github username
            # rather than full URL

            if (
                "github.com" not in url.lower()
                and
                not url.startswith("http")
            ):

                if re.match(
                    r"^[A-Za-z0-9-]+$",
                    url
                ):

                    url = (
                        "https://github.com/"
                        + url
                    )

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

        return redirect(
            "/candidates"
        )

    return render_template(
        "upload.html"
    )


# =========================================================
# CANDIDATES
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

@app.route(
    "/candidate/<int:candidate_id>"
)
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
    """, (
        candidate_id,
    )).fetchone()

    conn.close()

    if candidate is None:

        return (
            "Candidate not found.",
            404
        )

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

    # Delete sources first

    conn.execute("""
        DELETE FROM candidate_sources

        WHERE candidate_id = ?
    """, (
        candidate_id,
    ))

    # Delete candidate

    conn.execute("""
        DELETE FROM candidates

        WHERE id = ?
    """, (
        candidate_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        "/candidates"
    )


# =========================================================
# CREATE JOB
# =========================================================

@app.route(
    "/create-job",
    methods=["GET", "POST"]
)
def create_job():

    if request.method == "POST":

        job_title = request.form.get(
            "job_title",
            ""
        ).strip()

        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        required_skills = request.form.get(
            "required_skills",
            ""
        ).strip()

        if not job_title:

            return (
                "Job title is required.",
                400
            )

        if not job_description:

            return (
                "Job description is required.",
                400
            )

        if not required_skills:

            return (
                "Required skills are required.",
                400
            )

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

        return redirect(
            "/jobs"
        )

    return render_template(
        "create_job.html"
    )


# =========================================================
# JOBS
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
# GITHUB ANALYSIS
# =========================================================

def analyze_github_url(url):

    parsed = urlparse(url)

    parts = [

        part

        for part
        in parsed.path.strip("/").split("/")

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
            "confidence": "Low",
            "repositories": []
        }

    username = parts[0]

    api_base = (
        "https://api.github.com"
    )

    headers = {

        "Accept":
            "application/vnd.github+json",

        "User-Agent":
            "AI-Candidate-Intelligence/1.0"
    }

    try:

        # -------------------------------------------------
        # PROFILE
        # -------------------------------------------------

        profile_response = requests.get(

            f"{api_base}/users/{username}",

            headers=headers,

            timeout=10
        )

        if profile_response.status_code != 200:

            return {

                "url": url,

                "type": "github",

                "status":
                    f"GitHub HTTP "
                    f"{profile_response.status_code}",

                "title": "",

                "description": "",

                "technologies": [],

                "evidence": [
                    "GitHub profile could not be retrieved."
                ],

                "confidence": "Low",

                "repositories": []
            }

        profile = (
            profile_response.json()
        )

        # -------------------------------------------------
        # REPOSITORIES
        # -------------------------------------------------

        repos_response = requests.get(

            f"{api_base}/users/"
            f"{username}/repos",

            params={

                "per_page": 100,

                "sort": "updated"
            },

            headers=headers,

            timeout=10
        )

        repositories = []

        if repos_response.status_code == 200:

            repositories = (
                repos_response.json()
            )

        # -------------------------------------------------
        # ANALYZE REPOSITORIES
        # -------------------------------------------------

        languages = set()

        technologies = set()

        repository_evidence = []

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

        for repo in repositories:

            language = (
                repo.get("language")
                or ""
            )

            if language:

                languages.add(
                    language
                )

            repo_name = (
                repo.get("name")
                or ""
            )

            repo_description = (
                repo.get("description")
                or ""
            )

            searchable = (

                repo_name
                + " "
                + repo_description
                + " "
                + language

            ).lower()

            for technology in (
                technology_keywords
            ):

                if technology.lower() in searchable:

                    technologies.add(
                        technology
                    )

            repository_evidence.append({

                "name":
                    repo_name,

                "description":
                    repo_description,

                "language":
                    language or "Unknown",

                "stars":
                    repo.get(
                        "stargazers_count",
                        0
                    ),

                "forks":
                    repo.get(
                        "forks_count",
                        0
                    ),

                "html_url":
                    repo.get(
                        "html_url"
                    ),

                "updated_at":
                    repo.get(
                        "updated_at"
                    )
            })

        # Add detected languages

        for language in languages:

            technologies.add(
                language
            )

        # -------------------------------------------------
        # EVIDENCE
        # -------------------------------------------------

        evidence = [

            f"GitHub username: {username}",

            (
                "Public repositories found: "
                f"{len(repositories)}"
            ),

            (
                "Public followers: "
                f"{profile.get('followers', 0)}"
            ),

            (
                "Public following: "
                f"{profile.get('following', 0)}"
            )
        ]

        if profile.get("bio"):

            evidence.append(
                "GitHub bio: "
                + profile["bio"]
            )

        if languages:

            evidence.append(

                "Repository languages: "
                + ", ".join(
                    sorted(languages)
                )
            )

        if technologies:

            evidence.append(

                "Detected technologies: "
                + ", ".join(
                    sorted(technologies)
                )
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

            "title":
                profile.get("name")
                or username,

            "description":
                profile.get("bio")
                or "",

            "technologies":
                sorted(technologies),

            "evidence":
                evidence,

            "repositories":
                repository_evidence,

            "confidence":
                confidence
        }

    except requests.RequestException as e:

        return {

            "url": url,

            "type": "github",

            "status":
                "GitHub request failed",

            "title": "",

            "description": "",

            "technologies": [],

            "evidence": [
                str(e)
            ],

            "confidence": "Low",

            "repositories": []
        }


# =========================================================
# WEBSITE ANALYSIS
# =========================================================

def analyze_website(url):

    try:

        response = requests.get(

            url,

            timeout=10,

            headers={

                "User-Agent":
                    "Mozilla/5.0 "
                    "AI-Candidate-Intelligence/1.0"
            }
        )

        if response.status_code != 200:

            return {

                "url": url,

                "type": "website",

                "status":
                    f"HTTP {response.status_code}",

                "title": "",

                "description": "",

                "technologies": [],

                "evidence": [

                    (
                        "Website returned HTTP "
                        f"{response.status_code}."
                    )
                ],

                "confidence": "Low",

                "repositories": []
            }

        html = response.text

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------

        title = ""

        title_match = re.search(

            r"<title[^>]*>"
            r"(.*?)"
            r"</title>",

            html,

            re.IGNORECASE | re.DOTALL
        )

        if title_match:

            title = clean_text(
                title_match.group(1)
            )

        # -------------------------------------------------
        # META DESCRIPTION
        # -------------------------------------------------

        description = ""

        description_match = re.search(

            r'<meta[^>]+'
            r'name=["\']description["\']'
            r'[^>]+'
            r'content=["\'](.*?)["\']',

            html,

            re.IGNORECASE | re.DOTALL
        )

        if description_match:

            description = clean_text(
                description_match.group(1)
            )

        # -------------------------------------------------
        # TECHNOLOGY DETECTION
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

            "api",
            "rest",
            "graphql"
        ]

        searchable_text = (
            html.lower()
        )

        technologies = []

        for technology in (
            technology_keywords
        ):

            if technology.lower() in searchable_text:

                technologies.append(
                    technology
                )

        # -------------------------------------------------
        # EVIDENCE
        # -------------------------------------------------

        evidence = [

            "Public webpage successfully accessed.",

            (
                "Page size: "
                f"{len(html)} characters."
            )
        ]

        if title:

            evidence.append(
                "Page title: "
                + title
            )

        if description:

            evidence.append(
                "Page description: "
                + description
            )

        if technologies:

            evidence.append(

                "Detected technologies: "
                + ", ".join(
                    sorted(set(technologies))
                )
            )

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        if title and technologies:

            confidence = "High"

        elif title or technologies:

            confidence = "Medium"

        else:

            confidence = "Low"

        return {

            "url": url,

            "type": "website",

            "status": "analyzed",

            "title": title,

            "description": description,

            "technologies":
                sorted(set(technologies)),

            "evidence": evidence,

            "confidence": confidence,

            "repositories": []
        }

    except requests.RequestException as e:

        return {

            "url": url,

            "type": "website",

            "status":
                "Website request failed",

            "title": "",

            "description": "",

            "technologies": [],

            "evidence": [
                str(e)
            ],

            "confidence": "Low",

            "repositories": []
        }


# =========================================================
# GENERIC URL ANALYSIS
# =========================================================

def analyze_url(url):

    if not url:

        return {

            "url": "",

            "type": "unknown",

            "status": "not provided",

            "title": "",

            "description": "",

            "technologies": [],

            "evidence": [],

            "confidence": "None",

            "repositories": []
        }

    url = url.strip()

    parsed = urlparse(url)

    if (

        parsed.scheme
        not in ("http", "https")

        or not parsed.netloc

    ):

        return {

            "url": url,

            "type": "invalid",

            "status": "invalid URL",

            "title": "",

            "description": "",

            "technologies": [],

            "evidence": [],

            "confidence": "None",

            "repositories": []
        }

    hostname = (
        parsed.netloc.lower()
    )

    # -----------------------------------------------------
    # GITHUB
    # -----------------------------------------------------

    if "github.com" in hostname:

        return analyze_github_url(
            url
        )

    # -----------------------------------------------------
    # LINKEDIN
    # -----------------------------------------------------

    if "linkedin.com" in hostname:

        return {

            "url": url,

            "type": "linkedin",

            "status":
                "profile URL supplied",

            "title":
                "LinkedIn profile",

            "description": "",

            "technologies": [],

            "evidence": [

                "Candidate supplied a LinkedIn profile URL.",

                (
                    "LinkedIn profile content was "
                    "not independently scraped."
                )
            ],

            "confidence": "Limited",

            "repositories": []
        }

    # -----------------------------------------------------
    # OTHER WEBSITE
    # -----------------------------------------------------

    return analyze_website(
        url
    )


# =========================================================
# SAVE SOURCE ANALYSIS
# =========================================================

def save_source_analysis(
    candidate_id,
    source_id,
    analysis
):

    technologies = ", ".join(
        analysis.get(
            "technologies",
            []
        )
    )

    evidence = "\n".join(
        analysis.get(
            "evidence",
            []
        )
    )

    conn = get_db_connection()

    conn.execute("""
        UPDATE candidate_sources

        SET

            source_type = ?,

            status = ?,

            title = ?,

            description = ?,

            technologies = ?,

            evidence = ?

        WHERE

            id = ?

        AND

            candidate_id = ?
    """, (

        analysis.get(
            "type",
            "unknown"
        ),

        analysis.get(
            "status",
            "unknown"
        ),

        analysis.get(
            "title",
            ""
        ),

        analysis.get(
            "description",
            ""
        ),

        technologies,

        evidence,

        source_id,

        candidate_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# CANDIDATE ANALYSIS
# =========================================================

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
        SELECT *

        FROM candidates

        WHERE id = ?
    """, (
        candidate_id,
    )).fetchone()

    if candidate is None:

        conn.close()

        return (
            "Candidate not found.",
            404
        )

    # =====================================================
    # GET JOBS
    # =====================================================

    jobs = conn.execute("""
        SELECT *

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
    # GET
    # =====================================================

    if request.method == "GET":

        return render_template(

            "analyze_candidate.html",

            candidate=candidate,

            jobs=jobs
        )

    # =====================================================
    # SELECT JOB
    # =====================================================

    job_id = request.form.get(
        "job_id"
    )

    if not job_id:

        return (
            "Please select a job.",
            400
        )

    conn = get_db_connection()

    job = conn.execute("""
        SELECT *

        FROM jobs

        WHERE id = ?
    """, (
        job_id,
    )).fetchone()

    conn.close()

    if job is None:

        return (
            "Job not found.",
            404
        )

    # =====================================================
    # GET CANDIDATE SOURCES
    # =====================================================

    conn = get_db_connection()

    source_rows = conn.execute("""
        SELECT *

        FROM candidate_sources

        WHERE candidate_id = ?

        ORDER BY id
    """, (
        candidate_id,
    )).fetchall()

    conn.close()

    # =====================================================
    # ANALYZE EVERY SOURCE
    # =====================================================

    analyzed_sources = []

    for source in source_rows:

        analysis = analyze_url(
            source["url"]
        )

        save_source_analysis(

            candidate_id,

            source["id"],

            analysis
        )

        analysis["id"] = (
            source["id"]
        )

        analyzed_sources.append(
            analysis
        )

    # =====================================================
    # PREPARE REQUIRED SKILLS
    # =====================================================

    required_skills = [

        skill.strip().lower()

        for skill
        in job["required_skills"].split(",")

        if skill.strip()
    ]

    # =====================================================
    # BUILD COMPLETE CANDIDATE EVIDENCE
    # =====================================================

    candidate_parts = [

        candidate["full_name"]
        or "",

        candidate["skills"]
        or "",

        candidate["experience"]
        or "",

        candidate["job_description"]
        or ""
    ]

    # Add source evidence

    for source in analyzed_sources:

        candidate_parts.append(

            source.get(
                "title",
                ""
            )
        )

        candidate_parts.append(

            source.get(
                "description",
                ""
            )
        )

        candidate_parts.extend(

            source.get(
                "technologies",
                []
            )
        )

        candidate_parts.extend(

            source.get(
                "evidence",
                []
            )
        )

        # GitHub repository evidence

        for repo in source.get(
            "repositories",
            []
        ):

            candidate_parts.append(

                repo.get(
                    "name",
                    ""
                )
            )

            candidate_parts.append(

                repo.get(
                    "description",
                    ""
                )
            )

            candidate_parts.append(

                repo.get(
                    "language",
                    ""
                )
            )

    candidate_text = " ".join(
        candidate_parts
    ).lower()

    # =====================================================
    # MATCH SKILLS
    # =====================================================

    matched_skills = []

    missing_skills = []

    skill_evidence = {}

    for skill in required_skills:

        # Special normalization

        normalized_skill = (
            skill
            .replace(
                "last api",
                "rest api"
            )
            .strip()
        )

        pattern = (

            r"(?<!\w)"
            + re.escape(
                normalized_skill
            )
            + r"(?!\w)"
        )

        if re.search(
            pattern,
            candidate_text,
            re.IGNORECASE
        ):

            matched_skills.append(
                skill
            )

            skill_evidence[
                skill
            ] = "Found in candidate evidence."

        else:

            missing_skills.append(
                skill
            )

            skill_evidence[
                skill
            ] = "No strong evidence found."

    # =====================================================
    # MATCH PERCENTAGE
    # =====================================================

    if required_skills:

        match_percentage = round(

            (
                len(matched_skills)
                /
                len(required_skills)
            )
            * 100
        )

    else:

        match_percentage = 0

    # =====================================================
    # SOURCE COUNTS
    # =====================================================

    accessible_sources = [

        source

        for source
        in analyzed_sources

        if source.get("status")
        in (
            "analyzed",
            "profile URL supplied"
        )
    ]

    high_confidence_sources = [

        source

        for source
        in analyzed_sources

        if source.get(
            "confidence"
        ) == "High"
    ]

    # =====================================================
    # EVIDENCE LEVEL
    # =====================================================

    if high_confidence_sources:

        evidence_level = "Strong"

    elif accessible_sources:

        evidence_level = "Moderate"

    else:

        evidence_level = "Insufficient"

    # =====================================================
    # OVERALL ASSESSMENT
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
    # SOURCE TECHNOLOGIES
    # =====================================================

    detected_technologies = set()

    for source in analyzed_sources:

        for technology in source.get(
            "technologies",
            []
        ):

            detected_technologies.add(
                technology.lower()
            )

    detected_technologies = sorted(
        detected_technologies
    )

    # =====================================================
    # RESULT PAGE
    # =====================================================

    return render_template(

        "analysis_result.html",

        candidate=candidate,

        job=job,

        matched_skills=matched_skills,

        missing_skills=missing_skills,

        skill_evidence=skill_evidence,

        match_percentage=match_percentage,

        analyzed_sources=analyzed_sources,

        accessible_sources=accessible_sources,

        detected_technologies=
            detected_technologies,

        evidence_level=evidence_level,

        overall_assessment=
            overall_assessment
    )


# =========================================================
# START APP
# =========================================================

init_db()


if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True
    )
