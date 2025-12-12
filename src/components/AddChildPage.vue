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
        <div class="form-section">
          <h3 class="section-title">اطلاعات زمان تولد (اختیاری)</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>قد (سانتی‌متر)</label>
            <input type="number" v-model.number="form.birth_height" placeholder="مثلا: 50">
          </div>
          <div class="form-group">
            <label>وزن (کیلوگرم)</label>
            <input type="number" v-model.number="form.birth_weight" placeholder="مثلا: 3.2" step="0.1">
          </div>
          <div class="form-group">
            <label>دور سر (سانتی‌متر)</label>
            <input type="number" v-model.number="form.birth_head_circumference" placeholder="مثلا: 35">
          </div>
        </div>
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
import jMoment from 'moment-jalaali';

export default {
  name: 'AddChildPage',
  components: { DatePicker },
  data() {
    return {
      form: {
        name: '',
        gender: '',
        birth_date_jalali: '',
        gestation_week: null, 
        birth_height: null,
        birth_weight: null,
        birth_head_circumference: null,
      }
    };
  },
  methods: {
    async handleSubmit() {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      if (!phoneNumber) {
        this.$router.push('/');
        return;
      }
      
      if (!this.form.name || !this.form.gender || !this.form.birth_date_jalali || !this.form.gestation_week) {
        alert("لطفا فیلدهای نام، جنسیت، تاریخ تولد و هفته بارداری را تکمیل کنید.");
        return;
      }

      try {
        const birth_date_gregorian = jMoment(this.form.birth_date_jalali, 'jYYYY/jMM/jDD').format('YYYY-MM-DD');

        const payload = {
          name: this.form.name,
          gender: this.form.gender,
          birth_date: birth_date_gregorian,
          gestation_week: parseInt(this.form.gestation_week),
          
  
          birth_height: this.form.birth_height ? parseFloat(this.form.birth_height) : undefined,
          birth_weight: this.form.birth_weight ? parseFloat(this.form.birth_weight) : undefined,
          birth_head_circumference: this.form.birth_head_circumference ? parseFloat(this.form.birth_head_circumference) : undefined,
        };

        await axios.post(`/children?phone_number=${phoneNumber}`, payload);
        
        alert('فرزند جدید با موفقیت اضافه شد.');
        this.$router.push('/dashboard');

      } catch (error) {
        console.error("Error adding child:", error.response || error);
        
        if (error.response && error.response.status === 422 && error.response.data.detail) {
          const errorDetails = error.response.data.detail[0];
          const fieldName = errorDetails.loc.join(' -> '); 
          const errorMessage = errorDetails.msg;
          alert(`خطا در فیلد '${fieldName}': ${errorMessage}`);
        } else {
          alert('خطا در افزودن فرزند. لطفا ورودی‌های خود را بررسی کنید.');
        }
      }
    }
  }
}
</script>

<style scoped>
.page-wrapper {
  direction: rtl; font-family: 'IBM Plex Sans Arabic', sans-serif;
  min-height: 100vh; padding: 40px 20px; box-sizing: border-box;
  background-image: url('@/assets/background.svg'); background-size: cover;
  display: flex; justify-content: center; align-items: flex-start; 
}

.form-container {
  width: 100%; 
  max-width: 700px; 
  background: rgba(255, 255, 255, 0.98);
  padding: 40px; 
  border-radius: 20px; 
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
  margin-top: 20px; 
  margin-bottom: 20px; 
}

h2 { text-align: center; margin-bottom: 30px; color: #333; }

.form-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
  gap: 25px; 
}

.form-group { display: flex; flex-direction: column; }
.form-group label { margin-bottom: 8px; font-weight: bold; color: #555; font-size: 0.9rem; }

input, select { 
  padding: 12px; 
  border: 1px solid #ddd; 
  border-radius: 8px; 
  font-family: inherit; 
  font-size: 1rem; 
  width: 100%; 
  box-sizing: border-box;
  background-color: #fff;
}
input:focus, select:focus {
  outline: none;
  border-color: #6A1B9A;
  box-shadow: 0 0 0 3px rgba(106, 27, 154, 0.1);
}

.submit-button {
  width: 100%; max-width: 250px; display: block; margin: 30px auto 10px;
  padding: 14px; background: #6A1B9A; color: white; border: none;
  border-radius: 8px; font-size: 1.1rem; cursor: pointer; font-weight: bold;
  transition: all 0.2s;
}
.submit-button:hover {
  background-color: #4A148C;
  transform: translateY(-2px);
}

.cancel-link { display: block; text-align: center; color: #555; text-decoration: none; margin-top: 15px; }

.section-title {
  margin-top: 35px;
  margin-bottom: 25px;
  text-align: right;
  font-size: 1.1rem;
  color: #6A1B9A;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
  font-weight: bold;
}

@media (max-width: 600px) {
  .page-wrapper {
    padding: 15px;
  }

  .form-container {
    padding: 25px 20px; 
    margin-top: 10px;
  }

  h2 {
    font-size: 1.4rem;
    margin-bottom: 20px;
  }

  .form-grid {
    grid-template-columns: 1fr; 
    gap: 15px;
  }

  input, select {
    padding: 10px;
    font-size: 16px; 
  }

  .section-title {
    font-size: 1rem;
    margin-top: 25px;
    margin-bottom: 15px;
  }

  .submit-button {
    max-width: 100%; 
    margin-top: 20px;
  }
}
</style>