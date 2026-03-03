<template>
  <div class="user-dashboard">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/dashboard">Home</router-link>
        <router-link to="/search">Search</router-link>
        <router-link to="/profile">Profile</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper">
      <h1 class="welcome-header">Welcome, {{ userName }}!</h1>
      
      <div v-if="isLoading" class="loading">Loading...</div>
      
      <div v-else>
        <div class="recommended-section">
          <h2>Recommended for You</h2>
          <div class="quizzes-grid">
            <div v-for="quiz in recommendedQuizzes" :key="quiz.id" class="quiz-card">
              <router-link :to="`/quiz/info/${quiz.id}`">{{ quiz.title }}</router-link>
            </div>
          </div>
        </div>

        <h2 class="all-subjects-header">All Subjects</h2>
        <div class="subject-accordion">
          <div v-for="subject in subjects" :key="subject.id" class="subject-item">
            <div class="subject-header" @click="toggleSubject(subject)">
              <h3>{{ subject.title }}</h3>
              <p>{{ subject.description }}</p>
            </div>
            <div class="accordion-content" :class="{ open: openSubjectId === subject.id }">
              <div v-if="subject.chapters && subject.chapters.length" class="chapter-list">
                <div v-for="chapter in subject.chapters" :key="chapter.id" class="chapter-item">
                  <h4 @click="toggleChapter(chapter)">{{ chapter.heading }}</h4>
                  <div class="quizzes-grid" v-if="openChapterId === chapter.id && chapter.quizzes">
                    <div v-for="quiz in chapter.quizzes" :key="quiz.id" class="quiz-card">
                      <router-link :to="`/quiz/info/${quiz.id}`">{{ quiz.title }}</router-link>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else-if="subject.chapters === undefined" class="loading-small">Loading chapters...</div>
              <div v-else class="loading-small">No chapters found for this subject.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserDashboard',
  data() {
    return {
      subjects: [],
      recommendedQuizzes: [],
      userName: '',
      isLoading: true,
      openSubjectId: null,
      openChapterId: null,
    };
  },
  methods: {
    async logout() {
      const accessToken = localStorage.getItem('token');
      try {
        if (accessToken) {
          await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            }
          });
        }
      } catch (error) {
        console.error('Logout request failed:', error);
      }
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      localStorage.removeItem('user_name');
      this.$router.push('/');
    },
    async fetchDashboardData() {
      this.isLoading = true;
      try {
        const [subjectsRes, recommendedRes] = await Promise.all([
          this.apiCall('/api/user/subjects'),
          this.apiCall('/api/user/recommended-quizzes')
        ]);
        this.subjects = subjectsRes;
        this.recommendedQuizzes = recommendedRes;
      } catch (error) {
        console.error(error);
      } finally {
        this.isLoading = false;
      }
    },
    async apiCall(endpoint) {
        const res = await fetch(endpoint, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!res.ok) throw new Error('API call failed');
        return res.json();
    },
    toggleSubject(subject) {
      if (this.openSubjectId === subject.id) {
        this.openSubjectId = null;
        return;
      }
      this.openSubjectId = subject.id;
      this.openChapterId = null;
      if (subject.chapters === undefined) {
        this.fetchChaptersForSubject(subject);
      }
    },
    async fetchChaptersForSubject(subject) {
      try {
        const res = await fetch(`/api/user/subjects/${subject.id}/chapters`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        subject.chapters = await res.json();
      } catch (error) {
        console.error('Error loading chapters:', error);
        subject.chapters = [];
      }
    },
    toggleChapter(chapter) {
      if (this.openChapterId === chapter.id) {
        this.openChapterId = null;
        return;
      }
      this.openChapterId = chapter.id;
      if (!chapter.quizzes) {
         this.fetchQuizzesForChapter(chapter);
      }
    },
    async fetchQuizzesForChapter(chapter) {
      try {
        const res = await fetch(`/api/user/chapters/${chapter.id}/quizzes`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        chapter.quizzes = await res.json();
      } catch (error) {
        console.error('Error loading quizzes:', error);
        chapter.quizzes = [];
      }
    }
  },
  mounted() {
    this.userName = localStorage.getItem('user_name') || 'User';
    this.fetchDashboardData();
  }
};
</script>

<style scoped>
@import '../assets/user_styles.css';

.welcome-header {
    color: #fff;
    margin-bottom: 2rem;
}
.recommended-section {
    background-color: rgba(0,0,0,0.1);
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}
.recommended-section h2 {
    color: #fff;
    margin-top: 0;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.2);
}
.recommended-section .quizzes-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}
.recommended-section .quiz-card {
    background-color: #5e10f0;
    border-color: #790bf7;
}
.recommended-section .quiz-card a {
    color: #ddd6fe;
}
.recommended-section .quiz-card:hover {
    background-color: #790bf7;
    border-color: #a78bfa;
}
.all-subjects-header {
    color: #fff;
    margin-bottom: 1.5rem;
}
</style>