from flask import Flask, render_template, request, redirect
import os

app = Flask(__name__)

candidates = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        candidate = {
            "full_name": request.form["full_name"],
            "email": request.form["email"],
            "github_username": request.form["github_username"],
            "portfolio": request.form["portfolio"],
            "job_description": request.form["job_description"]
        }

        candidates.append(candidate)

        return redirect("/candidates")

    return render_template("upload.html")


@app.route("/candidates")
def candidates_page():
    return render_template(
        "store_candidate.html",
        candidates=candidates
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
