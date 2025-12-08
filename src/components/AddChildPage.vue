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

