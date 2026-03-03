<template>
  <div class="user-management admin-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        <router-link to="/admin/analytics" class="nav_link">Analytics</router-link>
        <router-link to="/admin/users" class="nav_link">Users</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper">
      <div class="header-controls">
        <h2>User Management</h2>
      </div>
      <div class="search-bar">
        <input type="text" v-model="searchQuery" @input="handleSearch" placeholder="Search by name or email...">
      </div>
      <div class="table-container">
        <table class="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Qualification</th>
              <th>Age</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in displayedUsers" :key="user.id">
              <td>{{ user.id }}</td>
              <td>{{ user.full_name }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.qualification }}</td>
              <td>{{ user.age }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'UserManagement',
  data() {
    return {
      users: [],
      searchQuery: '',
      searchResults: [],
    };
  },
  computed: {
      displayedUsers() {
          return this.searchQuery.trim() ? this.searchResults : this.users;
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
    async fetchUsers() {
      try {
        const response = await fetch('/api/admin/users', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!response.ok) throw new Error('Failed to fetch users');
        this.users = await response.json();
      } catch (error) {
        console.error(error);
      }
    },
    async handleSearch() {
        if (this.searchQuery.trim() === '') {
            this.searchResults = [];
            return;
        }
        try {
            const response = await fetch(`/api/admin/search/users?q=${this.searchQuery}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            this.searchResults = await response.json();
        } catch (error) {
            console.error(error);
        }
    }
  },
  mounted() {
    this.fetchUsers();
  }
};
</script>
<style scoped>
@import '../assets/website_styles.css';
</style>