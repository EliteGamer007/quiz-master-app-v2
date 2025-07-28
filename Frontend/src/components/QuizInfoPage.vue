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
          <button @click="startQuiz" class="start-btn" :disabled="info.has_attempted">
            {{ info.has_attempted ? 'Already Attempted' : 'Start Quiz' }}
          </button>
          <p v-if="info.one_attempt_only" class="attempt-notice">This is a one-attempt only quiz.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
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
.info-container {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  color: #343a40;
}
.breadcrumb {
  font-size: 0.9rem;
  color: #6c757d;
  font-weight: 500;
}
.info-header h1 {
  margin: 0.5rem 0;
}
.description {
  font-size: 1.1rem;
  color: #495057;
  margin-bottom: 2rem;
}
.details-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  text-align: center;
  padding: 2rem 0;
  border-top: 1px solid #e9ecef;
  border-bottom: 1px solid #e9ecef;
}
.detail-box h4 {
  font-size: 2rem;
  font-weight: 700;
  color: #4f46e5;
  margin: 0;
}
.detail-box span {
  font-size: 0.9rem;
  color: #6c757d;
}
.rating-section {
  padding: 2rem 0;
  text-align: center;
}
.stars {
  font-size: 2.5rem;
  color: #ced4da;
  cursor: pointer;
}
.star.filled {
  color: #ffc107;
}
.start-button-container {
  text-align: center;
  margin-top: 1rem;
}
.start-btn {
  background-color: #4f46e5;
  color: white;
  border: none;
  padding: 1rem 3rem;
  border-radius: 50px;
  font-size: 1.2rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}
.start-btn:hover {
  background-color: #4338ca;
}
.start-btn:disabled {
    background-color: #a5b4fc;
    cursor: not-allowed;
}
.attempt-notice {
    font-size: 0.9rem;
    color: #6c757d;
    margin-top: 0.5rem;
}
</style>