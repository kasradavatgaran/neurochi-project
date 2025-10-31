<template>
  <div class="page-wrapper">
    <div class="form-container">
      <h2>ویرایش پروفایل</h2>
      <div class="profile-uploader">
        <img :src="profileImagePreview" class="profile-preview" alt="Profile Preview">
        <input type="file" @change="onFileSelected" accept="image/*" ref="fileInput" style="display: none;">
        <button @click="$refs.fileInput.click()" class="select-photo-btn">انتخاب عکس جدید</button>
      </div>

      <div class="form-group">
        <label>نام و نام خانوادگی</label>
        <input v-model="parentName" placeholder="نام جدید را وارد کنید">
      </div>
      
      <button @click="updateProfile" class="submit-button">ذخیره تغییرات</button>
      <button @click="logout" class="logout-button">خروج از حساب</button>
      <router-link to="/dashboard" class="cancel-link">بازگشت به داشبورد</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  name: 'EditProfilePage',
  data() {
    return {
      parentName: '',
      selectedFile: null,
      profileImagePreview: 'https://via.placeholder.com/100',
    };
  },
  methods: {
    onFileSelected(event) {
      this.selectedFile = event.target.files[0];
      if (this.selectedFile) {
        this.profileImagePreview = URL.createObjectURL(this.selectedFile);
      }
    },
    async updateProfile() {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      if (!phoneNumber) { this.$router.push('/'); return; }
      if (this.parentName && this.parentName.trim()) {
        try {
          await axios.put(`http://localhost:8000/users/${phoneNumber}?parent_name=${this.parentName}`);
        } catch (error) {
          console.error("Error updating name:", error);
          alert('خطا در به‌روزرسانی نام.');
          return;
        }
      }
      if (this.selectedFile) {
        const formData = new FormData();
        formData.append("file", this.selectedFile);
        try {
          await axios.post(`http://localhost:8000/users/${phoneNumber}/upload-profile-image`, formData);
        } catch (error) {
          console.error("Error uploading image:", error);
          alert('خطا در آپلود عکس.');
          return;
        }
      }

      alert('پروفایل با موفقیت به‌روزرسانی شد.');
      this.$router.push('/dashboard');
    },
    logout() {
      if (confirm('آیا برای خروج از حساب مطمئن هستید؟')) {
        localStorage.removeItem('loggedInUserPhone');
        this.$router.push('/');
      }
    },
    async fetchCurrentData() {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      if (!phoneNumber) { this.$router.push('/'); return; }
      try {
        const response = await axios.get(`http://localhost:8000/me/${phoneNumber}`);
        this.parentName = response.data.parent_name;
        if (response.data.profile_image_url) {
          this.profileImagePreview = `http://localhost:8000/${response.data.profile_image_url}`;
        }
      } catch (error) {
        console.error("Error fetching current data:", error);
      }
    }
  },
  mounted() {
    this.fetchCurrentData();
  }
}
</script>

<style scoped>
.page-wrapper {
  direction: rtl; font-family: 'IBM Plex Sans Arabic', sans-serif;
  min-height: 100vh; padding: 40px 20px; box-sizing: border-box;
  background-image: url('@/assets/background.svg'); background-size: cover;
  display: flex; justify-content: center; align-items: center;
}
.form-container {
  width: 100%; max-width: 500px; background: rgba(255, 255, 255, 0.98);
  padding: 40px; border-radius: 20px; box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
}
h2 { text-align: center; margin-bottom: 30px; }
.profile-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 25px;
}
.profile-preview {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 15px;
  border: 3px solid #eee;
}
.select-photo-btn {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ccc;
  padding: 8px 15px;
  border-radius: 8px;
  cursor: pointer;
}
.form-group { display: flex; flex-direction: column; margin-bottom: 20px; }
.form-group label { margin-bottom: 8px; font-weight: bold; }
input {
  padding: 12px; border: 1px solid #ddd; border-radius: 8px;
  font-family: inherit; font-size: 1rem;
}
.submit-button, .logout-button {
  width: 100%; display: block; margin-bottom: 15px; padding: 14px;
  color: white; border: none; border-radius: 8px; font-size: 1.1rem;
  cursor: pointer; transition: background-color 0.3s;
}
.submit-button { background: #6A1B9A; }
.logout-button { background-color: #c0392b; }
.submit-button:hover { background-color: #4A148C; }
.logout-button:hover { background-color: #a93226; }
.cancel-link { display: block; text-align: center; color: #555; text-decoration: none; }
</style>