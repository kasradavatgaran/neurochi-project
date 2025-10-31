<template>
  <div class="login-page-wrapper">
    <div class="login-container">
      <img src="@/assets/logo.svg" alt="Kidora Logo" class="logo" />
      
      <h1>به کیدورا دستیار هوشمند والد خوش اومدی!</h1>
      <p>لطفا شماره همراه خود را برای دریافت کد فعال‌سازی وارد کنید.</p>
      
      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <input 
            type="tel" 
            v-model="phoneNumber" 
            placeholder="مثلا: ۰۹۱۲۳۴۵۶۷۸۹"
            autocomplete="off"
            maxlength="11"
            @input="clearError"
          />
        </div>
        
        <!-- چیدمان جدید برای چک‌باکس -->
        <div class="form-group checkbox-container">
          <label for="terms">
            <router-link to="/privacy">قوانین حریم خصوصی</router-link>
            را مطالعه کرده‌ام و می پذیرم.
          </label>
          <input type="checkbox" id="terms" v-model="agreedToTerms" />
        </div>

        <!-- کادر نمایش خطا (در صورت وجود) -->
        <div v-if="errorMessage" class="error-box">
          {{ errorMessage }}
        </div>
        
        <button type="submit" class="submit-button">ثبت</button>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import kidoraLogo from '@/assets/logo.svg';

export default {
  name: 'LoginPage',
  data() {
    return {
      phoneNumber: '',
      agreedToTerms: false,
      logo: kidoraLogo,
      errorMessage: '',
    };
  },
  methods: {
    async handleSubmit() {
      this.clearError();
      const phoneRegex = /^09\d{9}$/;
      if (!phoneRegex.test(this.phoneNumber)) {
        this.errorMessage = 'لطفا یک شماره موبایل معتبر وارد کنید.';
        return;
      }
      if (!this.agreedToTerms) {
        this.errorMessage = 'برای ادامه، لطفا قوانین حریم خصوصی را بپذیرید.';
        return;
      }

      try {
        const payload = { phone_number: this.phoneNumber };
        await axios.post('http://localhost:8000/request-otp', payload);
        this.$router.push({
          name: 'OtpPage',
          params: { phoneNumber: this.phoneNumber },
        });
      } catch (error) {
        console.error("Error requesting OTP:", error);
        if (error.request) {
          this.errorMessage = 'خطا در ارتباط با سرور. لطفا اتصال اینترنت خود را بررسی کنید.';
        } else {
          this.errorMessage = 'یک خطای پیش‌بینی نشده رخ داد.';
        }
      }
    },
    clearError() {
      this.errorMessage = '';
    }
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;700&display=swap');

.login-page-wrapper {
  direction: rtl;
  font-family: 'IBM Plex Sans Arabic', sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  background-image: url('@/assets/background.svg');
  background-size: cover;
  padding: 20px;
  box-sizing: border-box;
}
.login-container {
  background-color: #ffffff;
  padding: 40px 50px;
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 450px;
  text-align: center;
}
.logo {
  width: 90px;
  height: auto;
  margin-bottom: 25px;
}
h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 10px;
}
p {
  font-size: 0.95rem;
  color: #666;
  margin-bottom: 30px;
}
.login-form {
  width: 100%;
}
.form-group {
  margin-bottom: 20px;
  width: 100%;
}
input[type="tel"] {
  width: 100%;
  padding: 14px;
  border: 1px solid #ddd;
  border-radius: 99px; /* گوشه‌های کاملا گرد */
  font-size: 1.1rem;
  text-align: center;
  box-sizing: border-box;
  transition: all 0.3s ease;
  direction: ltr;
}
input[type="tel"]::placeholder {
  color: #aaa;
  font-family: 'IBM Plex Sans Arabic', sans-serif;
}
input[type="tel"]:focus {
  outline: none;
  border-color: #6A1B9A;
  box-shadow: 0 0 0 4px rgba(106, 27, 154, 0.1);
}
.checkbox-container {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: row-reverse;
  gap: 10px;
  font-size: 0.9rem;
  color: #555;
}
.checkbox-container label { cursor: pointer; }
.checkbox-container a {
  color: #BA68C8;
  text-decoration: none;
  font-weight: bold;
}
input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  background-color: #fff;
  margin: 0;
  font: inherit;
  color: currentColor;
  width: 1.15em;
  height: 1.15em;
  border: 0.15em solid #ddd;
  border-radius: 0.25em;
  transform: translateY(-0.075em);
  display: grid;
  place-content: center;
  cursor: pointer;
}
input[type="checkbox"]::before {
  content: "";
  width: 0.65em;
  height: 0.65em;
  transform: scale(0);
  transition: 120ms transform ease-in-out;
  box-shadow: inset 1em 1em #6A1B9A;
  transform-origin: bottom left;
  clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
}
input[type="checkbox"]:checked::before {
  transform: scale(1);
}
input[type="checkbox"]:checked {
  border-color: #6A1B9A;
}

.error-box {
  background-color: #fff2f2;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
  border-radius: 12px;
  padding: 12px 15px;
  margin-bottom: 20px;
  font-size: 0.9rem;
  text-align: center;
}

.submit-button {
  width: 100%;
  padding: 15px;
  background: #6A1B9A;
  color: white;
  border: none;
  border-radius: 99px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
}
.submit-button:hover {
  background: #4A148C;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(106, 27, 154, 0.3);
}
</style>