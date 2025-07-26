import { createRouter, createWebHistory } from 'vue-router';
import LoginForm from '../components/LoginForm.vue';
import RegisterForm from '../components/RegisterForm.vue';
import AdminDashboard from '../components/AdminDashboard.vue';
import UserDashboard from '../components/UserDashboard.vue';
import SubjectDetail from '../components/SubjectDetail.vue';
import ChapterDetail from '../components/ChapterDetail.vue';
import QuizDetail from '../components/QuizDetail.vue';
import UserManagement from '../components/UserManagement.vue';

const routes = [
  { path: '/', component: LoginForm, alias: '/login' },
  { path: '/register', component: RegisterForm },
  {
    path: '/admin_dashboard',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/dashboard',
    name: 'UserDashboard',
    component: UserDashboard,
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

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');

  if (to.meta.requiresAuth) {
    if (!token) {
      return next('/');
    }
    try {
      const payloadBase64 = token.split('.')[1];
      const decodedPayload = JSON.parse(atob(payloadBase64));
      const identity = decodedPayload.sub;
      
      const userRole = typeof identity === 'object' && identity.role ? identity.role : identity;

      if (to.meta.role && userRole !== to.meta.role) {
        return next('/');
      }
    } catch (e) {
      localStorage.removeItem('token');
      return next('/');
    }
  }
  next();
});

export default router;