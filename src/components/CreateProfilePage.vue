<template>
  <div class="profile-page-wrapper">
    <div class="form-container">
      <h1 class="main-title">ایجاد پروفایل</h1>
      <p class="main-subtitle">
        نام خود را ثبت کنید و مستقیم وارد چت عمومی شوید. افزودن فرزند اختیاری است و بعداً انجام می‌شود.
      </p>

      <form @submit.prevent="handleSubmit">
        <div class="form-section">
          <h2>اطلاعات شما</h2>
          <div class="form-group">
            <label for="parentName">نام و نام خانوادگی</label>
            <input
              id="parentName"
              v-model="parentName"
              type="text"
              placeholder="نام خود را وارد کنید"
              required
            >
          </div>
        </div>
        <div class="button-wrapper">
          <button type="submit" class="submit-button" :disabled="isSubmitting">
            {{ isSubmitting ? 'در حال ثبت...' : 'ورود به چت عمومی' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'CreateProfilePage',
  props: ['phoneNumber'],
  data() {
    return {
      parentName: '',
      isSubmitting: false,
    };
  },
  methods: {
    async handleSubmit() {
      const parentName = this.parentName.trim();
      if (!parentName) {
        alert('لطفاً نام و نام خانوادگی را وارد کنید.');
        return;
      }

      this.isSubmitting = true;
      try {
        await api.post('/create-profile', {
          phone_number: this.phoneNumber,
          parent_name: parentName,
        });
        localStorage.setItem('loggedInUserPhone', this.phoneNumber);
        this.$router.push('/dashboard');
      } catch (error) {
        console.error('Error creating profile:', error.response || error);
        const detail = error.response?.data?.detail;
        alert(typeof detail === 'string' ? detail : 'خطا در ثبت اطلاعات. لطفاً دوباره تلاش کنید.');
      } finally {
        this.isSubmitting = false;
      }
    },
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;700&display=swap');

.profile-page-wrapper {
  direction: rtl;
  min-height: 100dvh;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  font-family: 'IBM Plex Sans Arabic', sans-serif;
  background: url('@/assets/background.svg') center / cover;
}
.form-container {
  width: min(100%, 560px);
  box-sizing: border-box;
  padding: 34px 38px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
}
.main-title { margin: 0 0 8px; text-align: center; color: #333; font-size: 1.8rem; }
.main-subtitle { margin: 0 0 30px; text-align: center; color: #666; line-height: 1.9; }
.form-section { margin-bottom: 28px; }
.form-section h2 { margin: 0 0 20px; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0; color: #444; font-size: 1.1rem; }
.form-group { display: flex; flex-direction: column; }
.form-group label { margin-bottom: 8px; color: #555; font-weight: 500; }
.form-group input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font: inherit;
}
.form-group input:focus { outline: none; border-color: #6a1b9a; box-shadow: 0 0 0 3px rgba(106, 27, 154, 0.15); }
.button-wrapper { display: flex; justify-content: center; }
.submit-button {
  min-width: 220px;
  border: 0;
  border-radius: 10px;
  padding: 13px 24px;
  background: #6a1b9a;
  color: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.submit-button:disabled { opacity: 0.65; cursor: wait; }
@media (max-width: 560px) {
  .profile-page-wrapper { align-items: flex-start; padding: 16px 16px calc(16px + env(safe-area-inset-bottom)); }
  .form-container { padding: 28px 22px; margin-top: 8px; }
}
</style>
