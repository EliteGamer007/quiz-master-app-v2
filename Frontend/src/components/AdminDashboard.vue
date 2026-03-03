<template>
  <div class="admin-dashboard">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        <router-link to="/admin/analytics" class="nav_link">Analytics</router-link>
        <router-link v-if="isAdmin" to="/admin/users" class="nav_link">Users</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper">
      <div class="header-controls">
        <h2>{{ searchResults.length ? 'Search Results' : 'Subjects' }}</h2>
        <button v-if="isAdmin" class="primary-btn" @click="openModal()">Add Subject</button>
      </div>

      <div class="search-bar">
        <input type="text" v-model="searchQuery" @input="handleSearch" placeholder="Search for quizzes...">
      </div>

      <div v-if="searchResults.length" class="admin-grid">
        <div v-for="quiz in searchResults" :key="quiz.id" class="admin-card">
          <router-link :to="`/quizzes/${quiz.id}`" class="admin-card-link">
            <h3>{{ quiz.title }}</h3>
            <p>{{ quiz.description }}</p>
          </router-link>
        </div>
      </div>
      
      <div v-else class="admin-grid">
        <div v-for="subject in subjects" :key="subject.id" class="admin-card">
          <router-link :to="{ name: 'SubjectDetail', params: { subjectId: subject.id } }" class="admin-card-link">
            <h3>{{ subject.title }}</h3>
            <p>{{ subject.description }}</p>
          </router-link>
          <div v-if="isAdmin" class="card-actions">
            <button class="edit-btn" @click="openModal(subject)">Edit</button>
            <button class="delete-btn" @click="confirmDelete(subject)">Delete</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showSubjectModal" class="modal-overlay">
      <div class="modal-content">
        <h4>{{ modal.isEdit ? 'Edit Subject' : 'Add New Subject' }}</h4>
        <input v-model="modal.data.title" type="text" placeholder="Subject Name" />
        <textarea v-model="modal.data.description" placeholder="Description"></textarea>
        <div class="modal-actions">
          <button @click="handleSubjectSubmit">{{ modal.isEdit ? 'Save Changes' : 'Add Subject' }}</button>
          <button @click="closeModal">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdminDashboard',
  data() {
    return {
      subjects: [],
      searchQuery: '',
      searchResults: [],
      showSubjectModal: false,
      modal: {
        isEdit: false,
        data: { id: null, title: '', description: '' }
      }
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
    async apiCall(endpoint, method = 'GET', body = null) {
      const headers = {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      };
      const config = { method, headers, body: body ? JSON.stringify(body) : null };
      const response = await fetch(endpoint, config);
      if (!response.ok) throw new Error('API call failed');
      if (response.status === 204 || response.headers.get('Content-Length') === '0') return null;
      return response.json();
    },
    async fetchSubjects() {
      try {
        // Both admin and quiz master can view subjects
        const endpoint = this.isQuizMaster ? '/api/quiz-master/subjects' : '/api/admin/subjects';
        this.subjects = await this.apiCall(endpoint);
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
        // Only admin has search endpoint, quiz masters see their own quizzes
        if (this.isAdmin) {
          this.searchResults = await this.apiCall(`/api/admin/search/quizzes?q=${this.searchQuery}`);
        } else {
          // For quiz master, filter their own quizzes
          const quizzes = await this.apiCall('/api/quiz-master/quizzes');
          this.searchResults = quizzes.filter(q => 
            q.title.toLowerCase().includes(this.searchQuery.toLowerCase())
          );
        }
      } catch (error) {
        console.error(error);
      }
    },
    openModal(subject = null) {
      // Quiz masters cannot create/edit subjects
      if (this.isQuizMaster) {
        alert('Quiz Masters can create quizzes but cannot modify subjects.');
        return;
      }
      this.modal.isEdit = !!subject;
      this.modal.data = subject ? { ...subject } : { id: null, title: '', description: '' };
      this.showSubjectModal = true;
    },
    closeModal() {
      this.showSubjectModal = false;
    },
    async handleSubjectSubmit() {
      const { isEdit, data } = this.modal;
      const endpoint = isEdit ? `/api/admin/subjects/${data.id}` : '/api/admin/subjects';
      const method = isEdit ? 'PUT' : 'POST';
      try {
        await this.apiCall(endpoint, method, data);
        await this.fetchSubjects();
        this.closeModal();
      } catch (error) {
        console.error(error);
      }
    },
    confirmDelete(subject) {
      if (confirm(`Are you sure you want to delete "${subject.title}"?`)) {
        this.deleteSubject(subject.id);
      }
    },
    async deleteSubject(id) {
      try {
        await this.apiCall(`/api/admin/subjects/${id}`, 'DELETE');
        this.subjects = this.subjects.filter(s => s.id !== id);
      } catch (error) {
        console.error(error);
      }
    }
  },
  mounted() {
    this.fetchSubjects();
  }
};
</script>

<style scoped>
@import '../assets/website_styles.css';
</style>