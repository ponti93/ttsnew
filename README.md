# Pronunciation App

This is a simple web application for practicing pronunciation using AI analysis.

## Features
- Choose from 3 predefined phrases or input a custom phrase.
- Listen to the correct pronunciation using text-to-speech.
- Record your own pronunciation.
- Get a similarity score and transcribed text as feedback.

## Requirements
- Python 3.10+
- Install dependencies: `pip install -r requirements.txt`

## Usage
1. Run the app: `python app.py`
2. Open the web interface in your browser.
3. Select a phrase and click "Play Phrase".
4. Record your pronunciation using the recorder.
5. Click "Analyze Pronunciation" to get feedback.

## How it Works
- Uses Google Speech Recognition for transcription, with Hugging Face Wav2Vec2 as fallback.
- Compares the transcribed text with the target phrase using SequenceMatcher.
- Provides a similarity score and the transcribed text.

Note: Internet connection required for TTS and potentially for speech recognition if Google API is used.

## Deployment on Render

1. **Push your code to GitHub**
   - Make sure your repo includes all files, especially `requirements.txt`, `render.yaml`, and `.gitignore`.

2. **Create a new Web Service on Render**
   - Go to [Render.com](https://render.com)
   - Click "New Web Service" and connect your GitHub repo
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `python app.py`
   - Add any required environment variables (e.g., `SECRET_KEY`, database URLs)

3. **Database setup**
   - If using PostgreSQL, create a Render PostgreSQL instance and update your connection string in `app.py`.

4. **Accessing the app**
   - Render will expose your Flask app on a public URL. Gradio will run on an internal port and be accessible via iframe in the Flask app.

## Project Structure

- All code is in a single folder for easy deployment.
- Flask serves as the main entry point; Gradio is embedded via iframe.
- Static files and templates are in the `static/` and `templates/` folders.

## Notes
- Only the Flask port is exposed publicly on Render.
- For local development, run `python app.py` and access via `http://localhost:5000`.
