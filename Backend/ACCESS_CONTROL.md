# Access Control Implementation
## Role-Based Access Control (RBAC) with Access Control Matrix

This document comprehensively defines the **Access Control Matrix (ACM)** and **Access Control List (ACL)** implemented in the Quiz Master Application with three distinct roles: **User**, **Quiz Master**, and **Admin**.

---

## 1. Role Definitions (Subjects)

| Role | Description | Authentication Method | Primary Purpose |
|------|-------------|----------------------|-----------------|
| **User** | Regular application users | Email + Password + OTP | Take quizzes, view scores, rate quizzes |
| **Quiz Master** | Content creators | Email + Password (No OTP) | Create and manage own quizzes, view analytics |
| **Admin** | System administrators | Hardcoded credentials (No OTP) | Full system access, user management, all quiz management |

---

## 2. Access Control Matrix (3 Subjects × 7+ Objects)

### Objects (Resources)

1. **Subjects** - Quiz subjects/topics
2. **Chapters** - Subject subdivisions  
3. **Quizzes** - Quiz content
4. **Questions** - Individual quiz questions
5. **Users** - User accounts
6. **Scores** - Quiz attempt records
7. **Analytics** - System statistics

### Access Control Matrix

| Subject (S) → Object (O) ↓ | User | Quiz Master | Admin |
|---------------------------|------|-------------|-------|
| **Subjects** | Read | Read | **Read, Create, Update, Delete** |
| **Chapters** | Read | Read | **Read, Create, Update, Delete** |
| **Quizzes** | Read (available), Attempt | **Read (own only), Create, Update (own only)** | **Read (all), Create, Update (all), Delete (all)** |
| **Questions** | Read (during quiz) | **Read (own quizzes), Create (own quizzes), Update (own quizzes), Delete (own quizzes)** | **Read (all), Create (all), Update (all), Delete (all)** |
| **Users** | Read (self), Update (self) | **None** | **Read (all), Update (all), Delete (all)** |
| **Scores** | Read (self), Create (self), Export (self) | **Read (analytics for own quizzes)** | **Read (all), Analytics (all)** |
| **Analytics Dashboard** | **None** | **Access (own quizzes only)** | **Access (all data)** |
| **User Management** | **None** | **None** | **Full access** |

---

## 3. Policy Definition & Justification

### Why Three Roles?

#### 1. **User Role**
- **Purpose:** Consume content safely without modification rights
- **Security:** OTP authentication prevents unauthorized access to user accounts
- **Scope:** Limited to personal data and public quizzes
- **Justification:**
  - Users should not create quizzes (prevents spam and maintains content quality)
  - Users should only see their own data (privacy protection)
  - OTP provides additional security layer for accounts with personal data

#### 2. **Quiz Master Role**
- **Purpose:** Empower educators/content creators without full admin privileges
- **Security:** No OTP (trusted users), but restricted to own content
- **Scope:** Create/modify only their own quizzes and questions
- **Justification:**
  - Reduces admin workload by delegating content creation
  - Allows scalable content creation across multiple educators
  - Maintains accountability through quiz ownership tracking (`created_by_quiz_master_id`)
  - Prevents interference with other creators' content (isolation)
  - No access to user management (privacy protection and separation of duties)
  - Cannot see system-wide analytics (data privacy for other creators)

#### 3. **Admin Role**
- **Purpose:** System maintenance, moderation, and oversight
- **Security:** Hardcoded credentials with full access
- **Scope:** All operations across all resources
- **Justification:**
  - Emergency content fixes (can modify any quiz/question)
  - User account management (handle support requests)
  - System-wide analytics for platform health monitoring
  - Remove inappropriate content created by any user
  - Full system control ensures stability and security

### Access Restriction Rationale

| Restriction | Justification |
|-------------|---------------|
| Users cannot create quizzes | Prevents spam and maintains content quality |
| Quiz Masters cannot access user management | Privacy protection and separation of duties |
| Quiz Masters cannot edit others' quizzes | Prevents content tampering and maintains accountability |
| Quiz Masters cannot see all analytics | Data privacy for other content creators |
| Users require OTP | Additional security layer for accounts with personal data |
| Quiz Masters bypass OTP | Trusted role with no personal user data access |
| Admin has hardcoded credentials | Emergency access and system stability |

---

## 4. Implementation of Access Control (Programmatic Enforcement)

### A. Database Schema (Ownership Tracking)

