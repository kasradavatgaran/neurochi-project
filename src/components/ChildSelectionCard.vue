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
        const response = await axios.get(`/me/${phoneNumber}`);
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
        await axios.put(`/children/${this.childId}`, payload);
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
