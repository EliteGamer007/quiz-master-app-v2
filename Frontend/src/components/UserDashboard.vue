<template>
  <div class="container mt-5">
    <h2>User Dashboard</h2>
    <div v-if="user">
      <p><strong>Email:</strong> {{ user.email }}</p>
      <p><strong>Qualification:</strong> {{ user.qualification }}</p>
    </div>

    <h4 class="mt-4">Available Subjects</h4>
    <div v-if="subjects.length" class="row">
      <div class="col-md-6 mb-3" v-for="subject in subjects" :key="subject.id">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">{{ subject.title }}</h5>
            <p class="card-text">{{ subject.description }}</p>
          </div>
        </div>
      </div>
    </div>
    <p v-else>No subjects available.</p>

    <h4 class="mt-5">My Quiz Scores</h4>
    <table class="table table-bordered mt-2" v-if="scores.length">
      <thead>
        <tr>
          <th>Quiz Title</th>
          <th>Total Score</th>
          <th>Time Taken</th>
          <th>Rank</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(score, index) in scores" :key="index">
          <td>{{ score.quiz_title }}</td>
          <td>{{ score.total_score }}</td>
          <td>{{ score.attempt_time }} mins</td>
          <td>{{ score.user_rank }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>No quiz attempts yet.</p>
  </div>
</template>

<script>
export default {
  name: "UserDashboard",
  data() {
    return {
      user: null,
      scores: [],
      subjects: []
    };
  },
  mounted() {
    this.fetchUserData();
    this.fetchSubjects();
  },
  methods: {
    async fetchUserData() {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/user/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        this.user = {
          email: data.message.split(" ")[1],
          qualification: data.qualification
        };
        this.scores = data.scores;
      } else {
        console.error("Failed to load user dashboard");
      }
    },
    async fetchSubjects() {
  const token = localStorage.getItem('token');
  try {
    const response = await fetch('/api/user/subjects', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const contentType = response.headers.get("Content-Type");
    if (!response.ok) {
      const error = await response.json();
      console.error("Backend error:", error);
      return;
    }

    if (contentType && contentType.includes("application/json")) {
      this.subjects = await response.json();
    } else {
      console.error("Unexpected response type:", contentType);
    }

  } catch (err) {
    console.error("Failed to fetch subjects:", err);
  }
}

  }
};
</script>

<style scoped>
.container {
  max-width: 900px;
}
.card {
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}
</style>
