<template>
  <div class="main_content">
    <div class="container">
      <h1>Quiz Master</h1>
      <h2>Register</h2>
      
      <!-- Step 1: Registration Form -->
      <form v-if="!showOtpInput" @submit.prevent="register">
        <label for="full_name">Full Name</label>
        <input v-model="full_name" type="text" id="full_name" class="form-input" required />

        <label for="email">Email</label>
        <input v-model="email" type="email" id="email" class="form-input" required />

        <label for="password">Password</label>
        <input v-model="password" type="password" id="password" class="form-input" required />
        <small v-if="password && !isValidPassword" style="color: red; margin-top: -0.5rem; margin-bottom: 0.5rem; display: block;">
          Password must contain at least one uppercase letter and one number.
        </small>

        <label for="qualification">Qualification</label>
        <select v-model="qualification" id="qualification" class="form-input" required>
          <option disabled value="">Please select</option>
          <option>School</option>
          <option>University</option>
          <option>General</option>
          <option>Prefer not to say</option>
        </select>

        <label for="age">Age</label>
        <input v-model.number="age" type="number" id="age" class="form-input" required />
        <small v-if="age && age <= 12" style="color: orange; margin-top: -0.5rem; margin-bottom: 0.5rem; display: block;">
          Please ask your parent or guardian to register for you.
        </small>

        <button type="submit" :disabled="!canSubmit || loading">{{ loading ? 'Please wait...' : 'Register' }}</button>
        <div class="link">
          <p>Already have an account? <a href="#" @click.prevent="$router.push('/')">Login</a></p>
        </div>
      </form>

      <!-- Step 2: OTP Verification -->
      <form v-if="showOtpInput" @submit.prevent="verifyOtp">
        <div class="otp-info">
          <p>📧 We've sent a verification code to <strong>{{ email }}</strong></p>
          <p class="otp-subtitle">Please enter the 6-digit code to complete registration</p>
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
          {{ loading ? 'Verifying...' : 'Verify & Complete' }}
        </button>
        
        <div class="link">
          <p><a href="#" @click.prevent="resetForm">← Back to registration</a></p>
        </div>
      </form>
    </div>

    <div class="image_box">
      <img src="/quiz.jpg" alt="Quiz Registration Illustration" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'RegisterForm',
  data() {
    return {
      full_name: '',
      email: '',
      password: '',
      qualification: '',
      age: '',
      otp: '',
      showOtpInput: false,
      loading: false
    };
  },
  computed: {
    isValidPassword() {
      return /[A-Z]/.test(this.password) && /\d/.test(this.password);
    },
    canSubmit() {
      return (
        this.full_name &&
        this.email &&
        this.password &&
        this.qualification &&
        this.age > 0 &&
        this.isValidPassword
      );
    }
  },
  methods: {
    validateOtpInput() {
      // Only allow digits
      this.otp = this.otp.replace(/\D/g, '');
    },
    
    async register() {
      if (!this.canSubmit) {
        alert('Please complete all fields correctly before submitting.');
        return;
      }

      this.loading = true;
      try {
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: this.full_name,
            email: this.email,
            password: this.password,
            qualification: this.qualification,
            age: this.age
          })
        });

        const result = await res.json();
        
        if (res.ok) {
          alert(result.message || 'Verification code sent to your email');
          this.showOtpInput = true;
        } else {
          alert(result.message || result.error || 'Registration failed');
        }
      } catch (err) {
        alert('An error occurred during registration.');
        console.error(err);
      } finally {
        this.loading = false;
      }
    },

    async verifyOtp() {
      this.loading = true;
      try {
        const res = await fetch('/api/auth/verify-registration-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: this.email,
            otp: this.otp
          })
        });

        const result = await res.json();
        
        if (res.ok) {
          alert(result.message || 'Registration successful! You can now login.');
          this.$router.push('/');
        } else {
          alert(result.error || result.message || 'OTP verification failed');
        }
      } catch (err) {
        alert('An error occurred during verification.');
        console.error(err);
      } finally {
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