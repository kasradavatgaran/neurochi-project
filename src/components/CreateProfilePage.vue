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
              <label for="birth_height">قد (سانتی‌متر)</label>
              <input type="number" id="birth_height" v-model.number="form.birth_height" placeholder="مثلا: 50">
            </div>
            <div class="form-group">
              <label for="birth_weight">وزن (کیلوگرم)</label>
              <input type="number" id="birth_weight" v-model.number="form.birth_weight" placeholder="مثلا: 3.2" step="0.1">
            </div>
            <div class="form-group">
              <label for="birth_head_circumference">دور سر (سانتی‌متر)</label>
              <input type="number" id="birth_head_circumference" v-model.number="form.birth_head_circumference" placeholder="مثلا: 35">
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
        gestationWeek: '', 
        birth_height: null,
        birth_weight: null,
        birth_head_circumference: null,
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
            
            birth_height: this.form.birth_height ? parseFloat(this.form.birth_height) : null,
            birth_weight: this.form.birth_weight ? parseFloat(this.form.birth_weight) : null,
            birth_head_circumference: this.form.birth_head_circumference ? parseFloat(this.form.birth_head_circumference) : null,
          }
        };
        await axios.post('/create-profile', payload);
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
