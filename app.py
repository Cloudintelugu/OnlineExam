from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret_key"  # Change to a strong secret key in production

# Database connection
db = mysql.connector.connect(
    host="ccitdb.c3q08suy01ah.ap-south-2.rds.amazonaws.com",
    user="root",
    password="Admin-1234",  # Replace with your MySQL password
    database="exam_db"       # Replace with your database name
)
cursor = db.cursor(dictionary=True)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_user():
    email = request.form["email"]
    password = request.form["password"]

    # Validate user credentials
    cursor.execute("SELECT * FROM students WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone()

    if user:
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("index"))
    else:
        return render_template("login.html", error="Invalid email or password")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    # Check if email already exists
    cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
    student = cursor.fetchone()

    if student:
        return render_template("signup.html", error="Email already exists. Please use a different email.")

    # Insert new student into the database
    cursor.execute(
        "INSERT INTO students (name, email, password) VALUES (%s, %s, %s)",
        (name, email, password)
    )
    db.commit()

    return redirect(url_for("login"))



@app.route("/exam")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Fetch all questions from the database
    cursor.execute("SELECT id, question, option_a, option_b, option_c, option_d FROM questions")
    questions = cursor.fetchall()
    return render_template("exam.html", questions=questions, user_name=session["user_name"])

@app.route("/submit", methods=["POST"])
def submit():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    score = 0
    results = []

    # Fetch correct answers from the database
    cursor.execute("SELECT id, question, correct_answer, option_a, option_b, option_c, option_d FROM questions")
    correct_answers = cursor.fetchall()

    # Compare submitted answers with correct answers
    for question in correct_answers:
        user_answer = request.form.get(f"q{question['id']}")
        is_correct = user_answer == question["correct_answer"]

        if is_correct:
            score += 1

        # Store results for feedback
        results.append({
            "question": question["question"],
            "correct_answer": question[f"option_{question['correct_answer'].lower()}"],
            "user_answer": question[f"option_{user_answer.lower()}"] if user_answer else "No Answer",
            "is_correct": is_correct
        })

    # Save result to the database
    cursor.execute(
        "INSERT INTO student_scores (id, score) VALUES (%s, %s)",
        (user_id, score)
    )
    db.commit()

    # Render results page with feedback
    return render_template("results.html", name=session["user_name"], score=score, total=len(correct_answers), results=results)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
