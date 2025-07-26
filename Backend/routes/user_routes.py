from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from models.models import db, Subject, Chapter, Quiz, Question, Score
from .auth_routes import user_required
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/subjects', methods=['GET'])
@user_required
def get_subjects_for_user():
    subjects = Subject.query.all()
    return jsonify([
        {'id': s.id, 'title': s.title, 'description': s.description}
        for s in subjects
    ])

@user_bp.route('/subjects/<int:subject_id>/chapters', methods=['GET'])
@user_required
def get_chapters_for_subject(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return jsonify([
        {'id': c.id, 'heading': c.heading, 'level': c.level}
        for c in chapters
    ])

@user_bp.route('/chapters/<int:chapter_id>/quizzes', methods=['GET'])
@user_required
def get_quizzes_for_chapter(chapter_id):
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return jsonify([
        {
            'id': quiz.id,
            'title': quiz.title,
            'description': quiz.description,
            'time_limit': quiz.time_limit
        } for quiz in quizzes
    ])

@user_bp.route('/quiz/<int:quiz_id>/questions', methods=['GET'])
@user_required
def get_quiz_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = []
    for q in quiz.questions:
        questions.append({
            'id': q.id,
            'question_text': q.question_text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d
        })
    return jsonify({
        'quiz_id': quiz.id,
        'quiz_title': quiz.title,
        'time_limit': quiz.time_limit,
        'questions': questions
    })

@user_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@user_required
def submit_quiz(quiz_id):
    data = request.get_json()
    answers = data.get('answers', {})
    elapsed_time = data.get('elapsed_time', 0)

    quiz = Quiz.query.get_or_404(quiz_id)
    score = 0
    total_questions = len(quiz.questions)

    for question in quiz.questions:
        user_answer = answers.get(str(question.id))
        if user_answer == question.correct_option:
            score += 1

    user = get_jwt_identity()
    user_id = user.get('id')

    new_score = Score(
        user_id=user_id,
        quiz_id=quiz_id,
        total_score=score,
        attempt_time=elapsed_time,
        attempt_timestamp=datetime.utcnow()
    )

    db.session.add(new_score)
    db.session.commit()

    return jsonify({
        'message': 'Quiz submitted successfully',
        'total_score': score,
        'max_score': total_questions
    }), 200
