<template>
  <div class="profile-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/dashboard">Home</router-link>
        <router-link to="#">Search</router-link>
        <router-link to="/profile">Profile</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper">
      <div v-if="isLoading" class="loading">Loading Profile...</div>
      <div v-else>
        <div class="summary-section">
          <h2 class="section-title">Performance Summary</h2>
          <div class="summary-grid">
            <div>
              <div class="stat-value">{{ totalQuizzesTaken }}</div>
              <div class="stat-label">Quizzes Taken</div>
            </div>
            <div>
              <div class="stat-value">{{ correctAnswersPerQuiz }}</div>
              <div class="stat-label">Correct Answers / Quiz</div>
            </div>
            <div>
              <div class="stat-value">{{ averageScore }}%</div>
              <div class="stat-label">Average Score</div>
            </div>
          </div>
        </div>

        <div class="history-section">
          <h2 class="section-title">Quiz History</h2>
          <table class="history-table">
            <thead>
              <tr>
                <th>Quiz Title</th>
                <th>Score</th>
                <th>Date Attempted</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="scores.length === 0">
                <td colspan="3">You have not attempted any quizzes yet.</td>
              </tr>
              <tr v-for="(score, index) in scores" :key="index">
                <td>
                  <router-link :to="`/quiz/attempt/${score.quiz_id}`">
                    {{ score.quiz_title }}
                  </router-link>
                </td>
                <td>{{ score.score }} / {{ score.max_score }}</td>
                <td>{{ formatDate(score.date) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProfilePage',
  data() {
    return {
      scores: [],
      isLoading: true,
    };
  },
  computed: {
    totalQuizzesTaken() {
      return this.scores.length;
    },
    totalCorrectAnswers() {
      return this.scores.reduce((sum, s) => sum + s.score, 0);
    },
    correctAnswersPerQuiz() {
      if (this.scores.length === 0) return '0.0';
      return (this.totalCorrectAnswers / this.totalQuizzesTaken).toFixed(1);
    },
    averageScore() {
      if (this.scores.length === 0) return 0;
      const totalPossible = this.scores.reduce((sum, s) => sum + s.max_score, 0);
      return totalPossible > 0 ? ((this.totalCorrectAnswers / totalPossible) * 100).toFixed(2) : 0;
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('token');
      this.$router.push('/');
    },
    async fetchScores() {
      this.isLoading = true;
      try {
        const res = await fetch('/api/user/scores', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!res.ok) throw new Error('Failed to fetch scores');
        this.scores = await res.json();
      } catch (error) {
        console.error(error);
      } finally {
        this.isLoading = false;
      }
    },
    formatDate(dateString) {
      const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    }
  },
  mounted() {
    this.fetchScores();
  }
};
</script>

<style scoped>
@import '../assets/user_styles.css';

.summary-section, .history-section {
  padding: 2rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  color: #000000;
}
.section-title {
    border-bottom: 2px solid rgba(255, 255, 255, 0.5);
    padding-bottom: 0.5rem;
    display: inline-block;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  text-align: center;
  gap: 1rem;
  margin-top: 1.5rem;
}
.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
}
.stat-label {
  color: #e3e3e3;
}
.history-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1.5rem;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}
.history-table th, .history-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  text-align: left;
}
.history-table th {
  background-color: rgba(0, 0, 0, 0.2);
}
.history-table tbody tr:last-child td {
  border-bottom: none;
}
.history-table a {
    color: #fff;
    text-decoration: underline;
    font-weight: 500;
}
</style>