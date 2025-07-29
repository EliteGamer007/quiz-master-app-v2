<template>
  <div class="chapter-detail-page admin-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
       <div class="navbar-center">
        <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        <router-link to="/admin/users" class="nav_link">Users</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper" v-if="chapterData">
      <div class="header-controls">
        <h2>Quizzes for: {{ chapterData.chapter_heading }}</h2>
        <button class="primary-btn" @click="openQuizModal()">+ Add Quiz</button>
      </div>

      <div class="admin-grid">
        <div v-for="quiz in chapterData.quizzes" :key="quiz.id" class="admin-card">
          <router-link :to="{ name: 'QuizDetail', params: { quizId: quiz.id } }" class="admin-card-link">
            <h4>{{ quiz.title }}</h4>
            <p>{{ quiz.description }}</p>
          </router-link>
           <div class="card-actions">
            <button class="edit-btn" @click="openQuizModal(quiz)">Edit</button>
            <button class="delete-btn" @click="confirmDeleteQuiz(quiz)">Delete</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showQuizModal" class="modal-overlay">
      <div class="modal-content">
        <h4>{{ modal.isEdit ? 'Edit Quiz' : 'Add New Quiz' }}</h4>
        <input v-model="modal.data.title" type="text" placeholder="Quiz Title" />
        <textarea v-model="modal.data.description" placeholder="Description"></textarea>
        <input v-model.number="modal.data.time_limit" type="number" placeholder="Time Limit (minutes)" />
        <label for="start_time">Start Time (Optional)</label>
        <input v-model="modal.data.start_time" id="start_time" type="datetime-local" />
        <div class="checkbox-container">
          <input type="checkbox" v-model="modal.data.one_attempt_only" id="one_attempt_only" />
          <label for="one_attempt_only">One Attempt Only</label>
        </div>
        <div class="modal-actions">
          <button @click="handleQuizSubmit">{{ modal.isEdit ? 'Save Changes' : 'Add Quiz' }}</button>
          <button @click="closeQuizModal">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'ChapterDetail',
  data() {
    return {
      chapterData: null,
      showQuizModal: false,
      modal: {
        isEdit: false,
        data: { id: null, title: '', description: '', time_limit: null, one_attempt_only: false, start_time: '' }
      }
    };
  },
  methods: {
    logout() {
      localStorage.removeItem('token');
      this.$router.push('/');
    },
    async apiCall(endpoint, method = 'GET', body = null) {
      const headers = { 'Authorization': `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' };
      const config = { method, headers, body: body ? JSON.stringify(body) : null };
      const response = await fetch(endpoint, config);
      if (!response.ok) throw new Error(`API call failed`);
      if (response.status === 204) return;
      return response.json();
    },
    async fetchChapterDetails() {
      const chapterId = this.$route.params.chapterId;
      try {
        this.chapterData = await this.apiCall(`/api/admin/chapters/${chapterId}/quizzes`);
      } catch (err) {
        console.error(err);
      }
    },
    formatForInput(dateTimeString) {
        if (!dateTimeString) return '';
        const date = new Date(dateTimeString);
        const timezoneOffset = date.getTimezoneOffset() * 60000;
        const localDate = new Date(date.getTime() - timezoneOffset);
        return localDate.toISOString().slice(0, 16);
    },
    openQuizModal(quiz = null) {
      this.modal.isEdit = !!quiz;
      this.modal.data = quiz ? { ...quiz, start_time: this.formatForInput(quiz.start_time) } : { id: null, title: '', description: '', time_limit: null, one_attempt_only: false, start_time: '' };
      this.showQuizModal = true;
    },
    closeQuizModal() {
      this.showQuizModal = false;
    },
    async handleQuizSubmit() {
      const { isEdit, data } = this.modal;
      const endpoint = isEdit ? `/api/admin/quizzes/${data.id}` : `/api/admin/chapters/${this.chapterData.chapter_id}/quizzes`;
      const method = isEdit ? 'PUT' : 'POST';
      try {
        await this.apiCall(endpoint, method, data);
        await this.fetchChapterDetails();
        this.closeQuizModal();
      } catch (error) {
        console.error(error);
      }
    },
    confirmDeleteQuiz(quiz) {
      if (confirm(`Are you sure you want to delete "${quiz.title}"?`)) {
        this.deleteQuiz(quiz.id);
      }
    },
    async deleteQuiz(id) {
      try {
        await this.apiCall(`/api/admin/quizzes/${id}`, 'DELETE');
        this.chapterData.quizzes = this.chapterData.quizzes.filter(q => q.id !== id);
      } catch (error) {
        console.error(error);
      }
    }
  },
  mounted() {
    this.fetchChapterDetails();
  }
};
</script>
<style scoped>
@import '../assets/website_styles.css';
.checkbox-container {
  display: flex;
  align-items: center;
  margin-top: 1rem;
}
.checkbox-container input {
  width: auto;
  margin-right: 0.5rem;
}
</style>