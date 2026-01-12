from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity
from models.models import db, Subject, Chapter, Quiz, Question, Score, Rating
from .auth_routes import user_required
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func
from extensions import cache, limiter
import os
import random
# RSA digital signature utilities for quiz result integrity
from crypto_utils import sign_quiz_result, verify_quiz_result
user_bp = Blueprint('user', __name__)

@user_bp.route('/recommended-quizzes', methods=['GET'])
@user_required
def get_recommended_quizzes():
    user = get_jwt_identity()
    qualification = user.get('qualification')

    level_map = {
        'School': 'Beginner',
        'General': 'Intermediate',
        'University': 'Advanced'
    }
    
    recommended_quizzes = []
    target_level = level_map.get(qualification)

    if target_level:
        chapters = Chapter.query.filter_by(level=target_level).all()
        for chapter in chapters:
            recommended_quizzes.extend(chapter.quizzes)
    
    if not recommended_quizzes:
        all_quizzes = Quiz.query.all()
        if len(all_quizzes) > 3:
            recommended_quizzes = random.sample(all_quizzes, 3)
        else:
            recommended_quizzes = all_quizzes
    else:
        if len(recommended_quizzes) > 3:
            recommended_quizzes = random.sample(recommended_quizzes, 3)

    return jsonify([
        {'id': quiz.id, 'title': quiz.title} for quiz in recommended_quizzes
    ])


@user_bp.route('/progress', methods=['GET'])
@user_required
@limiter.limit("20/minute")
def get_user_progress():
    user = get_jwt_identity()
    user_id = user.get('id')
    
    progress = db.session.query(
        Score.attempt_timestamp,
        Score.total_score,
        func.count(Question.id)
    ).select_from(Score).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Question, Quiz.id == Question.quiz_id
    ).filter(
        Score.user_id == user_id
    ).group_by(Score.id).order_by(Score.attempt_timestamp).all()

    chart_data = {
        'labels': [p[0].strftime('%b %d') for p in progress],
        'data': [(p[1] / p[2]) * 100 if p[2] > 0 else 0 for p in progress]
    }
    return jsonify(chart_data)


@user_bp.route('/export-scores', methods=['POST'])
@user_required
@limiter.limit("5/minute")
def export_scores():
    from tasks import export_quiz_history_csv
    user = get_jwt_identity()
    user_id = user.get('id')
    task = export_quiz_history_csv.delay(user_id)
    return jsonify({'task_id': task.id}), 202

@user_bp.route('/export-status/<task_id>', methods=['GET'])
@user_required
@limiter.limit("60/minute")
def get_export_status(task_id):
    from celery.result import AsyncResult
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result,
    }
    return jsonify(result)

@user_bp.route('/download-export/<filename>', methods=['GET'])
@user_required
@limiter.limit("5/minute")
def download_export(filename):
    export_dir = os.path.join(os.getcwd(), 'static', 'exports')
    return send_from_directory(export_dir, filename, as_attachment=True)


@user_bp.route('/subjects', methods=['GET'])
@user_required
@limiter.limit("60/minute")
@cache.cached(timeout=300)
def get_subjects_for_user():
    subjects = Subject.query.all()
    return jsonify([
        {'id': s.id, 'title': s.title, 'description': s.description}
        for s in subjects
    ])

@user_bp.route('/subjects/<int:subject_id>/chapters', methods=['GET'])
@user_required
@limiter.limit("60/minute")
@cache.cached(timeout=300)
def get_chapters_for_subject(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return jsonify([
        {'id': c.id, 'heading': c.heading, 'level': c.level}
        for c in chapters
    ])

@user_bp.route('/chapters/<int:chapter_id>/quizzes', methods=['GET'])
@user_required
@limiter.limit("60/minute")
@cache.cached(timeout=300)
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
    end_time = None
    if quiz.start_time:
        now = datetime.utcnow()
        end_time = quiz.start_time + timedelta(minutes=(quiz.time_limit * 2))
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
        'start_time_formatted': quiz.start_time.strftime('%Y-%m-%d %H:%M') if quiz.start_time else None,
        'expiry_time_formatted': end_time.strftime('%Y-%m-%d %H:%M') if end_time else None
    }
    return jsonify(info)


