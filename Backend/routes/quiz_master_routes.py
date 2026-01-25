from flask import Blueprint, request, jsonify
from models.models import db, Quiz, Question, Score, Chapter, Subject
from .auth_routes import quiz_master_required
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.orm import joinedload
from sqlalchemy import func, cast, Float
from extensions import cache, limiter
from crypto_utils import encrypt_answer, decrypt_answer
import datetime

quiz_master_bp = Blueprint('quiz_master', __name__)

@quiz_master_bp.route('/dashboard', methods=['GET'])
@quiz_master_required
@limiter.limit("10/minute")
@cache.cached(timeout=600)
def get_quiz_master_dashboard():
    """Get dashboard analytics for quiz master's own quizzes only"""
    identity = get_jwt_identity()
    quiz_master_id = identity['id']
    
    # Count only quizzes created by this quiz master
    total_quizzes = Quiz.query.filter_by(created_by_quiz_master_id=quiz_master_id).count()
    
    # Count attempts only for this quiz master's quizzes
    total_attempts = db.session.query(func.count(Score.id))\
        .join(Quiz, Score.quiz_id == Quiz.id)\
        .filter(Quiz.created_by_quiz_master_id == quiz_master_id)\
        .scalar() or 0
    
    return jsonify({
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'quiz_master_name': identity['full_name']
    })

@quiz_master_bp.route('/analytics', methods=['GET'])
@quiz_master_required
@limiter.limit("10/minute")
@cache.cached(timeout=600)
def get_quiz_master_analytics():
    """Get detailed analytics for all quizzes created by this quiz master"""
    identity = get_jwt_identity()
    quiz_master_id = identity['id']
    
    # Get all quizzes created by this quiz master with their stats
    quizzes = db.session.query(
        Quiz.id,
        Quiz.title,
        func.count(Score.id).label('total_attempts'),
        func.avg(Score.total_score).label('avg_score')
    ).outerjoin(Score, Quiz.id == Score.quiz_id)\
     .filter(Quiz.created_by_quiz_master_id == quiz_master_id)\
     .group_by(Quiz.id, Quiz.title)\
     .all()
    
    analytics_data = [{
        'quiz_id': q.id,
        'quiz_title': q.title,
        'total_attempts': q.total_attempts,
        'average_score': round(q.avg_score, 2) if q.avg_score else 0
    } for q in quizzes]
    
    return jsonify(analytics_data)

@quiz_master_bp.route('/quiz/<int:quiz_id>/summary', methods=['GET'])
@quiz_master_required
@limiter.limit("10/minute")
@cache.cached(timeout=300)
def get_quiz_summary(quiz_id):
    """Get detailed summary for a specific quiz - only if created by this quiz master"""
    identity = get_jwt_identity()
    quiz_master_id = identity['id']
    
    quiz = Quiz.query.options(joinedload(Quiz.questions))\
        .filter_by(id=quiz_id, created_by_quiz_master_id=quiz_master_id)\
        .first_or_404()
    
    scores = Score.query.filter_by(quiz_id=quiz_id)\
        .options(joinedload(Score.user))\
        .order_by(Score.total_score.desc())\
        .limit(5).all()

    top_scores = [{
        'user_name': score.user.full_name,
        'score': score.total_score,
        'max_score': len(quiz.questions)
    } for score in scores]

    total_attempts = Score.query.filter_by(quiz_id=quiz_id).count()
    total_possible_score = total_attempts * len(quiz.questions)
    total_actual_score = db.session.query(func.sum(Score.total_score))\
        .filter_by(quiz_id=quiz_id).scalar() or 0
    
    accuracy = (total_actual_score / total_possible_score) * 100 if total_possible_score > 0 else 0

    score_distribution = db.session.query(Score.total_score, func.count(Score.id))\
        .filter_by(quiz_id=quiz_id).group_by(Score.total_score).all()
    
    chart_data = {
        'labels': [f"{int(s[0])}/{len(quiz.questions)}" for s in score_distribution],
        'data': [s[1] for s in score_distribution]
    }

    return jsonify({
        'top_scores': top_scores,
        'total_attempts': total_attempts,
        'accuracy': round(accuracy, 2),
        'chart_data': chart_data
    })

