<template>
  <div class="quiz-attempt">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <router-link to="/dashboard" class="logout_link">Back to Dashboard</router-link>
    </div>

    <div class="page_wrapper" v-if="quiz">
      <h2>{{ quiz.quiz_title }}</h2>

      <div class="question-box">
        <h3>Question {{ currentQuestionIndex + 1 }} of {{ quiz.questions.length }}</h3>
        <p>{{ currentQuestion.question_text }}</p>

        <div class="options-grid">
          <button
            v-for="option in ['A', 'B', 'C', 'D']"
            :key="option"
            :class="optionButtonClass(option)"
            @click="selectOption(option)"
            :disabled="selectedOption !== null"
          >
            {{ currentQuestion['option_' + option.toLowerCase()] }}
          </button>
        </div>

        <div class="question-controls" v-if="selectedOption">
          <p v-if="isCorrectOption(currentQuestion, selectedOption)" class="correct-msg">Correct!</p>
          <p v-else class="wrong-msg">Wrong! Correct answer: {{ currentQuestion.correct_option }}</p>
          <button @click="nextQuestion">Next</button>
        </div>
      </div>

      <div class="timer-bar">
        <div class="timer-fill" :style="{ width: timerWidth + '%' }"></div>
      </div>
    </div>

    <div class="loading" v-else>
      Loading quiz...
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
      timer: 0,
      timerWidth: 100,
      timerInterval: null,
      score: 0,
      startTime: null
    };
  },
  computed: {
    currentQuestion() {
      return this.quiz.questions[this.currentQuestionIndex];
    }
  },
  methods: {
    async fetchQuiz() {
      const res = await fetch(`/api/user/quiz/${this.$route.params.quizId}/questions`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      this.quiz = await res.json();
      this.startTime = Date.now();
      this.startTimer();
    },
    selectOption(option) {
      this.selectedOption = option;
      if (this.isCorrectOption(this.currentQuestion, option)) this.score++;
    },
    nextQuestion() {
      if (this.currentQuestionIndex + 1 < this.quiz.questions.length) {
        this.currentQuestionIndex++;
        this.selectedOption = null;
        this.timerWidth = 100;
      } else {
        this.submitQuiz();
      }
    },
    startTimer() {
      const limit = this.quiz.time_limit * 60;
      this.timerInterval = setInterval(() => {
        const elapsed = (Date.now() - this.startTime) / 1000;
        this.timerWidth = Math.max(0, 100 - (elapsed / limit) * 100);
        if (elapsed >= limit) {
          clearInterval(this.timerInterval);
          this.submitQuiz();
        }
      }, 1000);
    },
    isCorrectOption(question, selected) {
      const correct = (question.correct_option || '').toString().trim().toUpperCase();
      const chosen = (selected || '').toString().trim().toUpperCase();
      return correct === chosen;
    },
    optionButtonClass(option) {
      if (this.selectedOption === null) return 'option-btn';
      if (option === this.selectedOption) {
        return this.isCorrectOption(this.currentQuestion, option) ? 'option-btn correct' : 'option-btn wrong';
      }
      if (option === (this.currentQuestion.correct_option || '').toUpperCase()) {
        return 'option-btn correct';
      }
      return 'option-btn';
    },
    async submitQuiz() {
      clearInterval(this.timerInterval);
      const elapsed_time = (Date.now() - this.startTime) / 1000;
      const answers = {};
      this.quiz.questions.forEach((q, i) => {
        if (i <= this.currentQuestionIndex) {
          answers[q.id] = i === this.currentQuestionIndex ? this.selectedOption : null;
        }
      });
      const res = await fetch(`/api/user/quiz/${this.quiz.quiz_id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ answers, elapsed_time })
      });
      const result = await res.json();
      alert(`Quiz complete! You scored ${result.total_score} out of ${result.max_score}`);
      this.$router.push('/dashboard');
    },
  },
  mounted() {
    this.fetchQuiz();
  }
};
</script>

<style scoped>
.quiz-attempt {
  max-width: 800px;
  margin: auto;
  padding: 20px;
}

.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

button.option-btn {
  font-size: 18px;
  padding: 20px;
  width: 100%;
  border-radius: 8px;
  background-color: #eee;
  border: 1px solid #ccc;
  transition: 0.3s;
  cursor: pointer;
}

button.option-btn.correct {
  background-color: #c8f7c5;
  border-color: #2e7d32;
}

button.option-btn.wrong {
  background-color: #f8d7da;
  border-color: #c62828;
}

.correct-msg {
  color: #2e7d32;
  font-weight: bold;
}

.wrong-msg {
  color: #c62828;
  font-weight: bold;
}

.timer-bar {
  margin-top: 30px;
  height: 15px;
  background-color: #eee;
  border-radius: 10px;
  overflow: hidden;
}

.timer-fill {
  height: 100%;
  background-color: #007bff;
  transition: width 1s linear;
}
</style>
