<template>
  <div class="main_content">
    <div class="container">
      <h1>Quiz Master</h1>
      <h2>Reset Password</h2>
      
      <!-- Step 1: Enter Email -->
      <form v-if="step === 1" @submit.prevent="requestOtp">
        <div class="info-box">
          <p>🔑 Enter your registered email to receive a password reset OTP</p>
        </div>
        
        <label for="email">Email</label>
        <input v-model="email" type="email" id="email" class="form-input" placeholder="Enter your email" required />

        <button type="submit" :disabled="loading">{{ loading ? 'Sending OTP...' : 'Send OTP' }}</button>
        <div class="link">
          <p><a href="#" @click.prevent="$router.push('/login')">← Back to Login</a></p>
        </div>
      </form>

      <!-- Step 2: Enter OTP -->
      <form v-if="step === 2" @submit.prevent="verifyOtp">
        <div class="otp-info">
          <p>📧 We've sent a 6-digit OTP to <strong>{{ email }}</strong></p>
          <p class="otp-subtitle">Please enter it below to verify your identity</p>
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
          {{ loading ? 'Verifying...' : 'Verify OTP' }}
        </button>
        
        <div class="link">
          <p><a href="#" @click.prevent="resendOtp">Resend OTP</a></p>
          <p><a href="#" @click.prevent="goToStep(1)">← Change email</a></p>
        </div>
      </form>

      <!-- Step 3: Enter New Password -->
      <form v-if="step === 3" @submit.prevent="resetPassword">
        <div class="success-info">
          <p>✅ OTP verified! Now set your new password</p>
        </div>
        
        <label for="newPassword">New Password</label>
        <input 
          v-model="newPassword" 
          type="password" 
          id="newPassword" 
          class="form-input" 
          placeholder="Enter new password (min 6 characters)"
          minlength="6"
          required 
        />

        <label for="confirmPassword">Confirm Password</label>
        <input 
          v-model="confirmPassword" 
          type="password" 
          id="confirmPassword" 
          class="form-input" 
          placeholder="Confirm new password"
          minlength="6"
          required 
        />
        
        <div v-if="passwordError" class="error-text">{{ passwordError }}</div>

        <button type="submit" :disabled="loading || !isPasswordValid">
          {{ loading ? 'Resetting...' : 'Reset Password' }}
        </button>
        
        <div class="link">
          <p><a href="#" @click.prevent="goToStep(1)">← Start over</a></p>
        </div>
      </form>

      <!-- Step 4: Success -->
      <div v-if="step === 4" class="success-container">
        <div class="success-icon">🎉</div>
        <h3>Password Reset Successful!</h3>
        <p>Your password has been updated successfully.</p>
        <button @click="$router.push('/login')">Go to Login</button>
      </div>
    </div>

    <div class="image_box">
      <img src="/quiz.jpg" alt="Quiz Illustration" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'ForgotPassword',
  data() {
    return {
      step: 1,
      email: '',
      otp: '',
      newPassword: '',
      confirmPassword: '',
      loading: false
    };
  },
  computed: {
    passwordError() {
      if (this.newPassword && this.newPassword.length < 6) {
        return 'Password must be at least 6 characters';
      }
      if (this.confirmPassword && this.newPassword !== this.confirmPassword) {
        return 'Passwords do not match';
      }
      return '';
    },
    isPasswordValid() {
      return this.newPassword.length >= 6 && 
             this.newPassword === this.confirmPassword;
    }
  },
  methods: {
    validateOtpInput() {
      // Only allow digits
      this.otp = this.otp.replace(/\D/g, '');
    },
    
    goToStep(stepNum) {
      this.step = stepNum;
      if (stepNum === 1) {
        this.otp = '';
        this.newPassword = '';
        this.confirmPassword = '';
      }
    },
    
    async requestOtp() {
      this.loading = true;
      try {
        const res = await fetch('/api/auth/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email })
        });

        const result = await res.json();

        if (!res.ok) {
          alert(result.error || 'Failed to send OTP');
          this.loading = false;
          return;
        }

        alert(result.message || 'OTP sent to your email');
        this.step = 2;
        this.loading = false;
      } catch (err) {
        alert('An error occurred. Please try again.');
        console.error(err);
        this.loading = false;
      }
    },

    async resendOtp() {
      await this.requestOtp();
    },

    async verifyOtp() {
      this.loading = true;
      try {
        const res = await fetch('/api/auth/verify-reset-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, otp: this.otp })
        });

        const result = await res.json();

        if (!res.ok) {
          alert(result.error || 'OTP verification failed');
          this.loading = false;
          return;
        }

        this.step = 3;
        this.loading = false;
      } catch (err) {
        alert('An error occurred during OTP verification.');
        console.error(err);
        this.loading = false;
      }
    },

    async resetPassword() {
      if (!this.isPasswordValid) {
        alert('Please fix the password errors');
        return;
      }

      this.loading = true;
      try {
        const res = await fetch('/api/auth/reset-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            email: this.email, 
            otp: this.otp,
            new_password: this.newPassword,
            confirm_password: this.confirmPassword
          })
        });

        const result = await res.json();

        if (!res.ok) {
          alert(result.error || 'Password reset failed');
          this.loading = false;
          return;
        }

        this.step = 4;
        this.loading = false;
      } catch (err) {
        alert('An error occurred during password reset.');
        console.error(err);
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
@import '../assets/login_styles.css';

.info-box {
  background: #fff3e0;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #ff9800;
}

.info-box p {
  margin: 0;
  color: #e65100;
}

.success-info {
  background: #e8f5e9;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #4caf50;
}

.success-info p {
  margin: 0;
  color: #2e7d32;
}

.success-container {
  text-align: center;
  padding: 20px;
}

.success-icon {
  font-size: 4em;
  margin-bottom: 20px;
}

.success-container h3 {
  color: #4caf50;
  margin-bottom: 10px;
}

.success-container p {
  color: #666;
  margin-bottom: 25px;
}

.error-text {
  color: #d32f2f;
  font-size: 0.85em;
  margin-top: 5px;
  text-align: left;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
