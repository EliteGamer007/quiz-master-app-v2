<template>
  <div class="analytics-dashboard admin-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        <router-link to="/admin/analytics" class="nav_link">Analytics</router-link>
        <router-link to="/admin/users" class="nav_link" v-if="isAdmin">Users</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper">
      <div v-if="isLoading">Loading analytics...</div>
      <div v-else>
        <div class="summary-grid">
          <div class="summary-card" v-if="isAdmin">
            <h3>{{ analytics.total_users }}</h3>
            <p>Total Users</p>
          </div>
          <div class="summary-card">
            <h3>{{ analytics.total_quizzes }}</h3>
            <p>Total Quizzes</p>
          </div>
          <div class="summary-card">
            <h3>{{ analytics.total_attempts }}</h3>
            <p>Total Attempts</p>
          </div>
        </div>

        <div class="leaderboard-container">
          <h2>Leaderboard</h2>
          <div class="table-container">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>User</th>
                  <th>Quizzes Taken</th>
                  <th>Average Score Ratio</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(user, index) in leaderboard" :key="index">
                  <td>{{ index + 1 }}</td>
                  <td>{{ user.name }}</td>
                  <td>{{ user.quizzes_taken }}</td>
                  <td>{{ user.average_score_ratio }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalyticsDashboard',
  data() {
    return {
      analytics: {},
      leaderboard: [],
      isLoading: true
    };
  },
  computed: {
    isAdmin() {
      return localStorage.getItem('role') === 'admin';
    },
    isQuizMaster() {
      return localStorage.getItem('role') === 'quiz_master';
    }
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
    async fetchData() {
      this.isLoading = true;
      try {
        const baseUrl = this.isQuizMaster ? '/api/quiz-master' : '/api/admin';
        const [analyticsRes, leaderboardRes] = await Promise.all([
          this.apiCall(`${baseUrl}/analytics`),
          this.apiCall(`${baseUrl}/leaderboard`)
        ]);
        this.analytics = analyticsRes;
        this.leaderboard = leaderboardRes;
      } catch (error) {
        console.error(error);
      } finally {
        this.isLoading = false;
      }
    },
    async apiCall(endpoint) {
      const res = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!res.ok) throw new Error('API call failed');
      return res.json();
    }
  },
  mounted() {
    this.fetchData();
  }
};
</script>

<style scoped>
@import '../assets/website_styles.css';

.summary-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-bottom: 2rem;
}
.summary-card {
    background-color: #5e10f0;
    color: #fff;
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
}
.summary-card h3 {
    font-size: 2.5rem;
    margin: 0;
}
.leaderboard-container {
    background-color: #6d28d9;
    padding: 1.5rem;
    border-radius: 8px;
}
.leaderboard-container h2 {
    color: #fff;
    margin-bottom: 1rem;
}
</style>