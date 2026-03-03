import { createRouter, createWebHistory } from 'vue-router';
import LoginForm from '../components/LoginForm.vue';
import RegisterForm from '../components/RegisterForm.vue';
import ForgotPassword from '../components/ForgotPassword.vue';
import AdminDashboard from '../components/AdminDashboard.vue';
import UserDashboard from '../components/UserDashboard.vue';
import SubjectDetail from '../components/SubjectDetail.vue';
import ChapterDetail from '../components/ChapterDetail.vue';
import QuizDetail from '../components/QuizDetail.vue';
import UserManagement from '../components/UserManagement.vue';
import QuizAttempt from '../components/QuizAttempt.vue';
import ProfilePage from '../components/ProfilePage.vue';
import QuizInfoPage from '../components/QuizInfoPage.vue';
import SearchPage from '../components/SearchPage.vue';
import AnalyticsDashboard from '../components/AnalyticsDashboard.vue';

const routes = [
  { path: '/', component: LoginForm, alias: '/login' },
  { path: '/register', component: RegisterForm },
  { path: '/forgot-password', component: ForgotPassword },
  {
    path: '/admin_dashboard',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, role: ['admin', 'quiz_master'] }
  },
  {
    path: '/admin/analytics',
    name: 'AnalyticsDashboard',
    component: AnalyticsDashboard,
    meta: { requiresAuth: true, role: ['admin', 'quiz_master'] }
  },
  {
    path: '/dashboard',
    name: 'UserDashboard',
    component: UserDashboard,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/quiz/info/:quizId',
    name: 'QuizInfoPage',
    component: QuizInfoPage,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/quiz/attempt/:quizId',
    name: 'QuizAttempt',
    component: QuizAttempt,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/profile',
    name: 'ProfilePage',
    component: ProfilePage,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/search',
    name: 'SearchPage',
    component: SearchPage,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/admin/users',
    name: 'UserManagement',
    component: UserManagement,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/subjects/:subjectId',
    name: 'SubjectDetail',
    component: SubjectDetail,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/chapters/:chapterId',
    name: 'ChapterDetail',
    component: ChapterDetail,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/quizzes/:quizId',
    name: 'QuizDetail',
    component: QuizDetail,
    meta: { requiresAuth: true, role: 'admin' }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

function parseJwtPayload(token) {
  const parts = token.split('.');
  if (parts.length < 2) {
    throw new Error('Invalid JWT token format');
  }

  const base64Url = parts[1];
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const paddedBase64 = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
  return JSON.parse(atob(paddedBase64));
}

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  if (to.meta.requiresAuth) {
    if (!token) {
      return next('/');
    }
    try {
      const decodedPayload = parseJwtPayload(token);
      const identity = decodedPayload.identity;
      const userRole = typeof identity === 'object' && identity.role ? identity.role : identity;
      const allowedRoles = to.meta.role;
      if (allowedRoles) {
        const rolesArray = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
        if (!rolesArray.includes(userRole)) {
          return next('/');
        }
      }
    } catch (e) {
      localStorage.removeItem('token');
      return next('/');
    }
  }
  next();
});

export default router;