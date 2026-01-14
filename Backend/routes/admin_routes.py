from flask import Blueprint, request, jsonify, current_app
from models.models import db, User, Subject, Chapter, Quiz, Question, Score
from .auth_routes import admin_required, admin_or_quiz_master_required
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import or_, func, cast, Float
from werkzeug.utils import secure_filename
from extensions import cache, limiter
import datetime
import os

admin_bp = Blueprint('admin', __name__)

def get_file_url(filename):
    if filename:
        return f"{request.host_url}static/uploads/{filename}"
    return None

@admin_bp.route('/analytics', methods=['GET'])
@admin_required
@limiter.limit("10/minute")
@cache.cached(timeout=600)
def get_site_analytics():
    total_users = User.query.count()
    total_quizzes = Quiz.query.count()
    total_attempts = Score.query.count()
    return jsonify({
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts
    })

@admin_bp.route('/leaderboard', methods=['GET'])
@admin_required
@limiter.limit("10/minute")
@cache.cached(timeout=600)
def get_leaderboard():
    question_count_sq = db.session.query(
        Quiz.id, func.count(Question.id).label("question_count")
    ).join(Question).group_by(Quiz.id).subquery()

    leaderboard_data = db.session.query(
        User.full_name,
        func.count(Score.id).label('quizzes_taken'),
        func.avg(cast(Score.total_score, Float) / question_count_sq.c.question_count).label('average_score_ratio')
    ).join(Score, User.id == Score.user_id)\
     .join(question_count_sq, Score.quiz_id == question_count_sq.c.id)\
     .group_by(User.id)\
     .order_by(func.avg(cast(Score.total_score, Float) / question_count_sq.c.question_count).desc())\
     .limit(10).all()

    return jsonify([{
        'name': user.full_name,
        'quizzes_taken': user.quizzes_taken,
        'average_score_ratio': round(user.average_score_ratio, 2) if user.average_score_ratio else 0
    } for user in leaderboard_data])


@admin_bp.route('/quiz/<int:quiz_id>/summary', methods=['GET'])
@admin_or_quiz_master_required
@limiter.limit("10/minute")
@cache.cached(timeout=300)
def get_quiz_summary(quiz_id):
    quiz = Quiz.query.options(joinedload(Quiz.questions)).get_or_404(quiz_id)
    scores = Score.query.filter_by(quiz_id=quiz_id).options(joinedload(Score.user)).order_by(Score.total_score.desc()).limit(5).all()

    top_scores = [{
        'user_name': score.user.full_name,
        'score': score.total_score,
        'max_score': len(quiz.questions)
    } for score in scores]

    total_attempts = Score.query.filter_by(quiz_id=quiz_id).count()
    total_possible_score = total_attempts * len(quiz.questions)
    total_actual_score = db.session.query(func.sum(Score.total_score)).filter_by(quiz_id=quiz_id).scalar() or 0
    
    accuracy = (total_actual_score / total_possible_score) * 100 if total_possible_score > 0 else 0

    score_distribution = db.session.query(Score.total_score, func.count(Score.id)).filter_by(quiz_id=quiz_id).group_by(Score.total_score).all()
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


@admin_bp.route('/users', methods=['GET'])
@admin_required
@limiter.limit("60/minute")
@cache.cached(timeout=300)
def get_all_users():
    users = User.query.all()
    users_data = [{
        'id': user.id,
        'full_name': user.full_name,
        'email': user.email,
        'qualification': user.qualification,
        'age': user.age
    } for user in users]
    return jsonify(users_data), 200

@admin_bp.route('/search/users', methods=['GET'])
@admin_required
@limiter.limit("100/minute")
def search_users():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    search_term = f"%{query}%"
    users = User.query.filter(
        or_(
            User.full_name.ilike(search_term),
            User.email.ilike(search_term)
        )
    ).all()
    return jsonify([{
        'id': user.id, 'full_name': user.full_name, 'email': user.email,
        'qualification': user.qualification, 'age': user.age
    } for user in users])

