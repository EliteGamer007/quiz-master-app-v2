from celery_backend import celery
from models.models import db, User, Score
from datetime import datetime, timedelta
from app import mail
from flask_mail import Message
import csv
import os

def send_email(to_email, subject, body):
    print(f"Sending email to: {to_email}")
    msg = Message(subject, recipients=[to_email], body=body)
    mail.send(msg)

@celery.task(bind=True)
def export_quiz_history_csv(self, user_id):
    from app import create_app
    app = create_app()
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            return {'status': 'FAILURE', 'message': 'User not found'}

        scores = Score.query.filter_by(user_id=user_id).all()
        
        export_dir = os.path.join('static', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, f'{self.request.id}.csv')

        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['quiz_title', 'score', 'max_score', 'date_attempted']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for score in scores:
                writer.writerow({
                    'quiz_title': score.quiz.title,
                    'score': score.total_score,
                    'max_score': len(score.quiz.questions),
                    'date_attempted': score.attempt_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        file_url = f"/static/exports/{self.request.id}.csv"
        return {'status': 'SUCCESS', 'file_url': file_url}


@celery.task
def send_daily_reminders():
    from app import create_app
    app = create_app()
    with app.app_context():
        twenty_four_hours_ago = datetime.utcnow() - timedelta(days=1)
        active_user_ids = db.session.query(Score.user_id).filter(Score.attempt_timestamp > twenty_four_hours_ago).distinct()
        inactive_users = db.session.query(User).filter(User.id.notin_(active_user_ids)).all()

        for user in inactive_users:
            subject = "Don't Miss Out on Your Daily Quiz!"
            body = f"Hi {user.full_name},\n\nJust a friendly reminder to keep your skills sharp by attempting a quiz today on Quiz Master!\n\nBest,\nThe Quiz Master Team"
            send_email(user.email, subject, body)
        
        return f"Sent reminders to {len(inactive_users)} inactive users."


@celery.task
def send_monthly_reports():
    from app import create_app
    app = create_app()
    with app.app_context():
        today = datetime.utcnow()
        first_day_of_current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

        users = User.query.all()

        for user in users:
            scores = db.session.query(Score).filter(
                Score.user_id == user.id,
                Score.attempt_timestamp >= first_day_of_previous_month,
                Score.attempt_timestamp <= first_day_of_current_month
            ).all()
            
            if not scores:
                continue

            num_quizzes = len(scores)
            total_score = sum(s.total_score for s in scores)
            avg_score = total_score / num_quizzes if num_quizzes > 0 else 0
            
            report_month_name = first_day_of_previous_month.strftime("%B %Y")
            
            subject = f"Your Quiz Master Performance Report for {report_month_name}"
            body = (f"Hi {user.full_name},\n\n"
                    f"Here is your performance summary for {report_month_name}:\n"
                    f"  - Quizzes Attempted: {num_quizzes}\n"
                    f"  - Average Score: {avg_score:.2f}%\n\n"
                    f"Keep up the great work!\n"
                    f"The Quiz Master Team")

            send_email(user.email, subject, body)
            
        return f"Sent monthly reports to {len(users)} users."