import eventlet
eventlet.monkey_patch()

import sys
from celery.bin import celery

if __name__ == "__main__":
    sys.argv.insert(1, '-A')
    sys.argv.insert(2, 'celery_backend.celery')
    sys.argv.insert(3, 'beat')
    sys.argv.insert(4, '--loglevel=info')

    celery.main()