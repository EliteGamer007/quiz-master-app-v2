# Quiz Master Application

A full-stack quiz application with secure email OTP-based 2-factor authentication.

## Features

- ✅ User registration and authentication
- ✅ Email OTP 2-factor authentication for users
- ✅ Admin dashboard for quiz management
- ✅ Subject and chapter organization
- ✅ Quiz creation with multiple-choice questions
- ✅ Score tracking and leaderboards
- ✅ Quiz ratings and analytics
- ✅ Timed quizzes with attempt tracking

## Tech Stack

**Backend:**
- Flask (Python web framework)
- SQLite database
- Flask-JWT-Extended for authentication
- Flask-Mail for email OTP
- Flask-SQLAlchemy for ORM

**Frontend:**
- Vue.js 3
- Vue Router
- Axios for API calls

## Setup Instructions

### Backend Setup

1. Navigate to Backend directory:
   ```bash
   cd Backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` file with your credentials:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-gmail-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

   **Getting Gmail App Password:**
   - Go to Google Account → Security
   - Enable 2-Step Verification
   - Create App Password for Mail
   - Copy the 16-character password

5. Start the backend server:
   ```bash
   python app.py
   ```
   Server runs on: http://localhost:8000

### Frontend Setup

1. Navigate to Frontend directory:
   ```bash
   cd Frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run serve
   ```
   Application runs on: http://localhost:8080

## Authentication

### Admin Login
- **URL:** http://localhost:8080/login
- **Email:** admin@quiz.com
- **Password:** admin123
- **Note:** Admin login does NOT require OTP

### User Registration (with OTP)
1. Fill in registration form (name, email, password, etc.)
2. Submit registration
3. Check email for 6-digit verification code
4. Enter OTP to complete registration
5. OTP valid for 5 minutes

### User Login (with OTP)
1. Enter email and password
2. Check email for 6-digit OTP
3. Enter OTP to complete login
4. OTP valid for 5 minutes

## API Endpoints

### Authentication
- `POST /api/auth/register` - Request registration OTP
- `POST /api/auth/verify-registration-otp` - Verify OTP and complete registration
- `POST /api/auth/request-otp` - Request OTP for login
- `POST /api/auth/verify-otp` - Verify OTP and complete login

### Admin Routes
- `GET /api/admin/subjects` - List all subjects
- `POST /api/admin/subjects` - Create subject
- `GET /api/admin/subjects/:id/chapters` - List chapters
- `POST /api/admin/chapters` - Create chapter
- `POST /api/admin/quizzes` - Create quiz

### User Routes
- `GET /api/user/subjects` - Browse subjects
- `GET /api/user/quizzes/:id` - Get quiz details
- `POST /api/user/quizzes/:id/submit` - Submit quiz answers
- `GET /api/user/scores` - Get user scores

## Security Features

- **OTP Authentication:** 6-digit OTP with 5-minute expiration
- **JWT Tokens:** Secure session management
- **Password Hashing:** Werkzeug security
- **CORS Protection:** Configured for localhost:8080
- **Environment Variables:** Sensitive data protected

## Troubleshooting

**Email not sending:**
- Verify Gmail App Password is correct
- Check 2-Step Verification is enabled
- Ensure .env file is properly configured

**OTP expired:**
- OTP valid for 5 minutes only
- Request new OTP by logging in again

**Database errors:**
- Delete instance/quiz.db and restart

**CORS errors:**
- Ensure frontend runs on localhost:8080
- Check CORS configuration in app.py

## Project Milestones

- ✓ Milestone 0: Git tracker implementation
- ✓ Milestone 1: Database schema creation
- ✓ Milestone 2: JWT-based login and RBAC decorators
- ✓ Milestone 3: Admin dashboard and content management
- ✓ Milestone 4: User dashboard implementation
- ✓ Milestone 5: Quiz history and result summaries
- ✓ Milestone 6: Quiz scheduling
- ✓ Milestone 7: Celery-based background jobs
- ✓ Milestone 8: Search functionalities
- ✓ Milestone 9: CSV export for users
- ✓ Milestone 10: Redis caching and optimization
- ✓ Milestone 12: Analysis and leaderboard features
- ✓ Milestone 13: Final submission with bug fixes
- ✓ **NEW:** Email OTP 2-factor authentication

## License

Project for Modern App Development II course in the diploma level of IITM BSc online course.