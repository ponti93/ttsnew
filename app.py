from flask import Flask, render_template, flash, redirect, url_for
from flask_login import LoginManager, current_user, login_required
import os
from models.models import db, User, PracticeSession, PhonemeDetail
from gradio_server import launch_server

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:incorrect@localhost/pronunciation_app'
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

# Initialize Gradio server to find a free port
gradio_port = None

def initialize_gradio():
    """Initialize the Gradio server with the current user context."""
    global gradio_port
    try:
        gradio_port = launch_server(app, current_user)
        return gradio_port is not None
    except Exception as e:
        print(f"Error initializing Gradio server: {str(e)}")
        return False

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/practice')
@login_required
def practice():
    global gradio_port
    
    # Initialize Gradio if not already running
    if gradio_port is None:
        if not initialize_gradio():
            flash("Error initializing practice interface", "error")
            return redirect(url_for('index'))
    
    return render_template('practice.html', 
                         gradio_url=f"http://127.0.0.1:{gradio_port}",
                         user_id=current_user.id,
                         is_authenticated=True)

# Gradio Interface


# Global variable to store gradio server port
gradio_port = None

def initialize_gradio():
    global gradio_port
    try:
        gradio_port = launch_server(app, current_user)
        return gradio_port is not None
    except Exception as e:
        print(f"Error initializing Gradio server: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        # Initialize Gradio server
        if not initialize_gradio():
            print("Failed to initialize Gradio server")
            exit(1)
        
       # Use PORT env variable for Render
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
