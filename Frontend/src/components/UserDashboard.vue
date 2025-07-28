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
      <div v-if="isLoading" class="loading">Loading...</div>
      <div v-else class="subject-accordion">
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
</template>

<script>
export default {
  name: 'UserDashboard',
  data() {
    return {
      subjects: [],
      isLoading: true,
      openSubjectId: null,
      openChapterId: null,
    };
  },
  methods: {
    logout() {
      localStorage.removeItem('token');
      this.$router.push('/');
    },
    async fetchSubjects() {
      this.isLoading = true;
      try {
        const response = await fetch('/api/user/subjects', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!response.ok) throw new Error('Failed to fetch subjects');
        this.subjects = await response.json();
      } catch (error) {
        console.error(error);
      } finally {
        this.isLoading = false;
      }
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
    this.fetchSubjects();
  }
};
</script>

<style scoped>
@import '../assets/user_styles.css';
</style>