@quiz_master_bp.route('/quizzes', methods=['GET'])
@quiz_master_required
@limiter.limit("60/minute")
@cache.cached(timeout=300)
def get_my_quizzes():
    """Get all quizzes created by this quiz master"""
    identity = get_jwt_identity()
    quiz_master_id = identity['id']
    
    quizzes = Quiz.query.filter_by(created_by_quiz_master_id=quiz_master_id)\
        .options(joinedload(Quiz.chapter).joinedload(Chapter.subject))\
        .all()
    
    quizzes_data = [{
        'id': quiz.id,
        'title': quiz.title,
        'description': quiz.description,
        'chapter': quiz.chapter.heading if quiz.chapter else None,
        'subject': quiz.chapter.subject.title if quiz.chapter and quiz.chapter.subject else None,
        'time_limit': quiz.time_limit,
        'one_attempt_only': quiz.one_attempt_only,
        'created_on': quiz.created_on.isoformat() if quiz.created_on else None
    } for quiz in quizzes]
    
    return jsonify(quizzes_data)

@quiz_master_bp.route('/subjects', methods=['GET'])
@quiz_master_required
@limiter.limit("60/minute")
@cache.cached(timeout=300)
def get_subjects():
    """Get all subjects and chapters for quiz creation"""
    subjects = Subject.query.options(joinedload(Subject.chapters)).all()
    subjects_data = [{
        'id': s.id,
        'title': s.title,
        'description': s.description,
        'chapters': [{
            'id': c.id,
            'heading': c.heading,
            'level': c.level,
            'description': c.description
        } for c in s.chapters]
    } for s in subjects]
    return jsonify(subjects_data)

@quiz_master_bp.route('/chapters/<int:chapter_id>/quizzes', methods=['GET', 'POST'])
@quiz_master_required
@limiter.limit("30/minute")
def handle_chapter_quizzes(chapter_id):
    """Get all quizzes in a chapter (read-only) or create a new quiz"""
    if request.method == 'GET':
        # Quiz masters can view all quizzes in a chapter
        chapter = Chapter.query.options(joinedload(Chapter.quizzes)).get_or_404(chapter_id)
        quizzes_data = []
        for quiz in chapter.quizzes:
            quizzes_data.append({
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'time_limit': quiz.time_limit,
                'one_attempt_only': quiz.one_attempt_only,
                'start_time': quiz.start_time.isoformat() if quiz.start_time else None
            })
        return jsonify({
            'chapter_id': chapter.id,
            'chapter_heading': chapter.heading,
            'quizzes': quizzes_data
        })
    
    if request.method == 'POST':
        """Create a new quiz under a chapter"""
        cache.clear()
        identity = get_jwt_identity()
        quiz_master_id = identity['id']
        
        data = request.get_json()
        start_time = datetime.datetime.fromisoformat(data['start_time']) if data.get('start_time') else None
        
        new_quiz = Quiz(
            chapter_id=chapter_id,
            title=data['title'],
            description=data.get('description'),
            time_limit=data.get('time_limit'),
            one_attempt_only=data.get('one_attempt_only', False),
            start_time=start_time,
            created_by_quiz_master_id=quiz_master_id
        )
        db.session.add(new_quiz)
        db.session.commit()
        
        return jsonify({
            'id': new_quiz.id,
            'message': 'Quiz created successfully'
        }), 201

