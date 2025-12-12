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

<style scoped>
.page-wrapper {
  direction: rtl; font-family: 'IBM Plex Sans Arabic', sans-serif;
  min-height: 100vh; padding: 40px 20px; box-sizing: border-box;
  background-image: url('@/assets/background.svg'); background-size: cover;
  display: flex; justify-content: center; align-items: center;
}

.form-container {
  width: 100%; 
  max-width: 500px; 
  background: rgba(255, 255, 255, 0.98);
  padding: 40px; 
  border-radius: 20px; 
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

h2 { text-align: center; margin-bottom: 30px; color: #333; font-size: 1.5rem; }

.profile-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
}
.profile-preview {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 15px;
  border: 4px solid #f0e6ff; 
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.select-photo-btn {
  background: #f3f4f6;
  color: #4b5563;
  border: 1px solid #e5e7eb;
  padding: 8px 16px;
  border-radius: 99px;
  cursor: pointer;
  font-size: 0.9rem;
  font-family: inherit;
  transition: all 0.2s;
}
.select-photo-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.form-group { display: flex; flex-direction: column; margin-bottom: 25px; }
.form-group label { margin-bottom: 8px; font-weight: bold; color: #555; }
input {
  padding: 12px; border: 1px solid #ddd; border-radius: 10px;
  font-family: inherit; font-size: 1rem;
  width: 100%; box-sizing: border-box;
  background-color: #fff;
}
input:focus {
  outline: none;
  border-color: #6A1B9A;
  box-shadow: 0 0 0 3px rgba(106, 27, 154, 0.1);
}

.submit-button, .logout-button {
  width: 100%; display: block; margin-bottom: 15px; padding: 14px;
  color: white; border: none; border-radius: 12px; font-size: 1.1rem;
  cursor: pointer; transition: background-color 0.2s, transform 0.1s;
  font-weight: bold;
  font-family: inherit;
}
.submit-button { background: #6A1B9A; }
.logout-button { background-color: #ef4444; margin-top: 25px; } 
.submit-button:hover { background-color: #4A148C; transform: translateY(-2px); }
.logout-button:hover { background-color: #dc2626; transform: translateY(-2px); }

.cancel-link { 
  display: block; text-align: center; color: #6b7280; 
  text-decoration: none; margin-top: 15px; font-size: 0.95rem;
  padding: 10px;
}

@media (max-width: 600px) {
  .page-wrapper {
    padding: 15px;
    align-items: flex-start; 
  }

  .form-container {
    padding: 30px 20px;
    margin-top: 20px;
  }

  h2 {
    font-size: 1.3rem;
    margin-bottom: 25px;
  }

  .profile-preview {
    width: 100px;
    height: 100px;
  }

  .submit-button, .logout-button {
    padding: 12px;
    font-size: 1rem;
    border-radius: 10px;
  }
  
  .logout-button {
    margin-top: 30px; 
  }
}
</style>