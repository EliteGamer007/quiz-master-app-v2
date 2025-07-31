<template>
  <div class="quiz-info-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/dashboard">Home</router-link>
        <router-link to="/profile">Profile</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="$router.push('/dashboard')">Back</a>
    </div>

    <div class="page_wrapper">
      <div v-if="isLoading" class="loading">Loading Quiz Info...</div>
      <div v-else class="info-container">
        <div class="info-header">
          <span class="breadcrumb">{{ info.subject }} / {{ info.chapter }}</span>
          <h1>{{ info.title }}</h1>
          <p class="description">{{ info.description }}</p>
          <div v-if="info.start_time_formatted" class="schedule-info">
            This is a scheduled quiz. It is available from <strong>{{ formatToIST(info.start_time_formatted) }}</strong> to <strong>{{ formatToIST(info.expiry_time_formatted) }}</strong> (IST).
          </div>
        </div>
        
        <div class="details-grid">
          <div class="detail-box">
            <h4>{{ info.question_count }}</h4>
            <span>Questions</span>
          </div>
          <div class="detail-box">
            <h4>{{ info.time_limit }}</h4>
            <span>Minutes</span>
          </div>
          <div class="detail-box">
            <h4>{{ info.best_score }} / {{ info.question_count }}</h4>
            <span>Your Best Score</span>
          </div>
        </div>

        <div class="rating-section">
          <h3>Rate this Quiz</h3>
          <div class="stars">
            <span v-for="n in 5" :key="n" @click="rate(n)" class="star" :class="{ filled: n <= currentRating }">&#9733;</span>
          </div>
          <p v-if="info.average_rating">Average Rating: {{ parseFloat(info.average_rating).toFixed(1) }} &#9733;</p>
          <p v-else>No ratings yet.</p>
        </div>

        <div class="start-button-container">
          <div v-if="info.status === 'Live'">
            <button @click="startQuiz" class="start-btn" :disabled="info.has_attempted">
              {{ info.has_attempted ? 'Already Attempted' : 'Start Quiz' }}
            </button>
            <p v-if="info.one_attempt_only" class="attempt-notice">This is a one-attempt only quiz.</p>
          </div>
          <div v-else class="status-box">
            <p v-if="info.status === 'Not yet started'">This quiz has not started yet. It will be available on {{ formatToIST(info.start_time_formatted) }} (IST).</p>
            <p v-if="info.status === 'Expired'">This quiz has expired.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatInTimeZone } from 'date-fns-tz';

export default {
  name: 'QuizInfoPage',
  data() {
    return {
      info: null,
      isLoading: true,
      currentRating: 0,
    };
  },
  methods: {
    formatToIST(dateString) {
        if (!dateString) return '';
        return formatInTimeZone(new Date(dateString + 'Z'), 'Asia/Kolkata', 'yyyy-MM-dd HH:mm');
    },
    async fetchInfo() {
      this.isLoading = true;
      const quizId = this.$route.params.quizId;
      try {
        const res = await fetch(`/api/user/quiz-info/${quizId}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!res.ok) throw new Error('Failed to fetch info');
        this.info = await res.json();
      } catch (error) {
        console.error(error);
        this.$router.push('/dashboard');
      } finally {
        this.isLoading = false;
      }
    },
    async rate(rating) {
        this.currentRating = rating;
        const quizId = this.$route.params.quizId;
        try {
            const res = await fetch(`/api/user/quiz/${quizId}/rate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ rating })
            });
            if (res.status === 409) {
                alert("You have already rated this quiz.");
                return;
            }
            const result = await res.json();
            this.info.average_rating = result.new_average_rating;
            alert('Thank you for your rating!');
        } catch (error) {
            console.error("Failed to submit rating:", error);
        }
    },
    startQuiz() {
      this.$router.push(`/quiz/attempt/${this.info.id}`);
    }
  },
  mounted() {
    this.fetchInfo();
  }
};
</script>

<style scoped>
@import '../assets/user_styles.css';

.status-box {
    background-color: rgba(0,0,0,0.2);
    color: #fca5a5;
    padding: 1rem;
    border-radius: 8px;
    font-weight: 500;
}
.rating-section {
  padding: 2rem 0;
  text-align: center;
  border-top: 1px solid #790bf7;
  margin-top: 2rem;
}
.stars {
  font-size: 2.5rem;
  color: #a78bfa;
  cursor: pointer;
}
.star.filled {
  color: #ffc107;
}
</style>