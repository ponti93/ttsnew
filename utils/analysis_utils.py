import difflib
import speech_recognition as sr
from transformers import pipeline
import epitran
import pandas as pd
import numpy as np

def get_phoneme_analysis(text, transcript):
    """
    Analyze pronunciation at the phoneme level.
    Returns detailed phoneme comparison and scores.
    """
    try:
        epi = epitran.Epitran('eng-Latn')
        
        # Clean and normalize input text
        def clean_text(input_text):
            if not isinstance(input_text, str):
                return ""
            # Remove non-alphabetic characters except spaces
            cleaned = ''.join(c for c in input_text.lower() if c.isalpha() or c.isspace())
            # Remove multiple spaces
            cleaned = ' '.join(cleaned.split())
            return cleaned
        
        cleaned_text = clean_text(text)
        cleaned_transcript = clean_text(transcript)
        
        if not cleaned_text or not cleaned_transcript:
            return pd.DataFrame({'target': [], 'spoken': [], 'correct': []})
        
        # Get phonemes for both target and spoken text
        target_phonemes = epi.transliterate(cleaned_text)
        spoken_phonemes = epi.transliterate(cleaned_transcript)
        
        # Ensure we have phonemes to compare
        if not target_phonemes or not spoken_phonemes:
            return pd.DataFrame({'target': [], 'spoken': [], 'correct': []})
        
        # Compare phonemes
        phoneme_scores = []
        max_len = max(len(target_phonemes), len(spoken_phonemes))
        
        # Pad shorter sequence with spaces to match lengths
        target_phonemes = target_phonemes.ljust(max_len)
        spoken_phonemes = spoken_phonemes.ljust(max_len)
        
        for t_ph, s_ph in zip(target_phonemes, spoken_phonemes):
            score = 1 if t_ph == s_ph else 0
            phoneme_scores.append({
                'target': t_ph,
                'spoken': s_ph,
                'correct': score
            })
        
        df = pd.DataFrame(phoneme_scores)
        # Ensure we have a valid score column
        if 'correct' not in df.columns or df.empty:
            df = pd.DataFrame({'target': [], 'spoken': [], 'correct': []})
            
        return df
    except Exception as e:
        print(f"Phoneme analysis error: {str(e)}")
        return pd.DataFrame({'target': [], 'spoken': [], 'correct': []})

def get_phoneme_feedback(phoneme_df):
    """
    Generate specific feedback for phoneme mistakes.
    """
    mistakes = phoneme_df[phoneme_df['correct'] == 0]
    feedback = []
    
    for _, row in mistakes.iterrows():
        feedback.append({
            'target_phoneme': row['target'],
            'spoken_phoneme': row['spoken'],
            'tip': f"Try to pronounce '{row['target']}' instead of '{row['spoken']}'"
        })
    
    return feedback

def similarity_score(target_text: str, user_text: str) -> dict:
    """
    Enhanced similarity scoring with multiple metrics.
    
    Args:
        target_text (str): The expected text
        user_text (str): The actual spoken text
        
    Returns:
        dict: Detailed scoring information
    """
    # Input validation
    if not isinstance(target_text, str) or not isinstance(user_text, str):
        return {
            'overall_score': 0.0,
            'word_level_score': 0.0,
            'phoneme_score': 0.0,
            'completeness_score': 0.0,
            'phoneme_details': []
        }
    
    # Word-level similarity
    try:
        word_score = difflib.SequenceMatcher(None, 
            target_text.lower(), 
            user_text.lower()
        ).ratio()
    except Exception:
        word_score = 0.0
    
    # Phoneme-level analysis
    phoneme_df = get_phoneme_analysis(target_text, user_text)
    if phoneme_df.empty or 'correct' not in phoneme_df.columns:
        phoneme_score = 0.0
    else:
        phoneme_score = float(phoneme_df['correct'].mean()) if not pd.isna(phoneme_df['correct'].mean()) else 0.0
    
    # Word count comparison
    try:
        target_words = len(target_text.split())
        spoken_words = len(user_text.split())
        completeness_score = min(spoken_words / target_words if target_words > 0 else 0, 1.0)
    except Exception:
        completeness_score = 0.0
    
    # Calculate overall score, handling any remaining NaN values
    scores = [word_score, phoneme_score, completeness_score]
    valid_scores = [s for s in scores if not pd.isna(s)]
    overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    
    return {
        'overall_score': round(float(overall_score), 2),
        'word_level_score': round(float(word_score), 2),
        'phoneme_score': round(float(phoneme_score), 2),
        'completeness_score': round(float(completeness_score), 2),
        'phoneme_details': get_phoneme_feedback(phoneme_df)
    }

