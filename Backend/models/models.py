from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # Password stored as salted hash (200 chars to accommodate: "pbkdf2:sha256:260000$salt$hash")
    # Never stores plain text - uses Werkzeug's generate_password_hash with random salt per user
    password = db.Column(db.String(200), nullable=False)
    qualification = db.Column(db.String(100))
    age = db.Column(db.Integer)
    otp = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    scores = db.relationship('Score', backref='user', cascade='all, delete')
    ratings = db.relationship('Rating', backref='user', cascade='all, delete')

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # Password field for salted hash storage (same security as User model)
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
    one_attempt_only = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    avg_completion_time = db.Column(db.Float)
    # Hexadecimal (Base16) encoding: Quiz integrity hash for tamper detection
    # SHA-256 hash of quiz_id + questions content, encoded as hex string (64 chars)
    # Detects if questions/answers were modified after quiz creation
    integrity_hash = db.Column(db.String(64), nullable=True)  # Hex-encoded SHA-256 hash
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
    # RSA digital signature: Proves result integrity and authenticity
    # Signature is computed from: user_id|quiz_id|score|timestamp using SHA-256 + RSA-2048
    # Prevents tampering: changing score/user/quiz will invalidate signature
    digital_signature = db.Column(db.Text, nullable=True)  # Base64-encoded RSA signature
    # Base64 encoding: Compact verification token for result data
    # Format: user_id|quiz_id|score|timestamp encoded in Base64 (URL-safe, transferable)
    verification_token = db.Column(db.Text, nullable=True)  # Base64-encoded result data

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'quiz_id', name='_user_quiz_uc'),)