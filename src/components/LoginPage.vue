<template>
  <div class="login-page-wrapper">
    <div class="login-container">
      <img src="@/assets/logo.svg" alt="Nerochi Logo" class="logo" />
      
      <h1>به نوروچی دستیار هوشمند والد خوش اومدی!</h1>
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
        <div class="form-group checkbox-container">
          <label for="terms">
            <router-link to="/privacy">قوانین حریم خصوصی</router-link>
            را مطالعه کرده‌ام و می پذیرم.
          </label>
          <input type="checkbox" id="terms" v-model="agreedToTerms" />
        </div>

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
import NerochiLogo from '@/assets/logo.svg';

export default {
  name: 'LoginPage',
  data() {
    return {
      phoneNumber: '',
      agreedToTerms: false,
      logo: NerochiLogo,
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
        await axios.post('/request-otp', payload);
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