@admin_bp.route('/search/quizzes', methods=['GET'])
@admin_required
@limiter.limit("100/minute")
def search_quizzes():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    search_term = f"%{query}%"
    quizzes = Quiz.query.filter(Quiz.title.ilike(search_term)).all()
    return jsonify([{'id': quiz.id, 'title': quiz.title, 'description': quiz.description} for quiz in quizzes])


@admin_bp.route('/subjects', methods=['GET', 'POST'])
@admin_required
@limiter.limit("60/minute")
def handle_subjects():
    if request.method == 'GET':
        @cache.cached(timeout=300)
        def get_subjects():
            subjects = Subject.query.all()
            return jsonify([{'id': s.id, 'title': s.title, 'description': s.description} for s in subjects])
        return get_subjects()
    
    if request.method == 'POST':
        cache.clear()
        data = request.get_json()
        new_subject = Subject(title=data['title'], description=data['description'])
        db.session.add(new_subject)
        db.session.commit()
        return jsonify({'id': new_subject.id, 'title': new_subject.title, 'description': new_subject.description}), 201

@admin_bp.route('/subjects/<int:subject_id>', methods=['GET'])
@admin_or_quiz_master_required
@limiter.limit("60/minute")
def get_subject_detail(subject_id):
    @cache.cached(timeout=300)
    def _get_subject_detail(id):
        subject = Subject.query.get_or_404(id)
        chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        chapters_data = { 'Beginner': [], 'Intermediate': [], 'Advanced': [] }
        for chapter in chapters:
            if chapter.level in chapters_data:
                chapters_data[chapter.level].append({
                    'id': chapter.id, 'heading': chapter.heading, 'description': chapter.description, 'level': chapter.level
                })
        
        return jsonify({
            'id': subject.id, 'title': subject.title, 'description': subject.description, 'chapters': chapters_data
        })
    return _get_subject_detail(subject_id)

@admin_bp.route('/subjects/<int:subject_id>', methods=['PUT', 'DELETE'])
@admin_required
@limiter.limit("60/minute")
def update_delete_subject(subject_id):
    cache.clear()
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'PUT':
        data = request.get_json()
        subject.title = data['title']
        subject.description = data['description']
        db.session.commit()
        return jsonify({'message': 'Subject updated successfully'})

    if request.method == 'DELETE':
        db.session.delete(subject)
        db.session.commit()
        return jsonify({'message': 'Subject deleted successfully'})

@admin_bp.route('/subjects/<int:subject_id>/chapters', methods=['POST'])
@admin_required
@limiter.limit("60/minute")
def add_chapter(subject_id):
    cache.clear()
    data = request.get_json()
    new_chapter = Chapter(subject_id=subject_id, heading=data['heading'], level=data['level'], description=data['description'])
    db.session.add(new_chapter)
    db.session.commit()
    return jsonify({'id': new_chapter.id, 'heading': new_chapter.heading, 'level': new_chapter.level, 'description': new_chapter.description}), 201

@admin_bp.route('/chapters/<int:chapter_id>', methods=['PUT', 'DELETE'])
@admin_required
@limiter.limit("60/minute")
def handle_chapter(chapter_id):
    cache.clear()
    chapter = Chapter.query.get_or_404(chapter_id)
    if request.method == 'PUT':
        data = request.get_json()
        chapter.heading = data['heading']
        chapter.description = data['description']
        chapter.level = data['level']
        db.session.commit()
        return jsonify({'message': 'Chapter updated successfully'})

    if request.method == 'DELETE':
        db.session.delete(chapter)
        db.session.commit()
        return jsonify({'message': 'Chapter deleted successfully'})