@user_bp.route('/quiz/<int:quiz_id>/rate', methods=['POST'])
@user_required
@limiter.limit("10/minute")
def rate_quiz(quiz_id):
    cache.clear()
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
@limiter.limit("10/minute")
def get_quiz_questions(quiz_id):
    quiz = Quiz.query.options(joinedload(Quiz.questions)).get_or_404(quiz_id)

    if quiz.start_time:
        now = datetime.utcnow()
        end_time = quiz.start_time + timedelta(minutes=(quiz.time_limit * 2))
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
@limiter.limit("5/minute")
def submit_quiz(quiz_id):
    cache.clear()
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
    
    # Create timestamp in ISO format for signature
    attempt_timestamp = datetime.utcnow()
    timestamp_str = attempt_timestamp.isoformat()
    
    # 🔐 DIGITAL SIGNATURE: Sign the quiz result using RSA
    # Signing: user_id|quiz_id|score|timestamp with SHA-256 hash + RSA-2048 private key
    # This proves the result came from trusted server and hasn't been tampered with
    signature = sign_quiz_result(user_id, quiz_id, score, timestamp_str)
    
    new_score = Score(
        user_id=user_id,
        quiz_id=quiz_id,
        total_score=score,
        attempt_timestamp=attempt_timestamp,
        digital_signature=signature  # Store base64-encoded RSA signature
    )
    db.session.add(new_score)
    db.session.commit()
    return jsonify({
        'message': 'Quiz submitted successfully',
        'total_score': score,
        'max_score': total_questions,
        'digital_signature': signature,  # Return signature to user for verification
        'signed': True
    }), 200

@user_bp.route('/scores', methods=['GET'])
@user_required
@limiter.limit("60/minute")
@cache.cached(timeout=300)
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
            'date': score.attempt_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'digital_signature': score.digital_signature,  # Include signature for verification
            'timestamp': score.attempt_timestamp.isoformat(),  # ISO format for verification
            'user_id': score.user_id
        })
    return jsonify(score_data)

@user_bp.route('/verify-signature/<int:score_id>', methods=['GET'])
@user_required
def verify_score_signature(score_id):
    """
    Verify the digital signature of a quiz result
    Students can use this to confirm their result is authentic and unmodified
    """
    score = Score.query.get_or_404(score_id)
    user = get_jwt_identity()
    
    # Only allow users to verify their own scores
    if score.user_id != user.get('id'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not score.digital_signature:
        return jsonify({
            'verified': False,
            'message': 'No digital signature found (legacy result)'
        }), 200
    
    # Verify signature using public key
    timestamp_str = score.attempt_timestamp.isoformat()
    is_valid = verify_quiz_result(
        score.user_id,
        score.quiz_id,
        score.total_score,
        timestamp_str,
        score.digital_signature
    )
    
    return jsonify({
        'verified': is_valid,
        'score_id': score.id,
        'user_id': score.user_id,
        'quiz_id': score.quiz_id,
        'score': score.total_score,
        'timestamp': timestamp_str,
        'signature': score.digital_signature[:50] + '...',  # Truncated for display
        'message': '✅ Signature valid - Result is authentic and unmodified' if is_valid 
                   else '❌ Signature invalid - Result may be tampered'
    }), 200

@user_bp.route('/public-key', methods=['GET'])
def get_public_key():
    """
    Get the RSA public key for independent signature verification
    Students can download this and verify results using external tools
    No authentication required - public key is meant to be shared
    """
    from crypto_utils import get_public_key_pem
    
    public_key_pem = get_public_key_pem()
    
    return jsonify({
        'public_key': public_key_pem,
        'algorithm': 'RSA-2048',
        'hash': 'SHA-256',
        'padding': 'PSS',
        'usage': 'Verify quiz result signatures',
        'instructions': 'Use this public key to verify that quiz results are authentic and unmodified'
    }), 200

@user_bp.route('/search/subjects', methods=['GET'])
@user_required
@limiter.limit("100/minute")
def search_subjects():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    search_term = f"%{query}%"
    subjects = Subject.query.filter(Subject.title.ilike(search_term)).all()
    return jsonify([{'id': s.id, 'title': s.title, 'description': s.description} for s in subjects])

@user_bp.route('/search/quizzes', methods=['GET'])
@user_required
@limiter.limit("100/minute")
def search_quizzes():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    search_term = f"%{query}%"
    quizzes = Quiz.query.filter(Quiz.title.ilike(search_term)).all()
    return jsonify([{'id': quiz.id, 'title': quiz.title} for quiz in quizzes])