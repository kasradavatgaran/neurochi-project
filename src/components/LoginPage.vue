<template>
    <div class="login-page-wrapper">
      <div class="login-container">
        <img :src="logo" alt="Kidora Logo" class="logo" />
        
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
            />
          </div>
          
          <div class="form-group checkbox-container">
            <input type="checkbox" id="terms" v-model="agreedToTerms" />
            <label for="terms">
              <router-link to="/privacy">قوانین حریم خصوصی</router-link>
              را مطالعه کرده‌ام و می پذیرم.
            </label>
          </div>
          
          <button type="submit" class="submit-button">ثبت و دریافت کد</button>
        </form>
      </div>
    </div>
  </template>
  
  <script>
  import kidoraLogo from '@/assets/logo.svg';
  import backgroundpic from '@/assets/background.svg';
  
  export default {
    name: 'LoginPage',
    data() {
      return {
        phoneNumber: '',
        agreedToTerms: false,
        logo: kidoraLogo,
        backgroundImage: `url(${backgroundpic})`,
      };
    },
    methods: {
      handleSubmit() {
        const phoneRegex = /^09\d{9}$/;
        if (!phoneRegex.test(this.phoneNumber)) {
          alert('لطفا یک شماره موبایل معتبر (۱۱ رقمی که با 09 شروع شود) وارد کنید.');
          return;
        }
        if (!this.agreedToTerms) {
          alert('برای ادامه، لطفا قوانین حریم خصوصی را بپذیرید.');
          return;
        }
        this.$router.push({
          name: 'OtpPage',
          params: { phoneNumber: this.phoneNumber },
        });
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
    padding: 0;
    box-sizing: border-box;
    background-color: #F8F5FC;
    background-image: v-bind(backgroundImage);
    background-size: cover;
    background-position: center;
  }
  .login-container {
    background-color: #ffffff;
    padding: 30px 40px;
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
    width: 100%;
    max-width: 420px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .logo { width: 72px; height: auto; margin-bottom: 24px; }
  h1, p { width: 100%; text-align: right; }
  h1 { font-size: 1.1rem; font-weight: 700; color: #333; margin-bottom: 8px; }
  p { font-size: 0.9rem; color: #666; margin-bottom: 24px; }
  .login-form { width: 100%; }
  .form-group { margin-bottom: 20px; width: 100%; }
  input[type="tel"] {
    width: 100%;
    padding: 14px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1rem;
    box-sizing: border-box;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
    font-family: 'IBM Plex Sans Arabic', sans-serif;
    text-align: left;
    direction: ltr;
  }
  input[type="tel"]:focus { outline: none; border-color: #6A1B9A; }
  input[type="tel"]:not(:placeholder-shown) { text-align: center; direction: rtl; }
  .checkbox-container {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
    font-size: 0.8rem;
    color: #555;
    padding-right: 5px;
  }
  input[type="checkbox"] { width: 16px; height: 16px; accent-color: #6A1B9A; }
  
  .checkbox-container a {
    color: #BA68C8; 
    text-decoration: none;
    font-weight: bold;
  }
  .submit-button {
    width: 100%;
    padding: 14px;
    background: #6A1B9A;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: 'IBM Plex Sans Arabic', sans-serif;
  }
  .submit-button:hover { transform: translateY(-2px); filter: brightness(1.1); }
  </style>