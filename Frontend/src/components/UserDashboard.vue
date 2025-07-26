<template>
  <div class="user-dashboard">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper">
      <div class="header-controls">
        <h2>Browse Quizzes</h2>
      </div>

      <div class="subjects-grid" v-if="subjects.length">
        <div v-for="subject in subjects" :key="subject.id" class="subject-card clickable" @click="selectSubject(subject.id)">
          <h3>{{ subject.title }}</h3>
          <p>{{ subject.description }}</p>
        </div>
      </div>

      <div v-if="chapters.length">
        <h3>Chapters in {{ selectedSubjectTitle }}</h3>
        <div class="subjects-grid">
          <div v-for="chapter in chapters" :key="chapter.id" class="subject-card clickable" @click="selectChapter(chapter.id)">
            <h4>{{ chapter.heading }}</h4>
            <p>{{ chapter.level }}</p>
          </div>
        </div>
      </div>

      <div v-if="quizzes.length">
        <h3>Quizzes in {{ selectedChapterTitle }}</h3>
        <div class="subjects-grid">
          <div v-for="quiz in quizzes" :key="quiz.id" class="subject-card clickable">
            <router-link :to="`/quiz/${quiz.id}`" class="subject-card-link">
              <h4>{{ quiz.title }}</h4>
              <p>{{ quiz.description }}</p>
            </router-link>
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
      chapters: [],
      quizzes: [],
      selectedSubjectId: '',
      selectedChapterId: '',
      selectedSubjectTitle: '',
      selectedChapterTitle: '',
      isLoading: true
    };
  },
  methods: {
    logout() {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      this.$router.push('/');
    },
    async fetchSubjects() {
      try {
        const response = await fetch('/api/user/subjects', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        if (!response.ok) throw new Error('Unauthorized');
        this.subjects = await response.json();
      } catch (error) {
        console.error('Error fetching subjects:', error);
        this.logout();
      } finally {
        this.isLoading = false;
      }
    },
    async selectSubject(subjectId) {
      this.selectedSubjectId = subjectId;
      this.chapters = [];
      this.quizzes = [];
      const subject = this.subjects.find(s => s.id === subjectId);
      this.selectedSubjectTitle = subject ? subject.title : '';
      try {
        const res = await fetch(`/api/user/subjects/${subjectId}/chapters`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        this.chapters = await res.json();
      } catch (error) {
        console.error('Error loading chapters:', error);
      }
    },
    async selectChapter(chapterId) {
      this.selectedChapterId = chapterId;
      this.quizzes = [];
      const chapter = this.chapters.find(c => c.id === chapterId);
      this.selectedChapterTitle = chapter ? chapter.heading : '';
      try {
        const res = await fetch(`/api/user/chapters/${chapterId}/quizzes`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        this.quizzes = await res.json();
      } catch (error) {
        console.error('Error loading quizzes:', error);
      }
    }
  },
  mounted() {
    this.fetchSubjects();
  }
};
</script>

<style scoped>
@import '../assets/website_styles.css';

.clickable {
  cursor: pointer;
}
</style>
