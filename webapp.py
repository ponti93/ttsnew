from flask import Flask, render_template
from flask_login import LoginManager, login_required
from models.models import db, User
from auth.routes import auth_bp
import gradio as gr
from app import process_audio, play_phrase, PREDEFINED_PHRASES, CUSTOM_PHRASE_OPTION
import threading

def create_app():
    app = Flask(__name__)
    
    # Load config
    app.config.from_pyfile('config.py')
    
    # Initialize database
    db.init_app(app)
    
    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        # Use Session.get() instead of Query.get() for SQLAlchemy 2.0 compatibility
        return db.session.get(User, int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Import and register main blueprint
    from main import init_app as init_main
    init_main(app)
    
    # Create Gradio interface
    interface = gr.Blocks()
    with interface:
        gr.Markdown("# Pronunciation App with AI Analysis")
        gr.Markdown("Select a phrase, listen to it, record your pronunciation, and get feedback.")
        
        with gr.Row():
            phrase_dropdown = gr.Dropdown(
                label="Select Phrase Type",
                choices=PREDEFINED_PHRASES,
                value=CUSTOM_PHRASE_OPTION,
                interactive=True
            )
            
        with gr.Row():
            phrase_input = gr.Textbox(
                label="Phrase to Practice",
                placeholder="Type your custom phrase here",
                value="",
                interactive=True
            )
            
        play_btn = gr.Button("Play Phrase")
        audio_player = gr.Audio(label="Phrase Audio")
        play_output = gr.Textbox(label="Status", interactive=False)
        
        gr.Markdown("### Record Your Pronunciation")
        audio_recorder = gr.Audio(sources="microphone", label="Record here")
        
        submit_btn = gr.Button("Analyze Pronunciation")
        result_output = gr.Textbox(label="Feedback", lines=3)
        
        def get_active_phrase(custom_phrase, dropdown_phrase):
            if dropdown_phrase == CUSTOM_PHRASE_OPTION:
                return custom_phrase.strip() if custom_phrase else ""
            return dropdown_phrase if dropdown_phrase else ""
        
        def on_dropdown_select(dropdown_value):
            if dropdown_value == CUSTOM_PHRASE_OPTION:
                return gr.update(value="")
            elif dropdown_value:
                return gr.update(value=dropdown_value)
            return gr.update()
        
        # Update text box when dropdown changes
        phrase_dropdown.change(on_dropdown_select, inputs=[phrase_dropdown], outputs=[phrase_input])
        
        # Connect buttons to use either custom phrase or dropdown selection
        play_btn.click(
            lambda x, y: play_phrase(get_active_phrase(x, y)), 
            inputs=[phrase_input, phrase_dropdown], 
            outputs=[audio_player, play_output]
        )
        submit_btn.click(
            lambda x, y, z: process_audio(get_active_phrase(x, y), z), 
            inputs=[phrase_input, phrase_dropdown, audio_recorder], 
            outputs=result_output
        )
    
    # Launch Gradio interface in a separate thread
    def launch_gradio():
        interface.launch(
            share=False, 
            server_name="127.0.0.1", 
            server_port=7861, 
            prevent_thread_lock=True,
            auth=None,  # No additional auth needed
            show_api=False  # Hide API docs for security
        )
    
    gradio_thread = threading.Thread(target=launch_gradio)
    gradio_thread.daemon = True
    gradio_thread.start()
    
    # Add route to redirect to Gradio interface
    @app.route('/practice')
    @login_required
    def practice():
        return render_template('practice.html', gradio_url="http://localhost:7861")
    
    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)