def transcribe_audio_google(audio_file: str) -> str:
    """
    Transcribe audio using Google Speech Recognition.
    Args:
        audio_file: path to audio file (will be converted to WAV if needed)
    Returns:
        str: Transcribed text or error message
    """
    import os
    from pydub import AudioSegment
    
    try:
        # Convert audio to WAV if it's not already
        file_ext = os.path.splitext(audio_file)[1].lower()
        if file_ext != '.wav':
            try:
                if file_ext == '.ogg':
                    audio = AudioSegment.from_ogg(audio_file)
                elif file_ext == '.mp3':
                    audio = AudioSegment.from_mp3(audio_file)
                else:
                    audio = AudioSegment.from_file(audio_file)
                
                wav_path = os.path.splitext(audio_file)[0] + '.wav'
                audio.export(wav_path, format='wav')
                audio_file = wav_path
            except Exception as e:
                return f"Audio conversion error: {str(e)}"

        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Record from wav file
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            
        try:
            # Use Google Speech Recognition
            text = recognizer.recognize_google(audio_data)  # type: ignore
            return text.lower()
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError:
            return "Service unavailable"
            
    except Exception as e:
        return f"Audio processing error: {str(e)}"

def transcribe_audio_huggingface(audio_file: str) -> str:
    """
    Transcribe audio using Hugging Face Wav2Vec2 as offline alternative.
    Args:
        audio_file: Path to audio file
    Returns:
        str: Transcribed text or error message
    """
    try:
        import os
        from pydub import AudioSegment
        from typing import Dict, Any, Union, List
        
        # Convert audio to WAV if it's not already
        file_ext = os.path.splitext(audio_file)[1].lower()
        if file_ext != '.wav':
            try:
                if file_ext == '.ogg':
                    audio = AudioSegment.from_ogg(audio_file)
                elif file_ext == '.mp3':
                    audio = AudioSegment.from_mp3(audio_file)
                else:
                    audio = AudioSegment.from_file(audio_file)
                
                wav_path = os.path.splitext(audio_file)[0] + '.wav'
                audio.export(wav_path, format='wav')
                audio_file = wav_path
            except Exception as e:
                return f"Audio conversion error: {str(e)}"

        # Load pre-trained Wav2Vec2 model for speech recognition
        speech_recognizer = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-base-960h")  # type: ignore
        result: Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]] = speech_recognizer(audio_file)
        
        # Handle different types of output from the model
        transcript: str
        if isinstance(result, dict) and 'text' in result:
            transcript = str(result['text'])
        elif isinstance(result, str):
            transcript = result
        elif isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict) and 'text' in result[0]:
                transcript = str(result[0]['text'])
            else:
                transcript = str(result[0])
        else:
            return "Could not understand audio"
            
        return transcript.lower() if transcript else "Could not understand audio"
    except Exception as e:
        return f"Hugging Face transcription error: {str(e)}"

