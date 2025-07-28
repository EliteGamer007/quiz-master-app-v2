<template>
  <div class="quiz-detail-page">
    <div class="navbar">
        <div class="logo_box">QuizMaster</div>
        <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        <a href="#" class="logout_link" @click.prevent="$router.go(-1)">&larr; Back</a>
    </div>
    <div class="page_wrapper" v-if="quiz">
      <div class="header-controls">
        <h2>{{ quiz.title }} - Questions</h2>
        <button class="primary-btn" @click="openQuestionModal()">Add Question</button>
      </div>
      <div class="questions-list">
        <div v-for="(question, index) in quiz.questions" :key="question.id" class="admin-card">
          <div class="admin-card-link">
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
      showQuestionModal: false,
      modal: {
        isEdit: false,
        data: { question_text: '', option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'A' },
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
    },
    openQuestionModal(question = null) {
        this.modal.isEdit = !!question;
        this.modal.data = question ? { ...question } : { question_text: '', option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'A' };
        this.showQuestionModal = true;
    },
    closeQuestionModal() {
        this.showQuestionModal = false;
    },
    async handleQuestionSubmit() {
        const { isEdit, data } = this.modal;
        const endpoint = isEdit ? `/api/admin/questions/${data.id}` : `/api/admin/quizzes/${this.quiz.id}/questions`;
        const method = isEdit ? 'PUT' : 'POST';
        const formData = new FormData();
        for (const key in data) {
            if (data[key] !== null) {
                formData.append(key, data[key]);
            }
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
</style>