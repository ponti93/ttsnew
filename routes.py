from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.models import PracticeSession, PhonemeDetail
from sqlalchemy import func

bp = Blueprint('routes', __name__)

@bp.route('/progress')
@login_required
def progress():
    print(f"Fetching progress for user {current_user.id}")
    print(f"User authenticated: {current_user.is_authenticated}")
    
    try:
        # Get user's practice sessions
        practice_sessions = PracticeSession.query.filter_by(user_id=current_user.id).order_by(
            PracticeSession.created_at.desc()
        ).all()
        
        # Convert sessions to JSON-serializable format, but keep created_at as datetime
        sessions_data = []
        for session in practice_sessions:
            sessions_data.append({
                'created_at': session.created_at,  # Pass as datetime object
                'target_phrase': session.target_phrase,
                'overall_score': float(session.overall_score) if session.overall_score else 0,
                'word_accuracy': float(session.word_accuracy) if session.word_accuracy else 0,
                'phoneme_accuracy': float(session.phoneme_accuracy) if session.phoneme_accuracy else 0
            })
        practice_sessions = sessions_data
        print(f"Found {len(practice_sessions)} practice sessions")
        
        # Print details of each session (using dictionary access)
        for session in practice_sessions:
            print(f"Session: Phrase='{session['target_phrase']}', Score={session['overall_score']}, Created={session['created_at']}")
            
        # Debug information about the save_practice_session function
        print("\nChecking recent database activity:")
        all_sessions = PracticeSession.query.order_by(PracticeSession.created_at.desc()).limit(5).all()
        print(f"Last 5 practice sessions across all users:")
        for session in all_sessions:
            print(f"Session {session.id}: User={session.user_id}, Phrase='{session.target_phrase}', Score={session.overall_score}, Created={session.created_at}")
            
    except Exception as e:
        print(f"Error fetching practice sessions: {str(e)}")
        import traceback
        print(traceback.format_exc())
        practice_sessions = []
    
    # Calculate overall stats
    total_sessions = len(practice_sessions)
    if total_sessions > 0:
        avg_overall_score = sum(session['overall_score'] for session in practice_sessions) / total_sessions
        avg_word_accuracy = sum(session['word_accuracy'] for session in practice_sessions) / total_sessions
        avg_phoneme_accuracy = sum(session['phoneme_accuracy'] for session in practice_sessions) / total_sessions
        
        # Get most practiced phrases
        most_practiced = (
            PracticeSession.query.filter_by(user_id=current_user.id)
            .with_entities(
                PracticeSession.target_phrase,
                func.count(PracticeSession.id).label('count'),
                func.avg(PracticeSession.overall_score).label('avg_score')
            )
            .group_by(PracticeSession.target_phrase)
            .order_by(func.count(PracticeSession.id).desc())
            .limit(5)
            .all()
        )
        
        # Get problematic phonemes
        problematic_phonemes = (
            PhonemeDetail.query.join(PracticeSession)
            .filter(PracticeSession.user_id == current_user.id)
            .filter(PhonemeDetail.is_correct == False)
            .with_entities(
                PhonemeDetail.target_phoneme,
                func.count(PhonemeDetail.id).label('error_count')
            )
            .group_by(PhonemeDetail.target_phoneme)
            .order_by(func.count(PhonemeDetail.id).desc())
            .limit(5)
            .all()
        )
    else:
        avg_overall_score = 0
        avg_word_accuracy = 0
        avg_phoneme_accuracy = 0
        most_practiced = []
        problematic_phonemes = []
    
    return render_template('progress.html',
                         practice_sessions=practice_sessions,
                         total_sessions=total_sessions,
                         avg_overall_score=avg_overall_score,
                         avg_word_accuracy=avg_word_accuracy,
                         avg_phoneme_accuracy=avg_phoneme_accuracy,
                         most_practiced=most_practiced,
                         problematic_phonemes=problematic_phonemes)