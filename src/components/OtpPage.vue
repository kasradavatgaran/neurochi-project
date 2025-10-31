<template>
  <div class="otp-page-wrapper">
    <div class="otp-container">
      <img src="@/assets/logo.svg" alt="Kidora Logo" class="logo" />
      
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
import kidoraLogo from '@/assets/logo.svg';

export default {
  name: 'OtpPage',
  props: {
    phoneNumber: { type: String, required: true },
  },
  data() {
    return {
      logo: kidoraLogo,
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

        const response = await axios.post('http://localhost:8000/verify-otp', payload);
        
        if (response.data.action === 'create_profile') {
          this.$router.push({
            name: 'CreateProfile',
            params: { phoneNumber: response.data.phone_number }
          });
        } else if (response.data.action === 'login') {
          localStorage.setItem('loggedInUserPhone', response.data.user_data.phone_number);
          this.$router.push('/dashboard');
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

          await axios.post('http://localhost:8000/request-otp', { phone_number: this.phoneNumber });
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

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;700&display=swap');

.otp-page-wrapper {
  direction: rtl;
  font-family: 'IBM Plex Sans Arabic', sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  background-color: #f8f5fc;
}
.otp-container {
  background-color: #ffffff;
  padding: 40px;
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 420px;
  text-align: center;
}
.logo {
  width: 90px;
  height: auto;
  margin-bottom: 30px;
}
h1 {
  font-weight: 700;
  font-size: 1.8rem;
  margin-bottom: 12px;
  color: #333;
}
p {
  color: #666;
  font-size: 0.95rem;
  margin-bottom: 10px;
}
.phone-number {
  font-weight: bold;
  color: #333;
  margin-bottom: 30px;
  font-size: 1.2rem;
  letter-spacing: 3px;
}
.otp-inputs {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 25px;
}
.otp-inputs input {
  width: 55px;
  height: 55px;
  text-align: center;
  font-size: 1.8rem;
  font-weight: bold;
  border: 1px solid #ddd;
  border-radius: 12px;
  transition: all 0.3s;
  font-family: 'IBM Plex Sans Arabic', sans-serif;
  color: #6A1B9A;
}
.otp-inputs input:focus {
  outline: none;
  border-color: #6A1B9A;
  box-shadow: 0 0 0 4px rgba(106, 27, 154, 0.15);
}
.error-message {
  color: #c0392b;
  margin-bottom: 15px;
  font-size: 0.9rem;
}
.submit-button {
  width: 100%;
  padding: 14px;
  background: #6A1B9A;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}
.submit-button:hover {
  background-color: #4A148C;
}
.resend-container {
  margin-top: 25px;
  font-size: 0.9rem;
  color: #888;
}
.resend-container a {
  color: #6A1B9A;
  text-decoration: none;
  font-weight: bold;
  margin-right: 5px;
}
.timer {
  display: flex;
  justify-content: center;
  gap: 5px;
}
</style>