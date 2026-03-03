import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app

app = create_app()

with app.test_client() as client:
    login = client.post('/api/auth/request-otp', json={'email': 'admin@quiz.com', 'password': 'admin123'})
    data = login.get_json() or {}
    token = data.get('access_token') or data.get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    dash = client.get('/api/auth/admin/dashboard', headers=headers)
    analytics = client.get('/api/admin/analytics', headers=headers)

    print('login.status=', login.status_code)
    print('dash.status=', dash.status_code, 'dash.json=', dash.get_json())
    print('analytics.status=', analytics.status_code, 'analytics.json=', analytics.get_json())
