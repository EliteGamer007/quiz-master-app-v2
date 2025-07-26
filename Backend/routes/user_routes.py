from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import db, Score, Quiz, Subject
from sqlalchemy.orm import joinedload
from .auth_routes import user_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard', methods=['GET'])
@user_required
def user_dashboard():
    user = get_jwt_identity()
    user_id = user.get('id')

    scores = Score.query.filter_by(user_id=user_id).options(joinedload(Score.quiz)).all()
    score_data = [{
        'quiz_title': score.quiz.title,
        'total_score': score.total_score,
        'attempt_time': score.attempt_time,
        'user_rank': score.user_rank
    } for score in scores]

    return jsonify({
        'message': f"Welcome {user.get('email')}",
        'qualification': user.get('qualification'),
        'scores': score_data
    }), 200

@user_bp.route('/subjects', methods=['GET'])
@user_required
def get_subjects_for_user():
    subjects = Subject.query.all()
    subjects_data = [{
        'id': s.id,
        'title': s.title,
        'description': s.description
    } for s in subjects]

    return jsonify(subjects_data), 200
