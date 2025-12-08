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

<script>
import axios from 'axios';
import NerochiLogo from '@/assets/logo.svg';

export default {
  name: 'OtpPage',
  props: {
    phoneNumber: { type: String, required: true },
  },
  data() {
    return {
      logo: NerochiLogo,
      otp: ['', '', '', ''],
      errorMessage: '',
      timer: 90, 
      isTimerActive: false,
      timerInterval: null,
    };
  },
  computed: {
    formattedPhoneNumber() {
      if (!this.phoneNumber) return '';
      const persianNumber = this.toPersianDigits(this.phoneNumber);
      return `${persianNumber.substring(0, 4)} **** ${persianNumber.substring(8)}`;
    },
    formattedTimer() {
      const minutes = String(Math.floor(this.timer / 60)).padStart(2, '0');
      const seconds = String(this.timer % 60).padStart(2, '0');
      return this.toPersianDigits(`${minutes}:${seconds}`);
    },
  },
  methods: {
    handleInput(index) {
      this.errorMessage = '';
      const value = this.otp[index];
      if (!/^[0-9]$/.test(value)) {
        this.otp[index] = '';
        return;
      }
      if (value && index < 3) {
        this.$refs.otpInput[index + 1].focus();
      }
    },
    handleKeydown(index, event) {
      if (event.key === 'Backspace' && !this.otp[index] && index > 0) {
        this.$refs.otpInput[index - 1].focus();
      }
    },
    async handleVerification() {
  const enteredCode = this.otp.join('');
  if (enteredCode.length < 4) {
    this.errorMessage = 'لطفا کد ۴ رقمی را کامل وارد کنید.';
    return;
  }

  try {
    const payload = {
      phone_number: this.phoneNumber,
      otp_code: enteredCode,
    };

    const response = await axios.post('/verify-otp', payload);
    
    if (response.data.action === 'login') {
      localStorage.setItem('loggedInUserPhone', response.data.user_data.phone_number);
      this.$router.push('/dashboard');
    } 
    else if (response.data.action === 'create_profile') {
      this.$router.push({
        name: 'CreateProfile',
        params: { phoneNumber: response.data.phone_number }
      });
    } else {
      this.errorMessage = 'پاسخ سرور نامعتبر است.';
    }

  } catch (error) {
    this.errorMessage = error.response?.data?.detail || 'کد وارد شده صحیح نمی‌باشد.';
    console.error("Verification failed:", error.response || error);
  }
},
    startTimer() {
      this.timer = 90;
      this.isTimerActive = true;
      this.timerInterval = setInterval(() => {
        if (this.timer > 0) {
          this.timer--;
        } else {
          this.isTimerActive = false;
          clearInterval(this.timerInterval);
        }
      }, 1000);
    },
    async resendCode() {
      if (!this.isTimerActive) {
        try {
          this.errorMessage = '';
          this.otp = ['', '', '', ''];
          this.$refs.otpInput[0].focus();

          await axios.post('/request-otp', { phone_number: this.phoneNumber });
          alert(`کد جدید به شماره ${this.phoneNumber} ارسال شد.`);
          this.startTimer();
        } catch (error) {
          alert("خطا در ارسال مجدد کد.");
        }
      }
    },
    toPersianDigits(str) {
      const persianMap = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
      return str.toString().replace(/[0-9]/g, (m) => persianMap[parseInt(m)]);
    }
  },
  mounted() {
    this.$refs.otpInput[0].focus();
    this.startTimer();
  },
  beforeUnmount() {
    clearInterval(this.timerInterval);
  },
};
</script>
