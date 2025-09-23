import gradio as gr
import socket
from utils.audio_utils import text_to_speech
from utils.analysis_utils import analyze_pronunciation
from models.models import db, User, PracticeSession, PhonemeDetail

# Global variable to store Flask app instance
app = None

def get_default_user():
    """Get the first user from the database to use as default."""
    try:
        with app.app_context():
            user = User.query.first()
            return user.id if user else None
    except Exception as e:
        print(f"Error getting default user: {str(e)}")
        return None

def find_free_port(start_port=7861, max_attempts=100):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    raise OSError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")

# Predefined phrases
CUSTOM_PHRASE_OPTION = "[ Type a custom phrase ]"
PREDEFINED_PHRASES = [
    CUSTOM_PHRASE_OPTION,
    "Hello, how are you today?",
    "Thank you for your help.",
    "The weather is beautiful."
]

def play_phrase(phrase):
    """Generate TTS audio for the phrase."""
    if phrase:
        audio_file = text_to_speech(phrase)
        return audio_file, "Audio generated. Listen above."
    return None, "No phrase selected."

def save_practice_session(phrase, result, user_id):
    """Save the practice session to database."""
    global app
    
    if user_id is None or app is None:
        return False
        
    with app.app_context():
        try:
            user = db.session.get(User, user_id)
            if not user:
                print(f"Warning: Could not find user with ID {user_id}")
                return False
                
            practice_session = PracticeSession(
                user_id=user.id,
                target_phrase=phrase,
                spoken_phrase=result.get('transcript', ''),
                overall_score=result['scores']['overall'],
                word_accuracy=result['scores']['word_accuracy'],
                phoneme_accuracy=result['scores']['phoneme_accuracy'],
                completeness_score=result['scores']['completeness']
            )
            
            db.session.add(practice_session)
            db.session.flush()
            
            if result['feedback']['phoneme_issues']:
                for issue in result['feedback']['phoneme_issues']:
                    phoneme_detail = PhonemeDetail(
                        session_id=practice_session.id,
                        target_phoneme=issue.get('target_phoneme', ''),
                        spoken_phoneme=issue.get('spoken_phoneme', ''),
                        is_correct=False
                    )
                    db.session.add(phoneme_detail)
                    
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False

def format_detailed_feedback(result):
    """Format the analysis result into detailed feedback."""
            def get_default_user(flask_app):
                """Get the first user from the database to use as default."""
                with flask_app.app_context():
                    user = User.query.first()
                    return user.id if user else None
        feedback += f"Overall Score: {result['scores']['overall']:.1f}%\n\n"
        
        feedback += "Detailed Scores:\n"
        feedback += f"* Word Accuracy: {result['scores']['word_accuracy']:.1f}%\n"
        feedback += f"* Phoneme Accuracy: {result['scores']['phoneme_accuracy']:.1f}%\n"
        feedback += f"* Completeness: {result['scores']['completeness']:.1f}%\n\n"
        
        safe_transcript = ''.join(c for c in result['transcript'] if ord(c) < 128)
        feedback += f"Your pronunciation: {safe_transcript}\n\n"
        
        feedback += f"Feedback: {result['feedback']['general_feedback']}\n\n"
        
        if result['feedback']['improvement_tips']:
            feedback += "Improvement Tips:\n"
                safe_tip = ''.join(c for c in tip if ord(c) < 128)
                feedback += f"* {safe_tip}\n"
                
        if result['feedback']['phoneme_issues']:
            feedback += "\nSound Improvements:\n"
            for issue in result['feedback']['phoneme_issues']:
                safe_tip = ''.join(c for c in issue['tip'] if ord(c) < 128)
                feedback += f"* {safe_tip}\n"
                
        return feedback
    except Exception as e:
        return f"Error formatting feedback: {str(e)}"

def process_audio(phrase, audio, user_id):
    """Process the recorded audio and provide feedback."""
    global app
    
    if not phrase:
        return "Please select or enter a phrase first."
    if audio is None:
        return "Please record your audio."
    
    # If no user_id provided, try to get the default user
    if user_id is None and app:
        with app.app_context():
            user_id = get_default_user()

    import os
    import wave
    import tempfile

    # Handle tuple of (sample_rate, numpy_array)
    if isinstance(audio, tuple) and len(audio) == 2:
        sample_rate, audio_data = audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_path = temp_file.name
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
        audio_path = temp_path
    else:
        if isinstance(audio, str):
            audio_path = audio
        elif isinstance(audio, dict) and ('path' in audio or 'name' in audio):
            audio_path = audio.get('path') or audio.get('name')
        else:
            return "Error: Unsupported audio format"

    if not audio_path or not os.path.exists(audio_path):
        return "Error: Audio file path is invalid or does not exist"

    try:
        result = analyze_pronunciation(phrase, audio_path)
        
        if audio_path.endswith('.wav') and tempfile.gettempdir() in audio_path:
            try:
                os.remove(audio_path)
            except:
                pass
        
        if not result['success']:
            return "Error analyzing pronunciation. Please try again."
            
        feedback = format_detailed_feedback(result)
        
        # Save to database if we have a user_id
        if user_id:
            result['target_phrase'] = phrase
            if save_practice_session(phrase, result, user_id):
                feedback += "\n\nPractice session saved successfully!"
            else:
                feedback += "\n\nWarning: Failed to save practice session."
        else:
            feedback += "\n\nNote: Practice session not saved (not logged in)."
            
        return feedback
        
    except Exception as e:
        return f"Error during analysis: {str(e)}"

def create_interface(user_id):
    with gr.Blocks() as interface:
        gr.Markdown("# Pronunciation Practice")
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
        result_output = gr.Textbox(label="Feedback", lines=10)

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

        phrase_dropdown.change(on_dropdown_select, inputs=[phrase_dropdown], outputs=[phrase_input])
        play_btn.click(
            lambda x, y: play_phrase(get_active_phrase(x, y)), 
            inputs=[phrase_input, phrase_dropdown], 
            outputs=[audio_player, play_output]
        )
        submit_btn.click(
            lambda x, y, z: process_audio(get_active_phrase(x, y), z, user_id), 
            inputs=[phrase_input, phrase_dropdown, audio_recorder], 
            outputs=result_output
        )

    return interface

def launch_server(flask_app=None, current_user=None):
    """Launch the Gradio server on a free port."""
    try:
        global app
        app = flask_app
        
        port = find_free_port()
        # Use the default user if no user is provided
        user_id = None
        if app:
            with app.app_context():
                user_id = current_user.id if current_user and current_user.is_authenticated else get_default_user()
        
        interface = create_interface(user_id)
            # Export a mountable Gradio app for Flask
            def get_gradio_app(flask_app, current_user=None):
                user_id = None
                with flask_app.app_context():
                    user_id = current_user.id if current_user and getattr(current_user, 'is_authenticated', False) else get_default_user(flask_app)
                return create_interface(user_id, flask_app)
        interface.launch(
            server_name="0.0.0.0",
            server_port=port,
            share=False,
            prevent_thread_lock=True
        )
        print(f"Gradio server started on port {port}")
        return port
    except Exception as e:
        print(f"Error launching Gradio server: {str(e)}")
        return None

if __name__ == "__main__":
    launch_server()
