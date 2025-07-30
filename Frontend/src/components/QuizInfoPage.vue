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

        <div class="start-button-container">
          <div v-if="info.status === 'Live'">
            <button @click="startQuiz" class="start-btn" :disabled="info.has_attempted">
              {{ info.has_attempted ? 'Already Attempted' : 'Start Quiz' }}
            </button>
            <p v-if="info.one_attempt_only" class="attempt-notice">This is a one-attempt only quiz.</p>
          </div>
          <div v-else class="status-box">
            <p v-if="info.status === 'Not yet started'">This quiz has not started yet. It will be available on {{ info.start_time_formatted }}.</p>
            <p v-if="info.status === 'Expired'">This quiz has expired.</p>
          </div>
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
</style>