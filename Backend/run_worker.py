import eventlet
eventlet.monkey_patch()

import sys
from celery.bin import celery

if __name__ == "__main__":
    sys.argv.insert(1, '-A')
    sys.argv.insert(2, 'celery_backend.celery')
    sys.argv.insert(3, 'worker')
    sys.argv.insert(4, '-P')
    sys.argv.insert(5, 'eventlet')
    sys.argv.insert(6, '--loglevel=info')
    
    celery.main()