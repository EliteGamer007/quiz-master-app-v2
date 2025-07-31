<template>
  <div class="subject-detail-page admin-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        <router-link to="/admin/analytics" class="nav_link">Analytics</router-link>
        <router-link to="/admin/users" class="nav_link">Users</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper" v-if="subject">
      <div class="header-controls">
        <h2>{{ subject.title }}</h2>
        <router-link to="/admin_dashboard" class="back-link">&larr; Back to Subjects</router-link>
      </div>
      <p>{{ subject.description }}</p>

      <div class="chapter-levels-container">
        <div v-for="level in chapterLevels" :key="level" class="chapter-level-section">
          <div class="level-header">
            <h3>{{ level }} Chapters</h3>
            <button class="primary-btn" @click="openChapterModal(level)">+ Add Chapter</button>
          </div>
          <hr class="divider">
          <div class="admin-grid">
            <div v-for="chapter in subject.chapters[level]" :key="chapter.id" class="admin-card">
              <router-link :to="{ name: 'ChapterDetail', params: { chapterId: chapter.id } }" class="admin-card-link">
                  <h4>{{ chapter.heading }}</h4>
                  <p>{{ chapter.description }}</p>
              </router-link>
              <div class="card-actions">
                  <button class="edit-btn" @click="openChapterModal(level, chapter)">Edit</button>
                  <button class="delete-btn" @click="confirmDeleteChapter(chapter)">Delete</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showChapterModal" class="modal-overlay">
      <div class="modal-content">
        <h4>{{ modal.isEdit ? 'Edit' : 'Add New' }} {{ modal.data.level }} Chapter</h4>
        <input v-model="modal.data.heading" type="text" placeholder="Chapter Heading" />
        <textarea v-model="modal.data.description" placeholder="Description"></textarea>
        <div class="modal-actions">
          <button @click="handleChapterSubmit">{{ modal.isEdit ? 'Save Changes' : 'Add Chapter' }}</button>
          <button @click="closeChapterModal">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'SubjectDetail',
  data() {
    return {
      subject: null,
      showChapterModal: false,
      chapterLevels: ['Beginner', 'Intermediate', 'Advanced'],
      modal: {
        isEdit: false,
        data: { id: null, heading: '', description: '', level: '' }
      }
    };
  },
  methods: {
    logout() {
      localStorage.removeItem('token');
      this.$router.push('/');
    },
    async apiCall(endpoint, method = 'GET', body = null) {
      const headers = { 'Authorization': `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' };
      const config = { method, headers, body: body ? JSON.stringify(body) : null };
      const response = await fetch(endpoint, config);
      if (!response.ok) throw new Error(`API call failed`);
      if (response.status === 204) return;
      return response.json();
    },
    async fetchSubjectDetails() {
      const subjectId = this.$route.params.subjectId;
      try {
        this.subject = await this.apiCall(`/api/admin/subjects/${subjectId}`);
      } catch (err) {
        console.error(err);
      }
    },
    openChapterModal(level, chapter = null) {
      this.modal.isEdit = !!chapter;
      this.modal.data = chapter ? { ...chapter } : { id: null, heading: '', description: '', level: level };
      this.showChapterModal = true;
    },
    closeChapterModal() {
      this.showChapterModal = false;
    },
    async handleChapterSubmit() {
      const { isEdit, data } = this.modal;
      const endpoint = isEdit ? `/api/admin/chapters/${data.id}` : `/api/admin/subjects/${this.subject.id}/chapters`;
      const method = isEdit ? 'PUT' : 'POST';
      try {
        await this.apiCall(endpoint, method, data);
        await this.fetchSubjectDetails();
        this.closeChapterModal();
      } catch (error) {
        console.error(error);
      }
    },
    confirmDeleteChapter(chapter) {
      if (confirm(`Are you sure you want to delete "${chapter.heading}"?`)) {
        this.deleteChapter(chapter);
      }
    },
    async deleteChapter(chapter) {
      try {
        await this.apiCall(`/api/admin/chapters/${chapter.id}`, 'DELETE');
        await this.fetchSubjectDetails();
      } catch (error) {
        console.error(error);
      }
    }
  },
  mounted() {
    this.fetchSubjectDetails();
  }
};
</script>
<style scoped>
@import '../assets/website_styles.css';
</style>