from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity
from models.models import db, Subject, Chapter, Quiz, Question, Score, Rating
from .auth_routes import user_required
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func
from tasks import export_quiz_history_csv
from celery.result import AsyncResult
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/export-scores', methods=['POST'])
@user_required
def export_scores():
    user = get_jwt_identity()
    user_id = user.get('id')
    task = export_quiz_history_csv.delay(user_id)
    return jsonify({'task_id': task.id}), 202

@user_bp.route('/export-status/<task_id>', methods=['GET'])
@user_required
def get_export_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result,
    }
    return jsonify(result)

@user_bp.route('/download-export/<filename>', methods=['GET'])
@user_required
def download_export(filename):
    export_dir = os.path.join(os.getcwd(), 'static', 'exports')
    return send_from_directory(export_dir, filename, as_attachment=True)


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

@user_bp.route('/quiz-info/<int:quiz_id>', methods=['GET'])
@user_required
def get_quiz_info(quiz_id):
    user = get_jwt_identity()
    user_id = user.get('id')
    quiz = Quiz.query.options(
        joinedload(Quiz.chapter).joinedload(Chapter.subject),
        joinedload(Quiz.questions)
    ).get_or_404(quiz_id)
    
    best_score = db.session.query(func.max(Score.total_score)).filter_by(user_id=user_id, quiz_id=quiz_id).scalar()
    
    has_attempted = False
    if quiz.one_attempt_only:
        attempt_count = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).count()
        if attempt_count > 0:
            has_attempted = True

    status = 'Live'
    if quiz.start_time:
        now = datetime.utcnow()
        end_time = quiz.start_time + datetime.timedelta(minutes=(quiz.time_limit * 2))
        if now < quiz.start_time:
            status = 'Not yet started'
        elif now > end_time:
            status = 'Expired'

    info = {
        'id': quiz.id,
        'title': quiz.title,
        'description': quiz.description,
        'time_limit': quiz.time_limit,
        'chapter': quiz.chapter.heading,
        'subject': quiz.chapter.subject.title,
        'question_count': len(quiz.questions),
        'best_score': best_score if best_score is not None else 'N/A',
        'average_rating': quiz.rating,
        'one_attempt_only': quiz.one_attempt_only,
        'has_attempted': has_attempted,
        'status': status,
        'start_time_formatted': quiz.start_time.strftime('%Y-%m-%d %H:%M') if quiz.start_time else None
    }
    return jsonify(info)

@user_bp.route('/quiz/<int:quiz_id>/rate', methods=['POST'])
@user_required
def rate_quiz(quiz_id):
    data = request.get_json()
    user = get_jwt_identity()
    user_id = user.get('id')
    new_rating_score = data.get('rating')

    if not isinstance(new_rating_score, int) or not 1 <= new_rating_score <= 5:
        return jsonify({'error': 'Invalid rating'}), 400

    existing_rating = Rating.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
    if existing_rating:
        return jsonify({'error': 'You have already rated this quiz.'}), 409
    
    new_rating = Rating(user_id=user_id, quiz_id=quiz_id, score=new_rating_score)
    db.session.add(new_rating)
    
    quiz = Quiz.query.get_or_404(quiz_id)
    all_ratings = [r.score for r in quiz.ratings]
    quiz.rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
    
    db.session.commit()
    return jsonify({'message': 'Rating submitted', 'new_average_rating': quiz.rating})


@user_bp.route('/quiz/<int:quiz_id>/questions', methods=['GET'])
@user_required
def get_quiz_questions(quiz_id):
    quiz = Quiz.query.options(joinedload(Quiz.questions)).get_or_404(quiz_id)

    if quiz.start_time:
        now = datetime.utcnow()
        end_time = quiz.start_time + datetime.timedelta(minutes=(quiz.time_limit * 2))
        if now < quiz.start_time:
            return jsonify({'error': 'This quiz has not started yet.'}), 403
        if now > end_time:
            return jsonify({'error': 'This quiz has expired.'}), 403

    questions = []
    for q in quiz.questions:
        questions.append({
            'id': q.id,
            'question_text': q.question_text,
            'image_url': f"{request.host_url}static/uploads/{q.image_url}" if q.image_url else None,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'correct_option': q.correct_option
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
    quiz = Quiz.query.get_or_404(quiz_id)
    score = 0
    total_questions = len(quiz.questions)
    for question in quiz.questions:
        user_answer = answers.get(str(question.id))
        if user_answer and user_answer.upper() == question.correct_option.upper():
            score += 1
    user = get_jwt_identity()
    user_id = user.get('id')
    new_score = Score(
        user_id=user_id,
        quiz_id=quiz_id,
        total_score=score,
        attempt_timestamp=datetime.utcnow()
    )
    db.session.add(new_score)
    db.session.commit()
    return jsonify({
        'message': 'Quiz submitted successfully',
        'total_score': score,
        'max_score': total_questions
    }), 200

@user_bp.route('/scores', methods=['GET'])
@user_required
def get_user_scores():
    user = get_jwt_identity()
    user_id = user.get('id')
    scores = Score.query.filter_by(user_id=user_id).options(
        joinedload(Score.quiz).joinedload(Quiz.questions)
    ).order_by(Score.attempt_timestamp.desc()).all()
    
    score_data = []
    for score in scores:
        score_data.append({
            'quiz_id': score.quiz.id,
            'quiz_title': score.quiz.title,
            'score': score.total_score,
            'max_score': len(score.quiz.questions),
            'date': score.attempt_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(score_data)

@user_bp.route('/search/subjects', methods=['GET'])
@user_required
def search_subjects():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    search_term = f"%{query}%"
    subjects = Subject.query.filter(Subject.title.ilike(search_term)).all()
    return jsonify([{'id': s.id, 'title': s.title, 'description': s.description} for s in subjects])

@user_bp.route('/search/quizzes', methods=['GET'])
@user_required
def search_quizzes():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    search_term = f"%{query}%"
    quizzes = Quiz.query.filter(Quiz.title.ilike(search_term)).all()
    return jsonify([{'id': quiz.id, 'title': quiz.title} for quiz in quizzes])