def analyze_pronunciation(target_text: str, audio_path: str) -> dict:
    """
    Enhanced pronunciation analysis with detailed feedback.
    Returns comprehensive analysis of pronunciation quality.
    
    Args:
        target_text (str): The text that should have been spoken
        audio_path (str): Path to the audio file
        
    Returns:
        dict: Analysis results including scores and feedback
    """
    from typing import Dict, Any, Optional, List

    def create_error_response(error_msg: str, transcript: Optional[str] = None) -> Dict[str, Any]:
        return {
            'success': False,
            'error': error_msg,
            'transcript': transcript,
            'scores': None
        }
    
    try:
        # Input validation
        if not target_text or not audio_path:
            return create_error_response("Missing required input: target text or audio path")
        
        # Get transcript
        transcript = transcribe_audio_google(audio_path)
        
        # Check for transcription errors
        if not isinstance(transcript, str):
            return create_error_response("Invalid transcription result")
            
        if "Could not understand" in transcript or "Service unavailable" in transcript:
            # Fall back to Hugging Face
            transcript = transcribe_audio_huggingface(audio_path)
            
            if not isinstance(transcript, str) or "error" in transcript.lower() or "could not understand" in transcript.lower():
                return create_error_response(str(transcript))
    
        # Get detailed analysis
        try:
            analysis: Dict[str, Any] = similarity_score(target_text, transcript)
        except Exception as e:
            return create_error_response(f"Analysis error: {str(e)}", transcript)
        
        # Create success response
        feedback: Dict[str, Any] = {
            'success': True,
            'transcript': transcript,
            'scores': {
                'overall': round(analysis['overall_score'] * 100, 2),  # Convert to percentage
                'word_accuracy': round(analysis['word_level_score'] * 100, 2),
                'phoneme_accuracy': round(analysis['phoneme_score'] * 100, 2),
                'completeness': round(analysis['completeness_score'] * 100, 2)
            },
            'feedback': {
                'phoneme_issues': analysis['phoneme_details'],
                'general_feedback': get_general_feedback(analysis['overall_score']),
                'improvement_tips': get_improvement_tips(analysis)
            }
        }
        
        return feedback
        
    except Exception as e:
        return create_error_response(f"Unexpected error: {str(e)}")

def get_general_feedback(score: float) -> str:
    """
    Generate general feedback based on overall score
    
    Args:
        score (float): Overall pronunciation score between 0 and 1
        
    Returns:
        str: General feedback message
    """
    # Input validation
    if not isinstance(score, (int, float)):
        return "Invalid score provided"
        
    score = float(score)  # Convert to float if integer
    
    if score < 0 or score > 1:
        return "Score must be between 0 and 1"
        
    if score >= 0.9:
        return "Excellent pronunciation! Keep up the great work!"
    elif score >= 0.7:
        return "Good pronunciation. Some minor improvements possible."
    elif score >= 0.5:
        return "Fair pronunciation. Focus on the suggested improvements."
    else:
        return "Keep practicing! Focus on pronouncing each word clearly."

def get_improvement_tips(analysis: dict) -> list:
    """
    Generate specific improvement tips based on analysis
    
    Args:
        analysis (dict): Analysis results containing scores
        
    Returns:
        list: List of improvement tips
    """
    from typing import List
    
    tips: List[str] = []
    
    try:
        # Validate required keys exist
        required_keys = ['word_level_score', 'phoneme_score', 'completeness_score']
        for key in required_keys:
            if key not in analysis:
                raise KeyError(f"Missing required key: {key}")
        
        # Add specific tips based on scores
        if analysis['word_level_score'] < 0.7:
            tips.append("Practice saying each word separately first")
        
        if analysis['phoneme_score'] < 0.7:
            tips.append("Pay attention to individual sounds in each word")
        
        if analysis['completeness_score'] < 0.9:
            tips.append("Make sure to pronounce all words in the phrase")
            
        # If all scores are good but not perfect
        if all(analysis[key] >= 0.7 for key in required_keys) and any(analysis[key] < 0.9 for key in required_keys):
            tips.append("You're doing well! Try speaking more naturally while maintaining accuracy")
            
        # If no specific issues found
        if not tips:
            tips.append("Great job! Keep practicing to maintain your pronunciation skills")
            
        return tips
        
    except Exception as e:
        return [f"Error generating tips: {str(e)}"]
