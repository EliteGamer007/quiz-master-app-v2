<template>
  <div class="main_content">
    <div class="container">
      <h1>Quiz Master</h1>
      <h2>Login</h2>
      <form @submit.prevent="login">
        <label for="email">Email</label>
        <input v-model="email" type="email" id="email" class="form-input" required />

        <label for="password">Password</label>
        <input v-model="password" type="password" id="password" class="form-input" required />

        <button type="submit">Login</button>
        <div class="link">
          <p>New user? <a href="#" @click.prevent="$router.push('/register')">Register Here</a></p>
        </div>
      </form>
    </div>

    <div class="image_box">
      <img src="/quiz.jpg" alt="Quiz Illustration" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginForm',
  data() {
    return {
      email: '',
      password: ''
    };
  },
  methods: {
    async login() {
      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, password: this.password })
        });

        const result = await res.json();

        if (!res.ok) {
          alert(result.error || result.message || 'Login failed');
          return;
        }

        const { token, role, message } = result;

        if (!token || !token.startsWith('ey')) {
          alert('Received invalid token.');
          return;
        }

        localStorage.setItem('token', token);
        localStorage.setItem('role', role);

        alert(message);

        if (role === 'admin') {
          this.$router.push('/admin_dashboard');
        } else if (role === 'user') {
          this.$router.push('/user_dashboard');
        } else {
          alert('Unknown role. Access denied.');
        }
      } catch (err) {
        alert('An error occurred during login.');
        console.error(err);
      }
    }
  }
};
</script>

<style scoped>
@import '../assets/login_styles.css';
</style>
