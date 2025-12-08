<template>
  <div class="page-wrapper">
    <div class="form-container">
      <form @submit.prevent="handleSubmit">
        <h2>ویرایش اطلاعات {{ originalChildName }}</h2>
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
            <date-picker v-model="form.birth_date" required />
          </div>
          <div class="form-group">
            <label>هفته بارداری هنگام تولد</label>
            <input type="number" v-model="form.gestation_week" placeholder="مثلا: 38" required>
          </div>
        </div>
        <button type="submit" class="submit-button">ذخیره تغییرات</button>
        <router-link to="/dashboard" class="cancel-link">انصراف</router-link>
      </form>
    </div>
  </div>
</template>
