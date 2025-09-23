from flask import Flask, render_template, flash, redirect, url_for
from flask_login import LoginManager, current_user, login_required
import os
from models.models import db, User, PracticeSession, PhonemeDetail
from gradio_server import get_gradio_app

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'  # type: ignore
db.init_app(app)

# Register blueprints
from routes import bp
from auth.routes import auth_bp

app.register_blueprint(bp)
app.register_blueprint(auth_bp, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/practice')
@login_required
def practice():
    return render_template('practice.html', 
                         gradio_url=url_for('gradio_app'),
                         user_id=current_user.id,
                         is_authenticated=True)


# Mount Gradio as a Flask route
from flask import Response
gradio_app = get_gradio_app(app, current_user)
@app.route('/gradio')
def gradio_app_route():
    return Response(gradio_app.run(), mimetype="text/html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