```python
# New Model for Quiz Master accounts
class QuizMaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hashed with salt
    quizzes = db.relationship('Quiz', backref='creator', lazy=True)

# Modified Quiz Model - Tracks creator
class Quiz(db.Model):
    # ... existing fields ...
    created_by_quiz_master_id = db.Column(
        db.Integer, 
        db.ForeignKey('quiz_master.id'), 
        nullable=True
    )
    # NULL = admin-created, NOT NULL = quiz master created
```

### B. Authentication Decorators (Role-Based Access)

```python
# File: routes/auth_routes.py

from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

# Admin-only access
@admin_required
def admin_only_function():
    pass

# User-only access
@user_required  
def user_only_function():
    pass

# Quiz Master-only access
@quiz_master_required
def quiz_master_only_function():
    pass

# Admin OR Quiz Master access
@admin_or_quiz_master_required
def shared_function():
    pass
```

**Implementation:**
```python
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if identity != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

def quiz_master_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if not isinstance(identity, dict) or identity.get('role') != 'quiz_master':
            return jsonify({'error': 'Quiz Master access required'}), 403
        return fn(*args, **kwargs)
    return wrapper
```

### C. Ownership Verification Pattern

```python
# Ownership check for quiz masters
quiz = Quiz.query.filter_by(
    id=quiz_id,
    created_by_quiz_master_id=quiz_master_id
).first_or_404()
# Returns 404 if not found OR not owned by this quiz master

# Ownership check for questions
question = Question.query.join(Quiz).filter(
    Question.id == question_id,
    Quiz.created_by_quiz_master_id == quiz_master_id
).first_or_404()
```

### D. API Endpoint Security

#### User Endpoints (`/api/user/`)
```python
@user_bp.route('/quizzes', methods=['GET'])
@user_required  # Decorator enforces role
def get_available_quizzes():
    # Returns only available quizzes
    pass

@user_bp.route('/quiz/<id>/submit', methods=['POST'])
@user_required  # Decorator enforces role
def submit_quiz(id):
    user_id = get_jwt_identity()['id']  # Get from JWT
    # User can only submit for themselves
    pass
```

#### Quiz Master Endpoints (`/api/quiz-master/`)
```python
@quiz_master_bp.route('/quizzes', methods=['GET'])
@quiz_master_required  # Decorator enforces role
def get_own_quizzes():
    qm_id = get_jwt_identity()['id']
    # Filter by created_by_quiz_master_id = qm_id
    quizzes = Quiz.query.filter_by(created_by_quiz_master_id=qm_id).all()
    return jsonify([...])

@quiz_master_bp.route('/quizzes/<id>', methods=['PUT'])
@quiz_master_required  # Decorator enforces role
def update_quiz(id):
    qm_id = get_jwt_identity()['id']
    # Ownership check - returns 404 if not owner
    quiz = Quiz.query.filter_by(id=id, created_by_quiz_master_id=qm_id).first_or_404()
    # Update only if owned
    pass
```

#### Admin Endpoints (`/api/admin/`)
```python
@admin_bp.route('/quizzes/<id>', methods=['DELETE'])
@admin_required  # Decorator enforces role
def delete_quiz(id):
    # Admin can delete ANY quiz
    quiz = Quiz.query.get_or_404(id)
    db.session.delete(quiz)
    pass
```

### E. Multi-Layer Security

1. **Decorator Layer**: Checks JWT role
2. **Database Filter Layer**: Filters by ownership
3. **Query Layer**: Returns 404 if not found/not owned
4. **Frontend Layer**: Hides unauthorized UI elements

---

## 5. Access Control Lists (ACL) by Resource

### Dashboard & Analytics

| Endpoint | Allowed Roles | Scope | Justification |
|----------|---------------|-------|---------------|
| `/api/admin/analytics` | Admin | All data | Admin needs system-wide overview |
| `/api/quiz-master/dashboard` | Quiz Master | Own quizzes only | Quiz masters track their content performance |
| `/api/quiz-master/analytics` | Quiz Master | Own quizzes only | Privacy - cannot see others' data |

### Quiz Management

| Endpoint | Method | Allowed Roles | Ownership Check | Policy |
|----------|--------|---------------|-----------------|--------|
| `/api/admin/chapters/<id>/quizzes` | POST | Admin | Sets `created_by_quiz_master_id=NULL` | Admin creates system quizzes |
| `/api/quiz-master/chapters/<id>/quizzes` | POST | Quiz Master | Sets `created_by_quiz_master_id=qm.id` | Quiz master creates own quiz |
| `/api/admin/quizzes/<id>` | GET/PUT/DELETE | Admin | None (all quizzes) | Admin manages all content |
| `/api/quiz-master/quizzes/<id>` | GET/PUT | Quiz Master | Filters by `created_by_quiz_master_id` | Quiz master manages own content only |
| `/api/user/quizzes` | GET | User | None (public) | Users browse available quizzes |

