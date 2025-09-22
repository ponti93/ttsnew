from gtts import gTTS
import os
import tempfile

def text_to_speech(text, lang='en', speed=1.0):
    """
    Convert text to speech using Tacotron2 and return the file path.
    Args:
        text (str): Text to convert to speech
        lang (str): Language code (currently only 'en' supported)
        speed (float): Speech rate multiplier (0.5 to 2.0)
    Returns:
        str: Path to the generated audio file
    """
    """
    Convert text to speech and return the file path.
    Args:
        text (str): Text to convert to speech
        lang (str): Language code
        speed (float): Speech rate (not used in gTTS currently)
    Returns:
        str: Path to the generated audio file
    """
    tts = gTTS(text=text, lang=lang, slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
        tmp_path = tmp.name
    tts.save(tmp_path)
    return tmp_path
