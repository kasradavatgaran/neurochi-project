<template>
  <div class="privacy-wrapper">
    <div class="privacy-container">
      <h1>قوانین و حریم خصوصی</h1>
      <div class="content">
        <p>اینجا مجموعه قوانین سایت کیدورا قرار می‌گیرد. کاربر با ثبت نام در سایت، تمام این قوانین را می‌پذیرد.</p>
        <h2>ماده ۱: اطلاعات کاربری</h2>
        <p>اطلاعات وارد شده توسط کاربر، از جمله شماره همراه، نزد کیدورا محفوظ خواهد ماند و در اختیار هیچ شخص یا سازمان ثالثی قرار نخواهد گرفت مگر با حکم قضایی.</p>
        <h2>ماده ۲: مسئولیت محتوا</h2>
        <p>مسئولیت تمام محتوای تولید شده توسط کاربر بر عهده خود کاربر است و کیدورا هیچ مسئولیتی در قبال آن ندارد.</p>
        <h2>ماده ۳: شرایط استفاده</h2>
        <p>استفاده از سرویس‌های کیدورا برای مقاصد غیرقانونی ممنوع است. در صورت مشاهده تخلف، حساب کاربری مسدود خواهد شد.</p>
      </div>
      <router-link to="/" class="back-button">بازگشت به صفحه ورود</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PrivacyPolicy'
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;700&display=swap');

.privacy-wrapper {
  font-family: 'IBM Plex Sans Arabic', sans-serif;
  background-color: #f4f4f9;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  direction: rtl;
  padding: 20px;
  box-sizing: border-box;
}

.privacy-container {
  padding: 40px;
  max-width: 800px;
  background-color: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
  color: #333;
}

h1, h2 {
  border-bottom: 2px solid #6A1B9A;
  padding-bottom: 10px;
  margin-bottom: 20px;
  color: #6A1B9A;
}

.content {
  line-height: 1.8;
  text-align: right;
  max-height: 50vh;
  overflow-y: auto;
  padding-left: 15px;
}

.back-button {
  display: inline-block;
  margin-top: 30px;
  padding: 12px 25px;
  background-color: #6A1B9A;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: bold;
  transition: all 0.3s;
}

.back-button:hover {
  background-color: #4A148C;
  transform: translateY(-2px);
}
</style>