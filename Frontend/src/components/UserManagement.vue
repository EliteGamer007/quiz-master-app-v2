<template>
  <div class="user-management">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        <router-link to="/admin/users" class="nav_link">Users</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper">
      <div class="header-controls">
        <h2>User Management</h2>
      </div>
      <div class="table-container">
        <table>
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
            <tr v-for="user in users" :key="user.id">
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
      users: []
    };
  },
  methods: {
    logout() {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
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
    }
  },
  mounted() {
    this.fetchUsers();
  }
};
</script>

<style>
@import '../assets/website_styles.css';
</style>
