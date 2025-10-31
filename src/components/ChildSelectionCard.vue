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

<script>
import axios from 'axios';
import DatePicker from 'vue3-persian-datetime-picker';

export default {
  name: 'EditChildPage',
  props: {
    childId: {
      type: [String, Number],
      required: true,
    }
  },
  components: { DatePicker },
  data() {
    return {
      form: {
        name: '',
        gender: '',
        birth_date: '',
        gestation_week: ''
      },
      originalChildName: '...'
    };
  },
  methods: {
    async fetchChildData() {
      try {
        const phoneNumber = localStorage.getItem('loggedInUserPhone');
        if (!phoneNumber) { this.$router.push('/'); return; }
        const response = await axios.get(`http://localhost:8000/me/${phoneNumber}`);
        const child = response.data.children.find(c => c.id == this.childId);
        
        if (child) {
          this.form = { ...child };
          this.originalChildName = child.name;
        } else {
          alert("فرزند مورد نظر یافت نشد.");
          this.$router.push('/dashboard');
        }
      } catch (error) {
        console.error("Error fetching child data:", error);
        alert("خطا در دریافت اطلاعات فرزند.");
      }
    },
    async handleSubmit() {
      const payload = {
        ...this.form,
        gestation_week: parseInt(this.form.gestation_week)
      };

      try {
        await axios.put(`http://localhost:8000/children/${this.childId}`, payload);
        alert('اطلاعات فرزند با موفقیت به‌روزرسانی شد.');
        this.$router.push('/dashboard');
      } catch (error) {
        console.error("Error updating child:", error.response || error);
        alert('خطا در ویرایش اطلاعات.');
      }
    }
  },
  mounted() {
    this.fetchChildData();
  }
}
</script>

<style scoped>
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
h2 { text-align: center; margin-bottom: 30px; color: #333; }
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 25px;
}
.form-group { display: flex; flex-direction: column; }
.form-group label { margin-bottom: 8px; font-weight: bold; color: #555; }
input, select {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-family: inherit;
  font-size: 1rem;
}
.submit-button {
  width: 100%; max-width: 250px; display: block; margin: 30px auto 10px;
  padding: 14px; background: #6A1B9A; color: white; border: none;
  border-radius: 8px; font-size: 1.1rem; cursor: pointer; transition: background-color 0.3s;
}
.submit-button:hover { background-color: #4A148C; }
.cancel-link {
  display: block; text-align: center; color: #555;
  text-decoration: none; margin-top: 10px;
}
</style>