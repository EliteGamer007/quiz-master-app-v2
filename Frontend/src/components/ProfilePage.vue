<template>
  <div class="profile-page">
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
              <div class="stat-value">{{ averageScoreRatio }}</div>
              <div class="stat-label">Average Score Ratio</div>
            </div>
            <div>
              <div class="stat-value">{{ averagePercentage }}%</div>
              <div class="stat-label">Average Percentage</div>
            </div>
          </div>
        </div>

        <div class="progress-chart-container">
            <h2 class="section-title">Your Progress</h2>
            <canvas id="progressChart"></canvas>
        </div>

        <div class="history-section">
          <div class="history-header">
            <h2 class="section-title">Quiz History</h2>
            <button @click="startExport" :disabled="isExporting" class="export-btn">
              {{ isExporting ? 'Exporting...' : 'Export as CSV' }}
            </button>
          </div>
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
                  <router-link :to="`/quiz/info/${score.quiz_id}`">
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
import { Chart } from 'chart.js/auto';

export default {
  name: 'ProfilePage',
  data() {
    return {
      scores: [],
      progressData: { labels: [], data: [] },
      isLoading: true,
      isExporting: false,
      progressChart: null
    };
  },
  computed: {
    totalQuizzesTaken() {
      return this.scores.length;
    },
    averageScoreRatio() {
      if (this.scores.length === 0) return '0.00';
      const ratios = this.scores.map(s => s.max_score > 0 ? s.score / s.max_score : 0);
      const sumOfRatios = ratios.reduce((sum, r) => sum + r, 0);
      return (sumOfRatios / this.scores.length).toFixed(2);
    },
    averagePercentage() {
        return (this.averageScoreRatio * 100).toFixed(2);
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
            const [scoresRes, progressRes] = await Promise.all([
                this.apiCall('/api/user/scores'),
                this.apiCall('/api/user/progress')
            ]);
            this.scores = scoresRes;
            this.progressData = progressRes;
            this.renderChart();
        } catch (error) {
            console.error(error);
        } finally {
            this.isLoading = false;
        }
    },
    renderChart() {
        this.$nextTick(() => {
            const ctx = document.getElementById('progressChart');
            if (!ctx) return;
            if (this.progressChart) {
                this.progressChart.destroy();
            }
            this.progressChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.progressData.labels,
                    datasets: [{
                        label: 'Score (%)',
                        data: this.progressData.data,
                        borderColor: '#fff',
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        fill: true,
                        tension: 0.1
                    }]
                },
                options: {
                    scales: {
                        y: { min: 0, max: 100, ticks: { color: '#fff' } },
                        x: { ticks: { color: '#fff' } }
                    },
                    plugins: { legend: { labels: { color: '#fff' } } }
                }
            });
        });
    },
    async apiCall(endpoint) {
        const res = await fetch(endpoint, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!res.ok) throw new Error('API call failed');
        return res.json();
    },
    formatDate(dateString) {
      const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    async startExport() {
      this.isExporting = true;
      try {
        const res = await fetch('/api/user/export-scores', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        this.pollTaskStatus(data.task_id);
      } catch (error) {
        console.error('Failed to start export:', error);
        this.isExporting = false;
      }
    },
    pollTaskStatus(taskId) {
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/user/export-status/${taskId}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
          });
          const data = await res.json();
          if (data.task_status === 'SUCCESS') {
            clearInterval(interval);
            const filename = data.task_result.file_url.split('/').pop();
            this.downloadFile(filename);
          } else if (data.task_status === 'FAILURE') {
            clearInterval(interval);
            this.isExporting = false;
            alert('Export failed. Please try again.');
          }
        } catch (error) {
          clearInterval(interval);
          this.isExporting = false;
          console.error('Failed to poll task status:', error);
        }
      }, 3000);
    },
    async downloadFile(filename) {
        try {
            const res = await fetch(`/api/user/download-export/${filename}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            if (!res.ok) throw new Error('Download failed');
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'quiz_history.csv');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch(error) {
            console.error(error);
            alert('Could not download the file.');
        } finally {
            this.isExporting = false;
        }
    }
  },
  mounted() {
    this.fetchData();
  }
};
</script>

<style scoped>
@import '../assets/user_styles.css';
</style>