### Question Management

| Endpoint | Method | Allowed Roles | Ownership Check | Policy |
|----------|--------|---------------|-----------------|--------|
| `/api/admin/quizzes/<id>/questions` | POST | Admin | None | Admin adds questions to any quiz |
| `/api/quiz-master/quizzes/<id>/questions` | POST | Quiz Master | Verifies quiz ownership | Quiz master adds to own quizzes |
| `/api/admin/questions/<id>` | PUT/DELETE | Admin | None | Admin fixes any question |
| `/api/quiz-master/questions/<id>` | PUT/DELETE | Quiz Master | Verifies via quiz ownership | Quiz master modifies own questions |

### User Management

| Endpoint | Method | Allowed Roles | Scope | Policy |
|----------|--------|---------------|-------|--------|
| `/api/admin/users` | GET | Admin | All users | Admin needs user oversight |
| `/api/admin/search/users` | GET | Admin | All users | Admin performs user lookups |
| `/api/user/profile` | GET/PUT | User | Self only | Users manage own accounts |

---

## 6. Authentication Flow

### User Authentication
```
1. POST /api/auth/request-otp
   → Email + Password → Verify → Send OTP
2. POST /api/auth/verify-otp  
   → Email + OTP Code → Verify → JWT Token
3. Use JWT Token for subsequent requests
```

### Quiz Master Authentication
```
1. POST /api/auth/request-otp
   → Email + Password → Verify Role → JWT Token (No OTP)
2. Use JWT Token for subsequent requests
```

### Admin Authentication
```
1. POST /api/auth/request-otp
   → Hardcoded Email + Password → JWT Token (No OTP)
2. Use JWT Token for subsequent requests
```

### JWT Token Structure

```json
// User Token
{
  "id": 123,
  "email": "user@example.com",
  "role": "user",
  "qualification": "B.Sc",
  "exp": 1234567890
}

// Quiz Master Token
{
  "id": 45,
  "email": "master@example.com", 
  "role": "quiz_master",
  "full_name": "John Educator",
  "exp": 1234567890
}

// Admin Token
{
  "identity": "admin",
  "exp": 1234567890
}
```

---

## 7. Security Best Practices Implemented

✅ **Principle of Least Privilege**: Each role has minimum necessary permissions  
✅ **Separation of Duties**: Content creation separate from user management  
✅ **Accountability**: Quiz ownership tracked via `created_by_quiz_master_id`  
✅ **Defense in Depth**: Decorators + database filters + ownership checks  
✅ **Secure Authentication**: Password hashing, OTP for sensitive accounts  
✅ **Fail-Safe Defaults**: Missing permissions return 403, missing ownership returns 404  
✅ **Audit Trail**: Database tracks who created each quiz

---

## 8. Test Cases for Access Control

### ✅ Valid Access (Expected Success)

```python
# User submits quiz
POST /api/user/quiz/1/submit (with user token) → 200 OK

# Quiz Master views own quiz analytics
GET /api/quiz-master/quiz/5/summary (with qm token, owns quiz 5) → 200 OK

# Admin deletes any quiz
DELETE /api/admin/quizzes/10 (with admin token) → 200 OK
```

### ❌ Invalid Access (Expected 403 or 404)

```python
# User attempts to create quiz
POST /api/admin/chapters/1/quizzes (with user token) → 403 Forbidden

# Quiz Master attempts to view user list
GET /api/admin/users (with qm token) → 403 Forbidden

# Quiz Master attempts to edit another's quiz
PUT /api/quiz-master/quizzes/99 (qm doesn't own quiz 99) → 404 Not Found
```

---

## 9. Database Migration

### Migration Steps

```sql
-- 1. Create QuizMaster table
CREATE TABLE quiz_master (
    id INTEGER PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL
);

-- 2. Add foreign key to Quiz table
ALTER TABLE quiz ADD COLUMN created_by_quiz_master_id INTEGER;
ALTER TABLE quiz ADD FOREIGN KEY (created_by_quiz_master_id) 
    REFERENCES quiz_master(id);

-- 3. Create sample Quiz Master account
INSERT INTO quiz_master (full_name, email, password) 
VALUES ('John Educator', 'master@quiz.com', '<hashed_password>');
```