@admin_bp.route('/chapters/<int:chapter_id>/quizzes', methods=['GET'])
@admin_or_quiz_master_required
@limiter.limit("60/minute")
def get_chapter_quizzes(chapter_id):
    @cache.cached(timeout=300)
    def _get_quizzes_for_chapter(id):
        chapter = Chapter.query.options(joinedload(Chapter.quizzes)).get_or_404(id)
        quizzes_data = []
        for quiz in chapter.quizzes:
            quizzes_data.append({
                'id': quiz.id, 'title': quiz.title, 'description': quiz.description,
                'time_limit': quiz.time_limit, 'one_attempt_only': quiz.one_attempt_only,
                'start_time': quiz.start_time.isoformat() if quiz.start_time else None
            })
        return jsonify({'chapter_id': chapter.id, 'chapter_heading': chapter.heading, 'quizzes': quizzes_data})
    return _get_quizzes_for_chapter(chapter_id)

@admin_bp.route('/chapters/<int:chapter_id>/quizzes', methods=['POST'])
@admin_required
@limiter.limit("60/minute")
def create_chapter_quiz(chapter_id):
    cache.clear()
    data = request.get_json()
    start_time = datetime.datetime.fromisoformat(data['start_time']) if data.get('start_time') else None
    new_quiz = Quiz(
        chapter_id=chapter_id, 
        title=data['title'], 
        description=data.get('description'), 
        time_limit=data.get('time_limit'),
        one_attempt_only=data.get('one_attempt_only', False),
        start_time=start_time,
        created_by_quiz_master_id=None  # Admin-created quizzes have no quiz master owner
    )
    db.session.add(new_quiz)
    db.session.commit()
    return jsonify({'id': new_quiz.id}), 201

@admin_bp.route('/quizzes/<int:quiz_id>', methods=['GET'])
@admin_or_quiz_master_required
@limiter.limit("60/minute")
def get_quiz_detail(quiz_id):
    @cache.cached(timeout=300)
    def _get_quiz_detail(id):
        quiz = Quiz.query.get_or_404(id)
        questions = [{
            'id': q.id, 
            'question_text': q.question_text, 
            'image_url': get_file_url(q.image_url),
            'option_a': q.option_a, 'option_b': q.option_b, 
            'option_c': q.option_c, 'option_d': q.option_d, 
            'correct_option': q.correct_option
        } for q in quiz.questions]
        return jsonify({'id': quiz.id, 'title': quiz.title, 'description': quiz.description, 'questions': questions})
    return _get_quiz_detail(quiz_id)

@admin_bp.route('/quizzes/<int:quiz_id>', methods=['PUT', 'DELETE'])
@admin_required
@limiter.limit("60/minute")
def update_delete_quiz(quiz_id):
    cache.clear()
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'PUT':
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

    if request.method == 'DELETE':
        db.session.delete(quiz)
        db.session.commit()
        return jsonify({'message': 'Quiz deleted successfully'})

@admin_bp.route('/quizzes/<int:quiz_id>/questions', methods=['POST'])
@admin_required
@limiter.limit("30/minute")
def add_question(quiz_id):
    cache.clear()
    data = request.form.to_dict()
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            image_filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
    
    new_question = Question(quiz_id=quiz_id, image_url=image_filename, **data)
    db.session.add(new_question)
    db.session.commit()
    
    return jsonify({'id': new_question.id, 'image_url': get_file_url(new_question.image_url), **data}), 201

@admin_bp.route('/questions/<int:question_id>', methods=['PUT', 'DELETE'])
@admin_required
@limiter.limit("30/minute")
def handle_question(question_id):
    cache.clear()
    question = Question.query.get_or_404(question_id)
    if request.method == 'PUT':
        data = request.form.to_dict()
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
                question.image_url = image_filename
        for key, value in data.items():
            setattr(question, key, value)
        db.session.commit()
        return jsonify({'message': 'Question updated successfully'})

    if request.method == 'DELETE':
        db.session.delete(question)
        db.session.commit()
        return jsonify({'message': 'Question deleted successfully'})