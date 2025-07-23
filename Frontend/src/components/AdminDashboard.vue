<template>
  <div class="admin-dashboard">
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
        <h2>Subjects</h2>
        <button class="primary-btn" @click="openModal()">Add Subject</button>
      </div>

      <div class="subjects-grid">
        <div v-for="subject in subjects" :key="subject.id" class="subject-card">
          <router-link :to="{ name: 'SubjectDetail', params: { subjectId: subject.id } }" class="subject-card-link">
            <h3>{{ subject.title }}</h3>
            <p>{{ subject.description }}</p>
          </router-link>
          <div class="card-actions">
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
      showSubjectModal: false,
      modal: {
        isEdit: false,
        data: { id: null, title: '', description: '' }
      }
    };
  },
  methods: {
    logout() {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      this.$router.push('/');
    },
    async apiCall(endpoint, method = 'GET', body = null) {
      const headers = {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      };
      const config = { method, headers };
      if (body) {
        config.body = JSON.stringify(body);
      }
      const response = await fetch(endpoint, config);
      if (!response.ok) {
        throw new Error('API call failed');
      }
      return response.json();
    },
    async fetchSubjects() {
      try {
        this.subjects = await this.apiCall('/api/admin/subjects');
      } catch (error) {
        console.error(error);
      }
    },
    openModal(subject = null) {
      if (subject) {
        this.modal.isEdit = true;
        this.modal.data = { ...subject };
      } else {
        this.modal.isEdit = false;
        this.modal.data = { id: null, title: '', description: '' };
      }
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
        const result = await this.apiCall(endpoint, method, data);
        if (isEdit) {
          const index = this.subjects.findIndex(s => s.id === data.id);
          this.subjects[index] = data;
        } else {
          this.subjects.push(result);
        }
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

<style>
@import '../assets/website_styles.css';
</style>
