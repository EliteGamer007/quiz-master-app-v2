<template>
  <div class="quiz-attempt-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <router-link to="/dashboard" class="logout_link">Exit Quiz</router-link>
    </div>

    <div v-if="!quiz" class="loading-container">
      <div class="spinner-border text-light" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <div v-else class="quiz-main-content">
      <div class="question-header">
        Question {{ currentQuestionIndex + 1 }} of {{ quiz.questions.length }}
      </div>

      <div class="question-body">
        <p class="question-text">{{ currentQuestion.question_text }}</p>

        <div class="options-grid">
          <button
            v-for="option in ['A', 'B', 'C', 'D']"
            :key="option"
            class="option-btn"
            :class="getOptionClass(option)"
            @click="selectOption(option)"
            :disabled="selectedOption !== null"
          >
            {{ currentQuestion['option_' + option.toLowerCase()] }}
          </button>
        </div>
      </div>

      <div class="quiz-footer">
        <div class="timer-bar">
          <div class="timer-fill" :style="{ width: timerWidth + '%' }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuizAttempt',
  data() {
    return {
      quiz: null,
      currentQuestionIndex: 0,
      selectedOption: null,
      timerWidth: 100,
      timerInterval: null,
      userAnswers: {}
    };
  },
  computed: {
    currentQuestion() {
      if (!this.quiz) return null;
      return this.quiz.questions[this.currentQuestionIndex];
    }
  },
  methods: {
    async fetchQuiz() {
      try {
        const res = await fetch(`/api/user/quiz/${this.$route.params.quizId}/questions`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        this.quiz = await res.json();
        this.startTimer();
      } catch (error) {
        console.error("Failed to fetch quiz:", error);
      }
    },
    selectOption(option) {
      this.selectedOption = option;
      this.userAnswers[this.currentQuestion.id] = option;
      setTimeout(() => {
        if (this.currentQuestionIndex + 1 < this.quiz.questions.length) {
          this.currentQuestionIndex++;
          this.selectedOption = null;
        } else {
          this.submitQuiz();
        }
      }, 1200);
    },
    startTimer() {
      const startTime = Date.now();
      const limit = this.quiz.time_limit * 60;
      this.timerInterval = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        this.timerWidth = Math.max(0, 100 - (elapsed / limit) * 100);
        if (this.timerWidth <= 0) {
          this.submitQuiz();
        }
      }, 100);
    },
    getOptionClass(option) {
      if (this.selectedOption === null) return '';
      if (option === this.currentQuestion.correct_option) return 'correct';
      if (option === this.selectedOption) return 'wrong';
      return '';
    },
    async submitQuiz() {
      clearInterval(this.timerInterval);
      const res = await fetch(`/api/user/quiz/${this.quiz.quiz_id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ answers: this.userAnswers })
      });
      const result = await res.json();
      alert(`Quiz complete! You scored ${result.total_score} out of ${result.max_score}`);
      this.$router.push('/dashboard');
    }
  },
  beforeUnmount() {
    clearInterval(this.timerInterval);
  },
  mounted() {
    this.fetchQuiz();
  }
};
</script>

<style scoped>
@import '../assets/website_styles.css';
</style>