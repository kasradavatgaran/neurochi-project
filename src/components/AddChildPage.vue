<!-- ============================================= -->
<!-- فایل کامل و نهایی: src/components/AddChildPage.vue -->
<!-- ============================================= -->
<template>
  <div class="page-wrapper">
    <div class="form-container">
      <form @submit.prevent="handleSubmit">
        <h2>اطلاعات فرزند جدید</h2>
        
        <div class="form-grid">
          <div class="form-group">
            <label>نام کودک</label>
            <input type="text" v-model="form.name" required>
          </div>
          <div class="form-group">
            <label>جنسیت</label>
            <select v-model="form.gender" required>
              <option disabled value="">انتخاب کنید</option>
              <option>پسر</option>
              <option>دختر</option>
            </select>
          </div>
          <div class="form-group">
            <label>تاریخ تولد</label>
            <date-picker v-model="form.birth_date_jalali" placeholder="تاریخ تولد را انتخاب کنید" required />
          </div>
          <div class="form-group">
            <label>هفته بارداری هنگام تولد</label>
            <input type="number" v-model="form.gestation_week" placeholder="مثلا: 38" required>
          </div>
        </div>
        <button type="submit" class="submit-button">ثبت فرزند</button>
        <router-link to="/dashboard" class="cancel-link">انصراف</router-link>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import DatePicker from 'vue3-persian-datetime-picker';
import jMoment from 'moment-jalaali'; // کتابخانه تاریخ را وارد می‌کنیم

export default {
  name: 'AddChildPage',
  components: { DatePicker },
  data() {
    return {
      form: {
        name: '',
        gender: '',
        birth_date_jalali: '', // یک فیلد جدا برای تاریخ شمسی
        gestation_week: ''
      }
    };
  },
  methods: {
    async handleSubmit() {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      if (!phoneNumber) { this.$router.push('/'); return; }
      
      if (!this.form.name || !this.form.gender || !this.form.birth_date_jalali || !this.form.gestation_week) {
        alert("لطفا تمام فیلدها را تکمیل کنید.");
        return;
      }

      try {
        // ۱. تبدیل تاریخ شمسی به میلادی
        const birth_date_gregorian = jMoment(this.form.birth_date_jalali, 'jYYYY/jMM/jDD').format('YYYY-MM-DD');

        // ۲. ساختار payload با تاریخ میلادی
        const payload = {
          name: this.form.name,
          gender: this.form.gender,
          birth_date: birth_date_gregorian,
          gestation_week: parseInt(this.form.gestation_week)
        };

        // ۳. ارسال درخواست به بک‌اند
        await axios.post(`http://localhost:8000/children?phone_number=${phoneNumber}`, payload);
        
        alert('فرزند جدید با موفقیت اضافه شد.');
        this.$router.push('/dashboard');

      } catch (error) {
        console.error("Error adding child:", error.response || error);

        // مدیریت خطای بهتر برای نمایش پیام دقیق از سمت سرور
        if (error.response && error.response.data && error.response.data.detail) {
          // اگر خطای ولیدیشن Pydantic باشد
          const errorDetails = error.response.data.detail[0];
          const fieldName = errorDetails.loc[1];
          const errorMessage = errorDetails.msg;
          alert(`خطا در فیلد '${fieldName}': ${errorMessage}`);
        } else {
          // خطاهای عمومی دیگر
          alert('خطا در افزودن فرزند. لطفا ورودی‌های خود را بررسی کنید.');
        }
      }
    }
  }
}
</script>

<style scoped>
/* استایل‌های این فایل از پاسخ قبلی بدون تغییر باقی می‌مانند */
.page-wrapper {
  direction: rtl; font-family: 'IBM Plex Sans Arabic', sans-serif;
  min-height: 100vh; padding: 40px 20px; box-sizing: border-box;
  background-image: url('@/assets/background.svg'); background-size: cover;
  display: flex; justify-content: center; align-items: center;
}
.form-container {
  width: 100%; max-width: 700px; background: rgba(255, 255, 255, 0.98);
  padding: 40px; border-radius: 20px; box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
}
h2 { text-align: center; margin-bottom: 30px; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 25px; }
.form-group { display: flex; flex-direction: column; }
.form-group label { margin-bottom: 8px; font-weight: bold; }
input, select { padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-family: inherit; font-size: 1rem; }
.submit-button {
  width: 100%; max-width: 250px; display: block; margin: 30px auto 10px;
  padding: 14px; background: #6A1B9A; color: white; border: none;
  border-radius: 8px; font-size: 1.1rem; cursor: pointer;
}
.cancel-link { display: block; text-align: center; color: #555; text-decoration: none; }
</style>