import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# --------------------------------
# Flask setup
# --------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)

# --------------------------------
# Models
# --------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class PracticeSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    target_phrase = db.Column(db.String(200), nullable=False)
    spoken_phrase = db.Column(db.String(200), nullable=True)
    overall_score = db.Column(db.Float, nullable=True)

class PhonemeDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("practice_session.id"), nullable=False)
    target_phoneme = db.Column(db.String(10))
    spoken_phoneme = db.Column(db.String(10))
    is_correct = db.Column(db.Boolean, default=False)

# --------------------------------
# User Loader
# --------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------------
# Routes
# --------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("practice"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("practice"))
        return "Invalid credentials", 401
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/practice")
@login_required
def practice():
    return render_template("mypractice.html", gradio_url="/gradio", user_id=current_user.id, is_authenticated=True)

# --------------------------------
# Heavy ML routes (lazy imports)
# --------------------------------
@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    # 🔹 Import only when route is called
    from utils.analysis_utils import analyze_pronunciation  

    data = request.json
    phrase = data.get("phrase")
    audio_path = data.get("audio_path")

    if not phrase or not audio_path:
        return jsonify({"error": "Missing input"}), 400

    result = analyze_pronunciation(phrase, audio_path)
    return jsonify(result)

# --------------------------------
# Init DB
# --------------------------------
@app.before_request
def create_tables():
    db.create_all()

# --------------------------------
# Entrypoint
# --------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
