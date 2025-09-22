from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    practice_sessions = db.relationship('PracticeSession', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PracticeSession(db.Model):
    __tablename__ = 'practice_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    target_phrase = db.Column(db.Text, nullable=False)
    spoken_phrase = db.Column(db.Text)
    overall_score = db.Column(db.Float)
    word_accuracy = db.Column(db.Float)
    phoneme_accuracy = db.Column(db.Float)
    completeness_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    phoneme_details = db.relationship('PhonemeDetail', backref='practice_session', lazy=True)

    def __init__(self, user_id, target_phrase, spoken_phrase=None, overall_score=None,
                 word_accuracy=None, phoneme_accuracy=None, completeness_score=None):
        self.user_id = user_id
        self.target_phrase = target_phrase
        self.spoken_phrase = spoken_phrase
        self.overall_score = overall_score
        self.word_accuracy = word_accuracy
        self.phoneme_accuracy = phoneme_accuracy
        self.completeness_score = completeness_score

class PhonemeDetail(db.Model):
    __tablename__ = 'phoneme_details'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('practice_sessions.id'), nullable=False)
    target_phoneme = db.Column(db.String(10))
    spoken_phoneme = db.Column(db.String(10))
    is_correct = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, session_id, target_phoneme=None, spoken_phoneme=None, is_correct=False):
        self.session_id = session_id
        self.target_phoneme = target_phoneme
        self.spoken_phoneme = spoken_phoneme
        self.is_correct = is_correct