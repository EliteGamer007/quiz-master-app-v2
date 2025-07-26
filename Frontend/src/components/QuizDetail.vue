<template>
  <div class="quiz-detail-page">
    <div class="navbar">
        <div class="logo_box">QuizMaster</div>
    </div>
    <div class="page_wrapper" v-if="quiz">
      <div class="header-controls">
        <h2>{{ quiz.title }} - Questions</h2>
        <button class="primary-btn" @click="openQuestionModal()">Add Question</button>
      </div>
      <div class="questions-list">
        <div v-for="(question, index) in quiz.questions" :key="question.id" class="question-item">
          <img v-if="question.image_url" :src="getImageUrl(question.image_url)" alt="Question Image" class="question-image"/>
          <p><strong>Q{{ index + 1 }}:</strong> {{ question.question_text }}</p>
          <ul>
            <li :class="{ correct: question.correct_option === 'A' }">A: {{ question.option_a }}</li>
            <li :class="{ correct: question.correct_option === 'B' }">B: {{ question.option_b }}</li>
            <li :class="{ correct: question.correct_option === 'C' }">C: {{ question.option_c }}</li>
            <li :class="{ correct: question.correct_option === 'D' }">D: {{ question.option_d }}</li>
          </ul>
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
        
        <label>Question Image (Optional):</label>
        <img v-if="modal.data.image_url && !modal.file" :src="getImageUrl(modal.data.image_url)" class="modal-image-preview"/>
        <input type="file" @change="handleFileUpload" accept="image/*" />

        <input v-model="modal.data.option_a" placeholder="Option A" />
        <input v-model="modal.data.option_b" placeholder="Option B" />
        <input v-model="modal.data.option_c" placeholder="Option C" />
        <input v-model="modal.data.option_d" placeholder="Option D" />
        <select v-model="modal.data.correct_option">
          <option value="A">A</option>
          <option value="B">B</option>
          <option value="C">C</option>
          <option value="D">D</option>
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
        data: { question_text: '', image_url: null, option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'A' },
        file: null
      },
      // CORRECTED: Define backend URL in one place
      backendUrl: 'http://localhost:8000'
    };
  },
  methods: {
    // CORRECTED: Helper to construct full image URLs
    getImageUrl(path) {
      if (!path) return '';
      return `${this.backendUrl}${path}`;
    },
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
        
        // CORRECTED: Use the backendUrl data property
        const response = await fetch(`${this.backendUrl}${endpoint}`, config);
        if (!response.ok && response.status !== 204) {
             const errorData = await response.text();
             console.error('API Error Response:', errorData);
             throw new Error('API call failed');
        }
        if (response.status === 204) return;
        return response.json();
    },
    async fetchQuizDetails() {
        const quizId = this.$route.params.quizId;
        this.quiz = await this.apiCall(`/api/admin/quizzes/${quizId}`);
    },
    openQuestionModal(question = null) {
        if (question) {
            this.modal.isEdit = true;
            this.modal.data = { ...question };
        } else {
            this.modal.isEdit = false;
            this.modal.data = { question_text: '', image_url: null, option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'A' };
        }
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
        const quizId = this.quiz.id;
        const endpoint = isEdit ? `/api/admin/questions/${data.id}` : `/api/admin/quizzes/${quizId}/questions`;
        const method = isEdit ? 'PUT' : 'POST';

        const formData = new FormData();
        Object.keys(data).forEach(key => {
            if (key !== 'id' && key !== 'image_url' && data[key] !== null) {
                formData.append(key, data[key]);
            }
        });
        if (this.modal.file) {
            formData.append('image', this.modal.file);
        }

        try {
            const result = await this.apiCall(endpoint, method, formData);

            if (isEdit) {
                await this.fetchQuizDetails(); 
            } else {
                this.quiz.questions.push(result);
            }
            this.closeQuestionModal();
        } catch (error) {
            console.error("Failed to submit question:", error);
            // Optionally, show an error to the user here.
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

<style>
@import '../assets/website_styles.css';

.question-image {
  max-width: 200px;
  max-height: 150px;
  border-radius: 4px;
  margin-bottom: 10px;
  display: block;
}

.modal-image-preview {
  max-width: 100px;
  border-radius: 4px;
  margin: 5px 0;
}
</style>