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
    logout() {
      localStorage.removeItem('token');
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

.search-input {
  width: 100%;
  padding: 1rem;
  font-size: 1.5rem;
  border-radius: 8px;
  border: 2px solid #5e10f0;
  margin-bottom: 2rem;
}

.results-container h3 {
  color: #fff;
  border-bottom: 1px solid #790bf7;
  padding-bottom: 0.5rem;
  margin-top: 2rem;
}
.result-list {
  background-color: #5e10f0;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}
.result-item {
  color: #fff;
  padding: 0.75rem;
  border-bottom: 1px solid #790bf7;
}
.result-item:last-child {
  border-bottom: none;
}
.result-item a {
  color: #a78bfa;
  text-decoration: none;
}
.no-results {
    color: #fff;
    text-align: center;
    padding: 2rem;
    font-style: italic;
}
</style>