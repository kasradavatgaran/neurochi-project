<template>
  <div class="otp-page-wrapper">
    <div class="otp-container">
      <img src="@/assets/logo.svg" alt="Nerochi Logo" class="logo" />
      
      <h1>کد تایید را وارد کنید</h1>
      <p>کد تایید ۴ رقمی ارسال شده به شماره زیر را وارد کنید:</p>
      <div class="phone-number" dir="ltr">{{ formattedPhoneNumber }}</div>
      
      <form @submit.prevent="handleVerification" class="otp-form">
        <div class="otp-inputs" dir="ltr">
          <input
            v-for="(digit, index) in otp"
            :key="index"
            ref="otpInput"
            v-model="otp[index]"
            type="tel"
            maxlength="1"
            @input="handleInput(index)"
            @keydown="handleKeydown(index, $event)"
          />
        </div>
        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
        
        <button type="submit" class="submit-button">تایید و ادامه</button>

        <div class="resend-container">
          <div v-if="isTimerActive" class="timer">
            <span>{{ formattedTimer }}</span>
            <span> تا ارسال مجدد کد</span>
          </div>
          <div v-else>
            <span>کدی دریافت نکردید؟ </span>
            <a href="#" @click.prevent="resendCode">ارسال مجدد</a>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>
