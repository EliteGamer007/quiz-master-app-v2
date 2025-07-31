import eventlet
eventlet.monkey_patch()

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init

celery = Celery(__name__)
celery.config_from_object('celeryconfig')

flask_app = None

@worker_process_init.connect
def init_app(**kwargs):
    from app import create_app
    global flask_app
    flask_app = create_app()

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
