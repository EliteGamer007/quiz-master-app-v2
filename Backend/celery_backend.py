import eventlet
eventlet.monkey_patch()

from app import create_app
from celery import Celery
from celery.schedules import crontab

flask_app = create_app()

celery = Celery(
    __name__,
    broker=flask_app.config['broker_url'],
    backend=flask_app.config['result_backend'],
    include=['tasks']
)

celery.conf.update(flask_app.config)

class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

celery.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'tasks.send_daily_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    'send-monthly-reports': {
        'task': 'tasks.send_monthly_reports',
        'schedule': crontab(day_of_month=1, hour=8, minute=0),
    },
}