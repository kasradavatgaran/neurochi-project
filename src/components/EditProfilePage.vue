<template>
  <div class="page-wrapper">
    <div class="form-container">
      <h2>ویرایش پروفایل</h2>
      <div class="profile-uploader">
        <img :src="profileImagePreview" class="profile-preview" alt="Profile Preview">
        <input type="file" @change="onFileSelected" accept="image/*" ref="fileInput" style="display: none;">
        <button @click="$refs.fileInput.click()" class="select-photo-btn">انتخاب عکس جدید</button>
      </div>

      <div class="form-group">
        <label>نام و نام خانوادگی</label>
        <input v-model="parentName" placeholder="نام جدید را وارد کنید">
      </div>
      
      <button @click="updateProfile" class="submit-button">ذخیره تغییرات</button>
      <button @click="logout" class="logout-button">خروج از حساب</button>
      <router-link to="/dashboard" class="cancel-link">بازگشت به داشبورد</router-link>
    </div>
  </div>
</template>
