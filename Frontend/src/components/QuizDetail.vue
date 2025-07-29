<template>
  <div class="quiz-detail-page admin-page">
    <div class="navbar">
        <div class="logo_box">QuizMaster</div>
        <div class="navbar-center">
          <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        </div>
    </div>
    <div class="page_wrapper" v-if="quiz">
      <div class="header-controls">
        <h2>{{ quiz.title }} - Questions</h2>
        <button class="primary-btn" @click="openQuestionModal()">Add Question</button>
      </div>

      <div class="summary-section">
          <h3>Quiz Summary</h3>
          <div class="summary-grid">
              <div><strong>Top 5 Scores</strong>
                <ul v-if="summary.top_scores.length">
                    <li v-for="(s, i) in summary.top_scores" :key="i">{{s.user_name}}: {{s.score}}/{{s.max_score}}</li>
                </ul>
                <p v-else>No scores yet.</p>
              </div>
              <div><strong>Total Attempts</strong><p>{{summary.total_attempts}}</p></div>
              <div><strong>Overall Accuracy</strong><p>{{summary.accuracy}}%</p></div>
          </div>
      </div>

      <div class="questions-list">
        <div v-for="(question, index) in quiz.questions" :key="question.id" class="admin-card">
          <div class="admin-card-link">
            <img v-if="question.image_url" :src="question.image_url" class="question-image"/>
            <p><strong>Q{{ index + 1 }}:</strong> {{ question.question_text }}</p>
            <ul>
              <li :class="{ correct: question.correct_option === 'A' }">A: {{ question.option_a }}</li>
              <li :class="{ correct: question.correct_option === 'B' }">B: {{ question.option_b }}</li>
              <li :class="{ correct: question.correct_option === 'C' }">C: {{ question.option_c }}</li>
              <li :class="{ correct: question.correct_option === 'D' }">D: {{ question.option_d }}</li>
            </ul>
          </div>
          <div class="card-actions">
            <button class="edit-btn" @click="openQuestionModal(question)">Edit</button>
            <button class="delete-btn" @click="confirmDelete(question)">Delete</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showQuestionModal" class="modal-overlay">
      <div class="modal-content">
        <h4>{{ modal.isEdit ? 'Edit Question' : 'Add New Question' }}</h4>
        <textarea v-model="modal.data.question_text" placeholder="Question Text"></textarea>
        <input type="file" @change="handleFileUpload" accept="image/*" />
        <input v-model="modal.data.option_a" placeholder="Option A" />
        <input v-model="modal.data.option_b" placeholder="Option B" />
        <input v-model="modal.data.option_c" placeholder="Option C" />
        <input v-model="modal.data.option_d" placeholder="Option D" />
        <select v-model="modal.data.correct_option">
          <option value="A">A</option> <option value="B">B</option>
          <option value="C">C</option> <option value="D">D</option>
        </select>
        <div class="modal-actions">
          <button @click="handleQuestionSubmit">{{ modal.isEdit ? 'Save Changes' : 'Add Question' }}</button>
          <button @click="closeQuestionModal">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'QuizDetail',
  data() {
    return {
      quiz: null,
      summary: { top_scores: [], total_attempts: 0, accuracy: 0 },
      showQuestionModal: false,
      modal: {
        isEdit: false,
        data: { question_text: '', option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'A' },
        file: null
      },
    };
  },
  methods: {
    async apiCall(endpoint, method = 'GET', body = null) {
        const headers = { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
        const config = { method, headers };
        if (body) {
          if (body instanceof FormData) {
            config.body = body;
          } else {
            headers['Content-Type'] = 'application/json';
            config.body = JSON.stringify(body);
          }
        }
        const response = await fetch(endpoint, config);
        if (!response.ok && response.status !== 204) throw new Error('API call failed');
        if (response.status === 204) return;
        return response.json();
    },
    async fetchQuizDetails() {
        const quizId = this.$route.params.quizId;
        this.quiz = await this.apiCall(`/api/admin/quizzes/${quizId}`);
        this.summary = await this.apiCall(`/api/admin/quiz/${quizId}/summary`);
    },
    openQuestionModal(question = null) {
        this.modal.isEdit = !!question;
        this.modal.data = question ? { ...question } : { question_text: '', option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'A' };
        this.modal.file = null;
        this.showQuestionModal = true;
    },
    closeQuestionModal() {
        this.showQuestionModal = false;
    },
    handleFileUpload(event) {
      this.modal.file = event.target.files[0];
    },
    async handleQuestionSubmit() {
        const { isEdit, data } = this.modal;
        const endpoint = isEdit ? `/api/admin/questions/${data.id}` : `/api/admin/quizzes/${this.quiz.id}/questions`;
        const method = isEdit ? 'PUT' : 'POST';
        const formData = new FormData();
        for (const key in data) {
            if (data[key] !== null && key !== 'image_url') {
                formData.append(key, data[key]);
            }
        }
        if (this.modal.file) {
            formData.append('image', this.modal.file);
        }
        try {
            await this.apiCall(endpoint, method, formData);
            await this.fetchQuizDetails();
            this.closeQuestionModal();
        } catch (error) {
            console.error("Failed to submit question:", error);
        }
    },
    confirmDelete(question) {
        if (confirm(`Delete this question?`)) {
            this.deleteQuestion(question.id);
        }
    },
    async deleteQuestion(id) {
        await this.apiCall(`/api/admin/questions/${id}`, 'DELETE');
        this.quiz.questions = this.quiz.questions.filter(q => q.id !== id);
    }
  },
  mounted() {
    this.fetchQuizDetails();
  }
};
</script>
<style scoped>
@import '../assets/website_styles.css';
.summary-section {
    background-color: #5e10f0;
    color: #fff;
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}
.summary-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    text-align: center;
}
.summary-grid ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
}
.question-image {
    max-width: 100px;
    border-radius: 4px;
    margin-bottom: 1rem;
}
</style>