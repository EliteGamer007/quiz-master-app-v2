from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from models.models import db, User, Subject, Chapter, Quiz, Question
from .auth_routes import admin_required
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import datetime
import os

admin_bp = Blueprint('admin', __name__)

def get_file_url(filename):
    if filename:
        return f"/static/uploads/{filename}"
    return None

@admin_bp.route('/users', methods=['GET'])
@admin_required
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

@admin_bp.route('/subjects', methods=['GET', 'POST'])
@admin_required
def handle_subjects():
    if request.method == 'GET':
        subjects = Subject.query.all()
        return jsonify([{'id': s.id, 'title': s.title, 'description': s.description} for s in subjects]), 200
    
    if request.method == 'POST':
        data = request.get_json()
        new_subject = Subject(title=data['title'], description=data['description'])
        db.session.add(new_subject)
        db.session.commit()
        return jsonify({'id': new_subject.id, 'title': new_subject.title, 'description': new_subject.description}), 201

@admin_bp.route('/subjects/<int:subject_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def handle_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'GET':
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
def add_chapter(subject_id):
    data = request.get_json()
    new_chapter = Chapter(subject_id=subject_id, heading=data['heading'], level=data['level'], description=data['description'])
    db.session.add(new_chapter)
    db.session.commit()
    return jsonify({'id': new_chapter.id, 'heading': new_chapter.heading, 'level': new_chapter.level, 'description': new_chapter.description}), 201

@admin_bp.route('/chapters/<int:chapter_id>', methods=['PUT', 'DELETE'])
@admin_required
def handle_chapter(chapter_id):
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

@admin_bp.route('/chapters/<int:chapter_id>/quizzes', methods=['GET', 'POST'])
@admin_required
def handle_quizzes(chapter_id):
    if request.method == 'GET':
        chapter = Chapter.query.options(joinedload(Chapter.quizzes)).get_or_404(chapter_id)
        quizzes_data = []
        for quiz in chapter.quizzes:
            created_on_str = quiz.created_on.strftime('%Y-%m-%d %H:%M:%S') if quiz.created_on else None
            # UPDATED: Serialize start_time to ISO format string
            start_time_str = quiz.start_time.isoformat() if quiz.start_time else None
            quizzes_data.append({
                'id': quiz.id, 'title': quiz.title, 'description': quiz.description,
                'rating': quiz.rating, 'time_limit': quiz.time_limit, 
                'created_on': created_on_str, 'start_time': start_time_str
            })
        return jsonify({'chapter_id': chapter.id, 'chapter_heading': chapter.heading, 'quizzes': quizzes_data})

    if request.method == 'POST':
        data = request.get_json()
        # UPDATED: Parse start_time from incoming request
        start_time = datetime.datetime.fromisoformat(data['start_time']) if data.get('start_time') else None
        
        new_quiz = Quiz(
            chapter_id=chapter_id, 
            title=data['title'], 
            description=data.get('description'), 
            time_limit=data.get('time_limit'),
            start_time=start_time
        )
        db.session.add(new_quiz)
        db.session.commit()
        
        # UPDATED: Include start_time in the response
        return jsonify({
            'id': new_quiz.id, 
            'title': new_quiz.title, 
            'description': new_quiz.description, 
            'time_limit': new_quiz.time_limit, 
            'created_on': new_quiz.created_on.strftime('%Y-%m-%d %H:%M:%S'),
            'start_time': new_quiz.start_time.isoformat() if new_quiz.start_time else None
        }), 201

@admin_bp.route('/quizzes/<int:quiz_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def handle_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'GET':
        questions = [{
            'id': q.id, 
            'question_text': q.question_text, 
            'image_url': get_file_url(q.image_url),
            'option_a': q.option_a, 
            'option_b': q.option_b, 
            'option_c': q.option_c, 
            'option_d': q.option_d, 
            'correct_option': q.correct_option
        } for q in quiz.questions]
        return jsonify({'id': quiz.id, 'title': quiz.title, 'description': quiz.description, 'questions': questions})

    if request.method == 'PUT':
        data = request.get_json()
        quiz.title = data['title']
        quiz.description = data['description']
        quiz.time_limit = data['time_limit']
        # UPDATED: Update start_time if provided
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
def add_question(quiz_id):
    data = request.form.to_dict()
    
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            image_filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
    
    new_question = Question(
        quiz_id=quiz_id,
        image_url=image_filename,
        **data
    )
    db.session.add(new_question)
    db.session.commit()
    
    response_data = {
        'id': new_question.id,
        'image_url': get_file_url(new_question.image_url),
        **data
    }
    return jsonify(response_data), 201

@admin_bp.route('/questions/<int:question_id>', methods=['PUT', 'DELETE'])
@admin_required
def handle_question(question_id):
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
        if question.image_url:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], question.image_url))
            except FileNotFoundError:
                pass
        
        db.session.delete(question)
        db.session.commit()
        return jsonify({'message': 'Question deleted successfully'})