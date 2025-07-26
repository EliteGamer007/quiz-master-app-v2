fileName: components/ChapterDetail.vue
<template>
  <div class="chapter-detail-page">
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

      <div class="quizzes-grid">
        <template v-if="chapterData.quizzes && chapterData.quizzes.length > 0">
          <div v-for="quiz in chapterData.quizzes" :key="quiz.id" class="quiz-card">
            <router-link :to="{ name: 'QuizDetail', params: { quizId: quiz.id } }" class="quiz-card-link">
              <h4>{{ quiz.title }}</h4>
              <p class="quiz-description">{{ quiz.description }}</p>
              <div class="quiz-meta">
                <span><strong>Time Limit:</strong> {{ quiz.time_limit }} mins</span>
                <span><strong>Rating:</strong> {{ quiz.rating || 'N/A' }} &#9733;</span>
              </div>
              <div class="quiz-footer">
                <span v-if="quiz.start_time"><strong>Starts:</strong> {{ formatDateTime(quiz.start_time) }}</span>
                <span v-else><strong>Starts:</strong> Not scheduled</span>
              </div>
            </router-link>
             <div class="card-actions">
              <button class="edit-btn" @click="openQuizModal(quiz)">Edit</button>
              <button class="delete-btn" @click="confirmDeleteQuiz(quiz)">Delete</button>
            </div>
          </div>
        </template>
        <p v-else class="no-quizzes">No quizzes have been added to this chapter yet.</p>
      </div>
    </div>
    <div v-else class="loading">Loading chapter details...</div>

    <div v-if="showQuizModal" class="modal-overlay">
      <div class="modal-content">
        <h4>{{ modal.isEdit ? 'Edit Quiz' : 'Add New Quiz' }}</h4>
        <input v-model="modal.data.title" type="text" placeholder="Quiz Title" />
        <textarea v-model="modal.data.description" placeholder="Description"></textarea>
        <input v-model.number="modal.data.time_limit" type="number" placeholder="Time Limit (minutes)" />
        
        <label for="start_time">Start Time (Optional)</label>
        <input v-model="modal.data.start_time" id="start_time" type="datetime-local" />

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
        data: { id: null, title: '', description: '', time_limit: null, start_time: '' }
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
      if (!response.ok) throw new Error(`API call to ${endpoint} failed`);
      if (response.status === 204) return;
      return response.json();
    },
    async fetchChapterDetails() {
      const chapterId = this.$route.params.chapterId;
      try {
        this.chapterData = await this.apiCall(`/api/admin/chapters/${chapterId}/quizzes`);
      } catch (err) {
        console.error(err);
        this.$router.go(-1);
      }
    },
    formatDateTime(dateTimeString) {
      if (!dateTimeString) return 'N/A';
      const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateTimeString).toLocaleString(undefined, options);
    },
    formatForInput(dateTimeString) {
        if (!dateTimeString) return '';
        const date = new Date(dateTimeString);
        const timezoneOffset = date.getTimezoneOffset() * 60000;
        const localDate = new Date(date.getTime() - timezoneOffset);
        return localDate.toISOString().slice(0, 16);
    },
    openQuizModal(quiz = null) {
      if (quiz) {
        this.modal.isEdit = true;
        this.modal.data = { ...quiz, start_time: this.formatForInput(quiz.start_time) };
      } else {
        this.modal.isEdit = false;
        this.modal.data = { id: null, title: '', description: '', time_limit: null, start_time: '' };
      }
      this.showQuizModal = true;
    },
    closeQuizModal() {
      this.showQuizModal = false;
    },
    async handleQuizSubmit() {
      const { isEdit, data } = this.modal;
      const submissionData = {
          ...data,
          start_time: data.start_time ? data.start_time : null
      };

      const chapterId = this.chapterData.chapter_id;
      const endpoint = isEdit ? `/api/admin/quizzes/${data.id}` : `/api/admin/chapters/${chapterId}/quizzes`;
      const method = isEdit ? 'PUT' : 'POST';
      
      try {
        await this.apiCall(endpoint, method, submissionData);
        await this.fetchChapterDetails();
        this.closeQuizModal();
      } catch (error) {
        console.error(error);
        alert('Failed to save the quiz. Please check the console for errors.');
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

<style>
@import '../assets/website_styles.css';
</style>