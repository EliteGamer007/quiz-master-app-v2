<template>
  <div class="subject-detail-page">
    <div class="navbar">
      <div class="logo_box">QuizMaster</div>
      <div class="navbar-center">
        <router-link to="/admin_dashboard" class="nav_link">Dashboard</router-link>
        <router-link to="/admin/users" class="nav_link">Users</router-link>
      </div>
      <a href="#" class="logout_link" @click.prevent="logout">Logout</a>
    </div>

    <div class="page_wrapper" v-if="subject">
      <div class="header-controls">
        <h2>{{ subject.title }}</h2>
        <router-link to="/admin_dashboard" class="back-link">&larr; Back to Subjects</router-link>
      </div>
      <p class="subject-description">{{ subject.description }}</p>

      <div class="chapter-levels-container">
        <div v-for="level in chapterLevels" :key="level" class="chapter-level-section">
          <div class="level-header">
            <h3>{{ level }} Chapters</h3>
            <button class="primary-btn" @click="openChapterModal(level)">+ Add Chapter</button>
          </div>
          <hr class="divider">
          <div class="chapters-grid">
            <template v-if="subject.chapters[level] && subject.chapters[level].length > 0">
              <div v-for="chapter in subject.chapters[level]" :key="chapter.id" class="chapter-card">
                <router-link :to="{ name: 'ChapterDetail', params: { chapterId: chapter.id } }" class="chapter-card-link">
                    <h4>{{ chapter.heading }}</h4>
                    <p>{{ chapter.description }}</p>
                </router-link>
                <div class="card-actions">
                    <button class="edit-btn" @click="openChapterModal(level, chapter)">Edit</button>
                    <button class="delete-btn" @click="confirmDeleteChapter(chapter)">Delete</button>
                </div>
              </div>
            </template>
            <p v-else class="no-chapters">No chapters in this level yet.</p>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="loading">Loading subject details...</div>

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
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API call to ${endpoint} failed with status ${response.status}: ${errorText}`);
      }
      return response.json();
    },
    async fetchSubjectDetails() {
      const subjectId = this.$route.params.subjectId;
      try {
        this.subject = await this.apiCall(`/api/admin/subjects/${subjectId}`);
      } catch (err) {
        console.error(err);
        alert("Failed to load subject details. You may be unauthorized.");
        this.$router.push('/admin_dashboard');
      }
    },
    openChapterModal(level, chapter = null) {
      if (chapter) {
        this.modal.isEdit = true;
        this.modal.data = { ...chapter };
      } else {
        this.modal.isEdit = false;
        this.modal.data = { id: null, heading: '', description: '', level: level };
      }
      this.showChapterModal = true;
    },
    closeChapterModal() {
      this.showChapterModal = false;
    },
    async handleChapterSubmit() {
      const { isEdit, data } = this.modal;
      const subjectId = this.subject.id;
      const endpoint = isEdit ? `/api/admin/chapters/${data.id}` : `/api/admin/subjects/${subjectId}/chapters`;
      const method = isEdit ? 'PUT' : 'POST';
      
      try {
        const result = await this.apiCall(endpoint, method, data);
        if (isEdit) {
          const index = this.subject.chapters[data.level].findIndex(c => c.id === data.id);
          this.subject.chapters[data.level][index] = data;
        } else {
          this.subject.chapters[data.level].push(result);
        }
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
        const levelChapters = this.subject.chapters[chapter.level];
        this.subject.chapters[chapter.level] = levelChapters.filter(c => c.id !== chapter.id);
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

<style>
@import '../assets/website_styles.css';
</style>