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
          await axios.put(`/users/${phoneNumber}?parent_name=${this.parentName}`);
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
          await axios.post(`/users/${phoneNumber}/upload-profile-image`, formData);
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
        const response = await axios.get(`/me/${phoneNumber}`);
        this.parentName = response.data.parent_name;
        if (response.data.profile_image_url) {
          this.profileImagePreview = `/${response.data.profile_image_url}`;
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
