# AI Candidate Intelligence

AI Candidate Intelligence is a web application that helps recruiters evaluate candidates against a specific job requirement.

## 🎯 Problem

Recruiters often need to manually compare:

- Candidate skills
- Experience
- Job requirements
- GitHub profiles
- LinkedIn profiles
- Portfolio websites

This can take significant time when screening many candidates.

## 🚀 What It Does

The application allows a recruiter to:

- Upload candidate information
- Store candidate profiles
- Create job requirements
- Select a job for analysis
- Compare candidate skills against required skills
- Detect matched and missing skills
- Analyze candidate-provided GitHub, LinkedIn and portfolio links
- Produce an evidence-based candidate analysis

## 📸 Candidate Analysis

![Candidate Analysis](screenshot.png)

The analysis currently provides:

- Overall requirement match
- Matched skills
- Missing/unclear skills
- Candidate information
- Source availability
- GitHub/LinkedIn/portfolio source detection
- Job requirements
- Overall assessment

## 🧠 Analysis Pipeline

Candidate
↓
Candidate profile
↓
Job requirements
↓
Required skill extraction
↓
Candidate evidence extraction
↓
Skill matching
↓
External source detection
↓
Evidence assessment
↓
Candidate analysis

## 🛠️ Tech Stack

- Python
- Flask
- SQLite
- HTML
- CSS
- Jinja2
- Requests
- Gunicorn

## 🌐 Live Demo

[Open the deployed application](https://ai-candidate-intelligence.onrender.com)

## 💻 Core Engineering

The backend handles:

- Database creation and migration
- Candidate storage
- Job storage
- Candidate/job matching
- URL detection
- Public website requests
- Evidence generation
- Analysis result rendering

## 🔍 Current Limitation

The current version performs rule-based analysis and public-source detection.

GitHub and LinkedIn profiles are currently identified as candidate-provided sources rather than fully analyzed.

Future versions can add deeper public-source analysis, structured GitHub repository analysis, project/technology extraction, and stronger evidence scoring.

## 📈 Future Direction

The long-term goal is to move from simple keyword matching toward evidence-based candidate intelligence.

Instead of only asking:

"Does the candidate mention Python?"

the system should eventually ask:

"Does the candidate provide credible evidence that they have actually used Python, where was it used, how substantial was the work, and how relevant is it to this job?"

## 👩‍💻 Built By

Sovana Ruhani

Backend-focused developer building practical software products with Python, Flask and SQL.
