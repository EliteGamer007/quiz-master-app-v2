<template>
  <div class="search-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/dashboard">Home</router-link>
        <router-link to="/search">Search</router-link>
        <router-link to="/profile">Profile</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper">
      <div class="search-container">
        <input 
          type="text" 
          v-model="query" 
          @input="performSearch" 
          placeholder="Search for subjects or quizzes..."
          class="search-input"
        >
      </div>

      <div v-if="isLoading" class="loading">Searching...</div>

      <div v-if="!isLoading && query" class="results-container">
        <div v-if="subjects.length">
          <h3>Subjects</h3>
          <div class="result-list">
            <div v-for="subject in subjects" :key="subject.id" class="result-item">
               {{ subject.title }}
            </div>
          </div>
        </div>

        <div v-if="quizzes.length">
          <h3>Quizzes</h3>
          <div class="result-list">
            <div v-for="quiz in quizzes" :key="quiz.id" class="result-item">
              <router-link :to="`/quiz/info/${quiz.id}`">{{ quiz.title }}</router-link>
            </div>
          </div>
        </div>

        <div v-if="!subjects.length && !quizzes.length" class="no-results">
          No results found for "{{ query }}".
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SearchPage',
  data() {
    return {
      query: '',
      subjects: [],
      quizzes: [],
      isLoading: false,
      searchTimeout: null
    };
  },
  methods: {
    async logout() {
      const accessToken = localStorage.getItem('token');
      const refreshToken = sessionStorage.getItem('refresh_token');
      const logoutToken = refreshToken || accessToken;
      try {
        if (logoutToken) {
          await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${logoutToken}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
          });
        }
      } catch (error) {
        console.error('Logout request failed:', error);
      }
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      localStorage.removeItem('user_name');
      sessionStorage.removeItem('refresh_token');
      this.$router.push('/');
    },
    performSearch() {
      this.isLoading = true;
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(async () => {
        if (this.query.trim() === '') {
          this.subjects = [];
          this.quizzes = [];
          this.isLoading = false;
          return;
        }
        try {
          const [subjectsRes, quizzesRes] = await Promise.all([
            this.apiCall(`/api/user/search/subjects?q=${this.query}`),
            this.apiCall(`/api/user/search/quizzes?q=${this.query}`)
          ]);
          this.subjects = subjectsRes;
          this.quizzes = quizzesRes;
        } catch (error) {
          console.error("Search failed:", error);
        } finally {
          this.isLoading = false;
        }
      }, 500);
    },
    async apiCall(endpoint) {
      const res = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!res.ok) throw new Error('API call failed');
      return res.json();
    }
  }
};
</script>

<style scoped>
@import '../assets/user_styles.css';
</style>