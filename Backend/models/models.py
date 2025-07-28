from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    qualification = db.Column(db.String(100))
    age = db.Column(db.Integer)
    scores = db.relationship('Score', backref='user', cascade='all, delete')
    ratings = db.relationship('Rating', backref='user', cascade='all, delete')

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    chapters = db.relationship('Chapter', backref='subject', cascade='all, delete')

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    heading = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50))
    description = db.Column(db.Text)
    quizzes = db.relationship('Quiz', backref='chapter', cascade='all, delete')

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    rating = db.Column(db.Float)
    time_limit = db.Column(db.Integer)
    start_time = db.Column(db.DateTime, nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    avg_completion_time = db.Column(db.Float)
    questions = db.relationship('Question', backref='quiz', cascade='all, delete')
    scores = db.relationship('Score', backref='quiz', cascade='all, delete')
    ratings = db.relationship('Rating', backref='quiz', cascade='all, delete')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    difficulty = db.Column(db.String(20))
    description = db.Column(db.Text)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    total_score = db.Column(db.Float, nullable=False)
    attempt_time = db.Column(db.Float)
    user_rank = db.Column(db.Integer)
    attempt_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'quiz_id', name='_user_quiz_uc'),)
