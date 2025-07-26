<template>
  <div class="main_content">
    <div class="container">
      <h1>Quiz Master</h1>
      <h2>Register</h2>
      <form @submit.prevent="register">
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

        <button type="submit" :disabled="!canSubmit">Register</button>
        <div class="link">
          <p>Already have an account? <a href="#" @click.prevent="$router.push('/')">Login</a></p>
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
      age: ''
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
    async register() {
      if (!this.canSubmit) {
        alert('Please complete all fields correctly before submitting.');
        return;
      }

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
          alert(result.message);
          this.$router.push('/');
        } else {
          alert(result.message || 'Registration failed');
        }
      } catch (err) {
        alert('An error occurred during registration.');
        console.error(err);
      }
    }
  }
};
</script>

<style scoped>
@import '../assets/login_styles.css';
</style>