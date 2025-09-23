import os
from flask import Flask, render_template
from flask_login import LoginManager, current_user, login_required
from models.models import db, User
from routes import bp
from auth.routes import auth_bp
from gradio_server import get_gradio_app  # your existing file

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

# Login manager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Register blueprints
app.register_blueprint(bp)
app.register_blueprint(auth_bp, url_prefix='/auth')

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/practice')
@login_required
def practice():
    return render_template(
        'practice.html',
        gradio_url="/gradio",   # Gradio is mounted inside Flask
        user_id=current_user.id,
        is_authenticated=True
    )

# ---- Mount Gradio onto Flask ----
import gradio as gr
with app.app_context():
    gradio_app = get_gradio_app(app, current_user)  # your existing fn
    gr.mount_gradio_app(app, gradio_app, path="/gradio")

# Entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
