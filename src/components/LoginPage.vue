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