### Migration Script
```bash
cd Backend
python migrate_access_control.py
```

---

## 10. API Endpoints Summary

### User Endpoints (`/api/user/`)
- `GET /quizzes` - Browse available quizzes
- `POST /quiz/<id>/submit` - Submit quiz attempt
- `GET /scores` - View own score history
- `POST /quiz/<id>/rate` - Rate a quiz
- `GET /profile` - View own profile
- `PUT /profile` - Update own profile
- `POST /export-scores` - Export own scores to CSV

### Quiz Master Endpoints (`/api/quiz-master/`)
- `GET /dashboard` - View own statistics
- `GET /analytics` - Analytics for own quizzes
- `GET /quizzes` - List own quizzes
- `GET /subjects` - View all subjects (read-only)
- `GET /chapters/<id>/quizzes` - View quizzes in chapter
- `POST /chapters/<id>/quizzes` - Create quiz in chapter
- `GET /quizzes/<id>` - View own quiz details
- `PUT /quizzes/<id>` - Update own quiz
- `POST /quizzes/<id>/questions` - Add question to own quiz
- `PUT /questions/<id>` - Update question in own quiz
- `DELETE /questions/<id>` - Delete question from own quiz
- `GET /quiz/<id>/summary` - Analytics for own quiz

### Admin Endpoints (`/api/admin/`)
- `GET /analytics` - Site-wide analytics
- `GET /leaderboard` - Top performers
- `GET /users` - List all users
- `GET /search/users` - Search users
- `GET /subjects` - List subjects
- `POST /subjects` - Create subject
- `GET /subjects/<id>` - View subject (read-only split from PUT/DELETE)
- `PUT /subjects/<id>` - Update subject
- `DELETE /subjects/<id>` - Delete subject
- `POST /subjects/<id>/chapters` - Create chapter
- `PUT /chapters/<id>` - Update chapter
- `DELETE /chapters/<id>` - Delete chapter
- `GET /chapters/<id>/quizzes` - View quizzes in chapter (read-only)
- `POST /chapters/<id>/quizzes` - Create quiz
- `GET /quizzes/<id>` - View any quiz (read-only split)
- `PUT /quizzes/<id>` - Update any quiz
- `DELETE /quizzes/<id>` - Delete any quiz
- `POST /quizzes/<id>/questions` - Add question to any quiz
- `PUT /questions/<id>` - Update any question
- `DELETE /questions/<id>` - Delete any question
- `GET /quiz/<id>/summary` - Analytics for any quiz

---

## 11. Frontend Access Control

### Router Configuration
```javascript
// Multi-role routes
{
  path: '/admin_dashboard',
  meta: { requiresAuth: true, roles: ['admin', 'quiz_master'] }
}

// Admin-only routes
{
  path: '/admin/users',
  meta: { requiresAuth: true, role: 'admin' }
}

// Navigation guard
router.beforeEach((to, from, next) => {
  const userRole = getUserRole();
  
  // Check role array
  if (to.meta.roles && !to.meta.roles.includes(userRole)) {
    return next('/');  // Redirect if unauthorized
  }
  
  next();
});
```

### Component-Level Access Control
```vue
<template>
  <!-- Hide Users tab for quiz masters -->
  <router-link v-if="isAdmin" to="/admin/users">Users</router-link>
  
  <!-- Hide Delete button for quiz masters -->
  <button v-if="isAdmin" @click="deleteQuiz">Delete</button>
</template>

<script>
computed: {
  isAdmin() {
    return localStorage.getItem('role') === 'admin';
  },
  isQuizMaster() {
    return localStorage.getItem('role') === 'quiz_master';
  }
}
</script>
```

---

## Conclusion

This Access Control implementation successfully provides:

✅ **3 Distinct Roles** (User, Quiz Master, Admin)  
✅ **3+ Subjects** (User accounts, Quiz creators, System administrators)  
✅ **7+ Objects** (Subjects, Chapters, Quizzes, Questions, Users, Scores, Analytics)  
✅ **Clear Policy Justifications** for each permission  
✅ **Programmatic Enforcement** via decorators, database filters, and ownership checks  
✅ **Scalable Content Management** through Quiz Master role  
✅ **Admin Oversight** for system integrity  
✅ **Defense in Depth** with multiple security layers  
✅ **Audit Trail** through quiz ownership tracking

The system balances **security**, **usability**, and **scalability** while maintaining clear accountability through comprehensive access control policies.

---

**Implementation Date**: January 15, 2026  
**Status**: Fully Implemented and Tested ✅
