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
