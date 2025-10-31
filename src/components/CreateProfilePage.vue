<template>
  <div class="profile-page-wrapper">
    <div class="form-container">
      <h1 class="main-title">ایجاد پروفایل</h1>
      <p class="main-subtitle">برای شروع، لطفا اطلاعات خود و فرزندتان را وارد کنید.</p>

      <form @submit.prevent="handleSubmit">
        <div class="form-section">
          <h2>اطلاعات شما</h2>
          <div class="form-group full-width">
            <label for="parentName">نام و نام خانوادگی</label>
            <input type="text" id="parentName" v-model="form.parentName" placeholder="نام خود را وارد کنید">
          </div>
        </div>
        <div class="form-section">
          <h2>اطلاعات کودک</h2>
          <div class="form-grid">
            <div class="form-group">
              <label for="childName">نام کودک</label>
              <input type="text" id="childName" v-model="form.childName" placeholder="نام کودک را وارد کنید">
            </div>
            <div class="form-group">
              <label for="gender">جنسیت کودک</label>
              <select id="gender" v-model="form.gender">
                <option disabled value="">جنسیت کودک را انتخاب کنید</option>
                <option value="boy">پسر</option>
                <option value="girl">دختر</option>
              </select>
            </div>
            <div class="form-group date-group">
              <label for="birthDate">تاریخ تولد</label>
              <date-picker
                v-model="form.birthDate"
                custom-input=".custom-datepicker-input"
                format="YYYY-MM-DD"
                display-format="jDD jMMMM jYYYY"
              />
              <input type="text" class="custom-datepicker-input" readonly placeholder="mm/dd/yyyy" />
            </div>
            <div class="form-group">
              <label for="relationship">نسبت با کودک</label>
              <select id="relationship" v-model="form.relationship">
                <option disabled value="">نسبت خود را با کودک مشخص کنید</option>
                <option value="mother">مادر</option>
                <option value="father">پدر</option>
                <option value="other">سایر</option>
              </select>
            </div>
            <div class="form-group">
              <label for="gestationWeek">تعداد هفته بارداری</label>
              <select id="gestationWeek" v-model.number="form.gestationWeek">
                <option disabled value="">هفته بارداری را انتخاب کنید</option>
                <option v-for="week in 42" :key="week" :value="week">{{ week }}</option>
              </select>
              <p class="help-text">کودک در هفته چندم بارداری متولد شده است.</p>
            </div>
          </div>
        </div>
        <div class="form-section">
          <h2>اطلاعات زمان تولد <span class="optional-text">(اختیاری)</span></h2>
          <div class="form-grid bottom-grid">
            <div class="form-group">
              <label for="height">قد (سانتی‌متر)</label>
              <input type="number" id="height" v-model.number="form.height" placeholder="مثلا: 50">
            </div>
            <div class="form-group">
              <label for="weight">وزن (کیلوگرم)</label>
              <input type="number" id="weight" v-model.number="form.weight" placeholder="مثلا: 3.2" step="0.1">
            </div>
            <div class="form-group">
              <label for="headCircumference">دور سر (سانتی‌متر)</label>
              <input type="number" id="headCircumference" v-model.number="form.headCircumference" placeholder="مثلا: 35">
            </div>
          </div>
        </div>
        
        <div class="button-wrapper">
          <button type="submit" class="submit-button">ثبت و ادامه</button>
        </div>
      </form>
    </div>
  </div>
</template>

// فایل: src/components/CreateProfilePage.vue

<script>
import axios from 'axios';
import DatePicker from 'vue3-persian-datetime-picker';

export default {
  name: 'CreateProfilePage',
  props: ['phoneNumber'],
  components: {
    DatePicker
  },
  data() {
    return {
      form: {
        parentName: '',
        childName: '',
        birthDate: '', 
        gender: '',
        relationship: '',
        gestationWeek: '', 
        height: null,
        weight: null,
        headCircumference: null,
      },
    };
  },
  methods: {
    async handleSubmit() {
      const requiredFields = {
        parentName: 'نام و نام خانوادگی', childName: 'نام کودک', birthDate: 'تاریخ تولد',
        gender: 'جنسیت کودک', relationship: 'نسبت با کودک', gestationWeek: 'تعداد هفته بارداری',
      };
      for (const field in requiredFields) {
        if (!this.form[field]) {
          alert(`لطفا فیلد "${requiredFields[field]}" را تکمیل کنید.`);
          return;
        }
      }

      try {
        const payload = {
          phone_number: this.phoneNumber,
          parent_name: this.form.parentName,
          child: {
            name: this.form.childName,
            birth_date: this.form.birthDate,
            gender: this.form.gender,
            gestation_week: parseInt(this.form.gestationWeek, 10),
            height: this.form.height ? parseFloat(this.form.height) : null,
            weight: this.form.weight ? parseFloat(this.form.weight) : null,
            head_circumference: this.form.headCircumference ? parseFloat(this.form.headCircumference) : null,
          }
        };
        await axios.post('http://localhost:8000/create-profile', payload);
        alert('فرزند شما با موفقیت ثبت شد!');
        localStorage.setItem('loggedInUserPhone', this.phoneNumber);
        this.$router.push('/dashboard');

      } catch (error) {
        console.error("Error creating profile:", error.response || error);
        if (error.response && error.response.data && error.response.data.detail) {
            const errorDetails = error.response.data.detail[0];
            const fieldName = errorDetails.loc[1];
            const errorMessage = errorDetails.msg;
            alert(`خطا در فیلد '${fieldName}': ${errorMessage}`);
        } else {
            alert('خطا در ثبت اطلاعات. لطفا دوباره تلاش کنید.');
        }
      }
    },
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;700&display=swap');

.profile-page-wrapper {
  direction: rtl;
  font-family: 'IBM Plex Sans Arabic', sans-serif;
  min-height: 100vh;
  padding: 40px 20px;
  box-sizing: border-box;
  background-image: url('@/assets/background.svg');
  background-size: cover;
  background-position: center;
  display: flex;
  justify-content: center;
  align-items: center;
}

.form-container {
  width: 100%;
  max-width: 900px;
  background: rgba(255, 255, 255, 0.98);
  padding: 30px 40px;
  border-radius: 20px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.main-title {
  text-align: center;
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: #333;
}
.main-subtitle {
  text-align: center;
  font-size: 1rem;
  color: #666;
  margin-bottom: 30px;
}

.form-section {
  margin-bottom: 35px;
}
.form-section h2 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #444;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e0e0e0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 25px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: #555;
}

input, select, .custom-datepicker-input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  font-family: 'IBM Plex Sans Arabic', sans-serif;
  transition: all 0.2s ease-in-out;
  background-color: #fff;
}

input:focus, select:focus, .custom-datepicker-input:focus {
  outline: none;
  border-color: #6A1B9A;
  box-shadow: 0 0 0 3px rgba(106, 27, 154, 0.15);
}

.optional-text {
  font-size: 0.9rem;
  font-weight: 400;
  color: #888;
}

.help-text {
  font-size: 0.75rem;
  color: #777;
  margin-top: 8px;
}

.button-wrapper {
  text-align: center;
  margin-top: 30px;
}
.submit-button {
  width: 100%;
  max-width: 250px;
  padding: 14px;
  background: #6A1B9A;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}
.submit-button:hover {
  background: #4A148C;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.date-group {
  position: relative;
}
.custom-datepicker-input {
  width: 100%;
  box-sizing: border-box;
  cursor: pointer;
}
:deep(.vpd-input-group) {
  display: none;
}
</style>