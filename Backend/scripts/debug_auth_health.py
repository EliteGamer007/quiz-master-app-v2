import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from models.models import db, RevokedToken, UserTokenState, QuizMaster
from extensions import cache

app = create_app()

with app.app_context():
    revoked_deleted = RevokedToken.query.delete()
    states_deleted = UserTokenState.query.delete()
    db.session.commit()

    try:
        cache_result = cache.clear()
    except Exception as exc:
        cache_result = f"cache.clear failed: {exc}"

    qm_count = QuizMaster.query.count()

    with app.test_client() as client:
        admin_ok = client.post('/api/auth/request-otp', json={'email': 'admin@quiz.com', 'password': 'admin123'})
        admin_bad = client.post('/api/auth/request-otp', json={'email': 'admin@quiz.com', 'password': 'wrong'})

    print('reset.revoked_deleted=', revoked_deleted)
    print('reset.states_deleted=', states_deleted)
    print('reset.cache_clear=', cache_result)
    print('data.quiz_master_count=', qm_count)
    print('auth.admin_ok.status=', admin_ok.status_code)
    print('auth.admin_ok.json=', admin_ok.get_json())
    print('auth.admin_bad.status=', admin_bad.status_code)
    print('auth.admin_bad.json=', admin_bad.get_json())
