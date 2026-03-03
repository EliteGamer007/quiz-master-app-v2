<template>
  <div class="main_content">
    <div class="container">
      <h1>Quiz Master</h1>
      <h2>Login</h2>
      
      <!-- Step 1: Email & Password -->
      <form v-if="!showOtpInput" @submit.prevent="requestOtp">
        <label for="email">Email</label>
        <input v-model="email" type="email" id="email" class="form-input" required />

        <label for="password">Password</label>
        <input v-model="password" type="password" id="password" class="form-input" required />

        <button type="submit" :disabled="loading">{{ loading ? 'Please wait...' : 'Login' }}</button>
        <div class="link">
          <p>New user? <a href="#" @click.prevent="$router.push('/register')">Register Here</a></p>
          <p><a href="#" @click.prevent="$router.push('/forgot-password')">Forgot Password?</a></p>
        </div>
      </form>

      <!-- Step 2: OTP Verification -->
      <form v-if="showOtpInput" @submit.prevent="verifyOtp">
        <div class="otp-info">
          <p>📧 We've sent a 6-digit OTP to <strong>{{ email }}</strong></p>
          <p class="otp-subtitle">Please enter it below to complete login</p>
        </div>
        
        <label for="otp">Enter OTP</label>
        <input 
          v-model="otp" 
          type="text" 
          id="otp" 
          class="form-input otp-input" 
          maxlength="6"
          placeholder="000000"
          required 
          @input="validateOtpInput"
        />

        <button type="submit" :disabled="loading || otp.length !== 6">
          {{ loading ? 'Verifying...' : 'Verify & Login' }}
        </button>
        
        <div class="link">
          <p><a href="#" @click.prevent="resetForm">← Back to login</a></p>
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
      password: '',
      otp: '',
      showOtpInput: false,
      loading: false
    };
  },
  methods: {
    validateOtpInput() {
      // Only allow digits
      this.otp = this.otp.replace(/\D/g, '');
    },
    
    async requestOtp() {
      this.loading = true;
      try {
        const res = await fetch('/api/auth/request-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, password: this.password })
        });

        const result = await res.json();

        if (!res.ok) {
          alert(result.error || result.message || 'Login failed');
          this.loading = false;
          return;
        }

        // Check if admin or quiz_master (no OTP required)
        if (result.requires_otp === false) {
          const { token, role, full_name } = result;
          localStorage.setItem('token', token);
          localStorage.setItem('role', role);
          if (full_name) {
            localStorage.setItem('user_name', full_name);
          }
          this.loading = false;
          
          // Redirect based on role
          if (role === 'admin') {
            this.$router.push('/admin_dashboard');
          } else if (role === 'quiz_master') {
            this.$router.push('/admin_dashboard'); // Quiz masters use admin dashboard with restricted access
          }
          return;
        }

        // User login - show OTP input
        alert(result.message || 'OTP sent to your email');
        this.showOtpInput = true;
        this.loading = false;
      } catch (err) {
        alert('An error occurred during login.');
        console.error(err);
        this.loading = false;
      }
    },

    async verifyOtp() {
      this.loading = true;
      try {
        const res = await fetch('/api/auth/verify-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, otp: this.otp })
        });

        const result = await res.json();

        if (!res.ok) {
          alert(result.error || result.message || 'OTP verification failed');
          this.loading = false;
          return;
        }

        const { token, role, full_name } = result;

        if (!token) {
          alert('Received invalid token.');
          this.loading = false;
          return;
        }

        localStorage.setItem('token', token);
        localStorage.setItem('role', role);
        if (full_name) {
          localStorage.setItem('user_name', full_name);
        }

        if (role === 'admin') {
          this.$router.push('/admin_dashboard');
        } else if (role === 'user') {
          this.$router.push('/dashboard');
        }
      } catch (err) {
        alert('An error occurred during OTP verification.');
        console.error(err);
        this.loading = false;
      }
    },

    resetForm() {
      this.otp = '';
      this.showOtpInput = false;
    }
  }
};
</script>

<style scoped>
@import '../assets/login_styles.css';
</style>