@quiz_master_bp.route('/quizzes/<int:quiz_id>', methods=['GET', 'PUT'])
@quiz_master_required
@limiter.limit("60/minute")
def handle_quiz(quiz_id):
    """Get or update a quiz - only if created by this quiz master"""
    identity = get_jwt_identity()
    quiz_master_id = identity['id']
    
    quiz = Quiz.query.filter_by(id=quiz_id, created_by_quiz_master_id=quiz_master_id)\
        .first_or_404()
    
    if request.method == 'GET':
        questions = [{
            'id': q.id,
            'question_text': q.question_text,
            'image_url': q.image_url,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            # 🔓 DECRYPT: Quiz Master can see correct answers for their own quizzes
            'correct_option': decrypt_answer(q.correct_option),
            'difficulty': q.difficulty,
            'description': q.description
        } for q in quiz.questions]
        
        return jsonify({
            'id': quiz.id,
            'title': quiz.title,
            'description': quiz.description,
            'time_limit': quiz.time_limit,
            'one_attempt_only': quiz.one_attempt_only,
            'start_time': quiz.start_time.isoformat() if quiz.start_time else None,
            'questions': questions
        })
    
    if request.method == 'PUT':
        cache.clear()
        data = request.get_json()
        quiz.title = data['title']
        quiz.description = data['description']
        quiz.time_limit = data['time_limit']
        quiz.one_attempt_only = data.get('one_attempt_only', False)
        
        if 'start_time' in data and data['start_time']:
            quiz.start_time = datetime.datetime.fromisoformat(data['start_time'])
        else:
            quiz.start_time = None
        
        db.session.commit()
        return jsonify({'message': 'Quiz updated successfully'})

@quiz_master_bp.route('/quizzes/<int:quiz_id>/questions', methods=['POST'])
@quiz_master_required
@limiter.limit("30/minute")
def add_question(quiz_id):
    """Add a question to quiz - only if quiz was created by this quiz master"""
    cache.clear()
    identity = get_jwt_identity()
    quiz_master_id = identity['id']
    
    # Verify ownership
    quiz = Quiz.query.filter_by(id=quiz_id, created_by_quiz_master_id=quiz_master_id)\
        .first_or_404()
    
    data = request.get_json()
    # 🔐 ENCRYPT: Encrypt correct answer before storing
    new_question = Question(
        quiz_id=quiz_id,
        question_text=data['question_text'],
        image_url=data.get('image_url'),
        option_a=data['option_a'],
        option_b=data['option_b'],
        option_c=data['option_c'],
        option_d=data['option_d'],
        correct_option=encrypt_answer(data['correct_option']),
        difficulty=data.get('difficulty'),
        description=data.get('description')
    )
    db.session.add(new_question)
    db.session.commit()
    
    return jsonify({
        'id': new_question.id,
        'message': 'Question added successfully'
    }), 201

@quiz_master_bp.route('/questions/<int:question_id>', methods=['PUT', 'DELETE'])
@quiz_master_required
@limiter.limit("30/minute")
def handle_question(question_id):
    """Update or delete a question - only if the quiz was created by this quiz master"""
    cache.clear()
    identity = get_jwt_identity()
    quiz_master_id = identity['id']
    
    question = Question.query.get_or_404(question_id)
    
    # Verify ownership through quiz
    quiz = Quiz.query.filter_by(id=question.quiz_id, created_by_quiz_master_id=quiz_master_id)\
        .first_or_404()
    
    if request.method == 'PUT':
        data = request.get_json()
        question.question_text = data['question_text']
        question.option_a = data['option_a']
        question.option_b = data['option_b']
        question.option_c = data['option_c']
        question.option_d = data['option_d']
        # 🔐 ENCRYPT: Encrypt updated correct answer
        question.correct_option = encrypt_answer(data['correct_option'])
        question.difficulty = data.get('difficulty')
        question.description = data.get('description')
        question.image_url = data.get('image_url')
        
        db.session.commit()
        return jsonify({'message': 'Question updated successfully'})
    
    if request.method == 'DELETE':
        db.session.delete(question)
        db.session.commit()
        return jsonify({'message': 'Question deleted successfully'})
