<template>
  <div class="dashboard-wrapper">
    <aside class="sidebar">
      <div class="sidebar-header">
        <img src="@/assets/logo.svg" alt="Kidora Logo" class="logo">
        <span>کیدورا (ورژن ۱.۱)</span>
      </div>
      
      <div class="children-list">
        <div 
          v-for="child in children" 
          :key="child.id" 
          class="child-item"
          :class="{ active: selectedChild && selectedChild.id === child.id }"
          @click="selectChild(child)">
          <div class="child-info">
            <div class="child-icon-wrapper" v-html="child.gender === 'دختر' ? icons.girl : icons.boy"></div>
            <span>{{ child.name }}</span>
          </div>
          <div class="options-menu">
            <span class="options-icon" @click.stop="toggleMenu(child.id)">⋮</span>
            <div v-if="activeMenu === child.id" class="dropdown-menu" @click.stop>
              <a href="#" @click.prevent="editChild(child)">ویرایش</a>
              <a href="#" @click.prevent="deleteChild(child.id)" class="delete">حذف</a>
            </div>
          </div>
        </div>
      </div>

      <div class="sidebar-footer">
        <router-link to="/add-child" class="add-child-btn">
          <span>اضافه کردن فرزند</span>
          <span class="plus-icon">+</span>
        </router-link>
        <router-link to="/edit-profile" class="profile-section">
          <span>{{ user.parent_name }}</span>
          <img v-if="user.profile_image_url" :src="`http://localhost:8000/${user.profile_image_url}`" class="profile-icon">
          <div v-else class="parent-icon-default" v-html="icons.parent"></div>
        </router-link>
      </div>
    </aside>
    <main class="main-content">
      <div class="chat-area">
        <div class="chat-messages">
          <div v-if="currentMode === 'test_intro'" class="bot-message test-intro-card">
            <h2>سلام {{ user.parent_name }} عزیز</h2>
            <p>خیلی خوشحالیم که می‌خوای تست **{{ selectedTestCategory }}** رو برای **{{ selectedChild.name }}** شروع کنی.</p>
            <p>این تست‌ها بر اساس استانداردهای جهانی (مثل ASQ3) تنظیم شده‌اند. لطفا لینک‌های زیر را ببینید:</p>
            <p><a href="#" @click.prevent>لینک ۱ (ویدیو)</a><br><a href="#" @click.prevent>لینک ۲ (مقاله)</a></p>
            <p>اگه آماده هستی دکمه شروع رو بزن تا تست رو شروع کنیم.</p>
            <button @click="startTestNow" class="start-test-button">ثبت (شروع تست)</button>
          </div>
          <div v-else-if="currentMode === 'testing'" class="bot-message test-question-card">
            <p class="question-text">
              <span class="question-number">{{ lastBotMessage.question.order_index }} - </span> 
              {{ lastBotMessage.question.text }}
            </p>
            <div class="answer-options">
              <button @click="submitAnswer(lastBotMessage.session_id, 'C')" class="answer-button">
                {{ lastBotMessage.question.option_C }}
              </button>
              <button @click="submitAnswer(lastBotMessage.session_id, 'B')" class="answer-button">
                {{ lastBotMessage.question.option_B }}
              </button>
              <button @click="submitAnswer(lastBotMessage.session_id, 'A')" class="answer-button">
                {{ lastBotMessage.question.option_A }}
              </button>
            </div>
          </div>
          <div v-else-if="currentMode === 'test_results'" class="bot-message test-finished-card">
            <p>{{ lastBotMessage.message }}</p>
            <div class="test-actions">
              <button @click="resetFlow" class="action-button">شروع تست دیگر</button>
              <button @click="resetFlow" class="action-button primary">پیشنهاد بازی</button>
            </div>
          </div>
          <div v-else-if="currentMode === 'chat'" class="bot-message chat-response initial-message">
              <p v-if="lastBotMessage.response">{{ lastBotMessage.response }}</p>
              <div v-else>
                <p>برای شروع مکالمه، یک فرزند را از نوار کناری انتخاب کنید یا سوال خود را بپرسید.</p>
                <p>برای شروع تست‌های سنجش مهارت (ASQ3)، یکی از دسته‌بندی‌های زیر را انتخاب کنید.</p>
              </div>
          </div>
        </div>
      </div>
      <div class="categories-grid">
        <div class="category-card" v-for="cat in categories" :key="cat.title" @click="showTestIntro(cat)">
          <div v-html="cat.icon" class="category-icon"></div>
          <span class="category-title">{{ cat.title }}</span>
        </div>
      </div>
      <div class="chat-input-area" v-if="currentMode === 'chat'">
        <div class="chat-box">
          <span class="mic-icon">🎤</span>
          <input 
            type="text" 
            v-model="chatMessage" 
            placeholder="پیام خود را بنویسید..."
            @keyup.enter="sendChatMessage()">
          <span class="send-icon" @click="sendChatMessage()">➤</span>
        </div>
        <span class="chat-target">{{ chatPlaceholderTarget }}</span>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'DashboardPage',
  data() {
    return {
      user: { parent_name: 'در حال بارگذاری...' },
      children: [],
      selectedChild: null,
      activeMenu: null,
      chatMessage: '',
      currentMode: 'chat', 
      selectedTestCategory: null,
      lastBotMessage: { 
          type: 'chat_message', 
          response: null,
          session_id: null, 
          question: null,
          message: null 
      },
      categories: [
        { title: 'مهارت های حرکتی درشت', icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm0 8v5m-3-5 3 5 3-5m-6 5h6"/></svg>` },
        { title: 'مهارت های حرکتی ریز', icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line></svg>` },
        { title: 'حل مسئله', icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.32 0L12 2.69z"></path><line x1="12" y1="22" x2="12" y2="18"></line><line x1="12" y1="8" x2="12" y2="12"></line></svg>` },
        { title: 'ارتباطات', icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>` },
        { title: 'شخصی - اجتماعی', icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>` },
      ],
      icons: {
        boy: `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`,
        girl: `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><path d="M20 8v6"></path><path d="M23 11h-6"></path></svg>`,
        parent: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`
      }
    };
  },
  computed: {
    chatPlaceholderTarget() {
      if (this.selectedChild) {
        return `مکالمه در مورد: ${this.selectedChild.name}`;
      }
      return "مکالمه عمومی";
    }
  },
  methods: {
    selectChild(child) {
      this.selectedChild = child;
      this.activeMenu = null;
      this.resetFlow();
      this.sendChatMessage(`سلام! می‌خوام درباره ${child.name} صحبت کنم.`, true);
    },
    
    resetFlow() {
        this.currentMode = 'chat';
        this.selectedTestCategory = null;
        this.lastBotMessage = { type: 'chat_message', response: null };
    },

    showTestIntro(category) {
      if (!this.selectedChild) {
        alert("لطفا ابتدا یک فرزند را از نوار کناری انتخاب کنید تا تست برای او شروع شود.");
        return;
      }
      this.currentMode = 'test_intro';
      this.selectedTestCategory = category.title;
    },
    
    async startTestNow() {
      const payload = {
        phone_number: localStorage.getItem('loggedInUserPhone'),
        message: `/start_test_now ${this.selectedTestCategory}`, 
        child_id: this.selectedChild.id,
      };
      
      try {
        const response = await axios.post('http://localhost:8000/chat', payload);
        const data = response.data;
        
        if (data.type === 'start_test' && data.question) {
            this.currentMode = 'testing';
            this.lastBotMessage = {
                type: 'current_question',
                session_id: data.session_id,
                question: data.question
            };
        } else {
            alert(data.response || "خطا در شروع تست. شاید تست مناسب سن فرزند شما موجود نباشد.");
            this.resetFlow();
        }
      } catch (error) {
        alert('خطا در شروع تست. لطفا دوباره تلاش کنید.');
        this.resetFlow();
      }
    },
    
    async submitAnswer(sessionId, choice) {
      const payload = {
        session_id: sessionId,
        answer_choice: choice,
      };
      
      try {
        const response = await axios.post('http://localhost:8000/tests/answer', payload);
        const data = response.data;
        
        if (data.is_last_question) {
            this.currentMode = 'test_results';
            this.lastBotMessage = {
                type: 'test_finished',
                message: data.final_result_message,
                response: data.final_result_message
            };
        } else if (data.question) {
            this.lastBotMessage = {
                type: 'current_question',
                session_id: data.session_id,
                question: data.question
            };
        }
      } catch (error) {
        alert(error.response?.data?.detail || 'خطا در ثبت پاسخ.');
        this.resetFlow();
      }
    },
    
    async sendChatMessage(messageContent = null, isSilent = false) {
      const finalMessage = messageContent || this.chatMessage.trim();
      if (!finalMessage) return;
    
      if (!messageContent) {
          this.chatMessage = ''; 
      }
      
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      const payload = {
        phone_number: phoneNumber,
        message: finalMessage,
        child_id: this.selectedChild ? this.selectedChild.id : null,
      };
      
      try {
        const response = await axios.post('http://localhost:8000/chat', payload);
        const data = response.data;
        
        if (data.type === 'chat_message') {
            this.lastBotMessage = data;
        } 
        
        if (!isSilent) {
             console.log("پاسخ چت‌بات:", data.response);
        }
        
        await this.fetchUserData(); 
      } catch (error) {
        alert('خطا در ارسال پیام.');
      }
    },
    
    async fetchUserData() {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      if (!phoneNumber) { this.$router.push('/'); return; }
      try {
        const response = await axios.get(`http://localhost:8000/me/${phoneNumber}`);
        this.user = response.data;
        this.children = response.data.children;
        if (this.children.length > 0 && !this.selectedChild) {
          this.selectChild(this.children[0]);
        }
      } catch (error) {
        localStorage.removeItem('loggedInUserPhone');
        this.$router.push('/');
      }
    },
    
    toggleMenu(childId) {
      this.activeMenu = this.activeMenu === childId ? null : childId;
    },
    editChild(child) {
      if (child.has_conversation_started) {
        alert("امکان ویرایش اطلاعات فرزندی که مکالمه‌ای درباره او شروع شده، وجود ندارد.");
        return;
      }
      this.$router.push({ name: 'EditChild', params: { childId: child.id } });
      this.activeMenu = null;
    },
    async deleteChild(childId) {
      if (confirm("آیا از حذف این فرزند مطمئن هستید؟")) {
        try {
          await axios.delete(`http://localhost:8000/children/${childId}`);
          if (this.selectedChild && this.selectedChild.id === childId) {
              this.selectedChild = null;
              this.resetFlow();
          }
          await this.fetchUserData(); 
        } catch (error) {
          alert("خطا در حذف فرزند.");
        }
      }
      this.activeMenu = null;
    },
  },
  mounted() {
    this.fetchUserData();
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;700&display=swap');

.dashboard-wrapper {
  display: flex; direction: rtl; font-family: 'IBM Plex Sans Arabic', sans-serif;
  height: 100vh; width: 100vw;
  background-image: url('@/assets/background.svg'); background-size: cover;
  overflow: hidden;
}
.sidebar {
  width: 280px; background-color: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px);
  display: flex; flex-direction: column; padding: 20px;
  border-left: 1px solid rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}
.sidebar-header { display: flex; align-items: center; gap: 10px; margin-bottom: 40px; }
.logo { width: 40px; }
.children-list { flex-grow: 1; }
.child-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 15px; margin-bottom: 10px; border-radius: 12px;
  cursor: pointer; transition: all 0.3s;
  border: 1px solid transparent;
}
.child-item:not(.active):hover {
  background-color: #f0e6ff;
  border-color: #d1b3ff;
}
.child-item.active {
  background-color: #f0e6ff; color: #6A1B9A; font-weight: bold;
  border: 1px solid #d1b3ff;
}
.child-info { display: flex; align-items: center; gap: 12px; }
.child-icon-wrapper {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
}
.child-icon-wrapper :deep(svg) { width: 100%; height: 100%; color: #333; }
.child-item.active .child-icon-wrapper :deep(svg) { color: #6A1B9A; }

.options-menu { position: relative; }
.options-icon { font-size: 1.5rem; color: #888; padding: 0 5px; border-radius: 5px; user-select: none; }
.options-icon:hover { background-color: rgba(0,0,0,0.1); }
.dropdown-menu {
  position: absolute; left: 20px; top: 20px; background: white;
  border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  z-index: 10; width: 100px; overflow: hidden;
}
.dropdown-menu a { display: block; padding: 8px 12px; text-decoration: none; color: #333; font-size: 0.9rem; }
.dropdown-menu a:hover { background-color: #f5f5f5; }
.dropdown-menu a.delete { color: #c0392b; }

.sidebar-footer { border-top: 1px solid rgba(0,0,0,0.08); padding-top: 20px; }
.add-child-btn, .profile-section {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 15px; text-decoration: none; color: inherit; border-radius: 10px;
}
.add-child-btn:hover, .profile-section:hover { background-color: rgba(255,255,255,0.5); }
.add-child-btn { width: 100%; background: none; border: none; font-family: inherit; font-size: 1rem; margin-bottom: 10px; cursor: pointer; }
.plus-icon { font-size: 1.5rem; font-weight: bold; }
.profile-icon, .parent-icon-default {
  width: 32px; height: 32px; border-radius: 50%; object-fit: cover;
  border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.2);
}
.parent-icon-default {
  background: #f0e6ff; display: flex; align-items: center;
  justify-content: center; padding: 4px;
}
.parent-icon-default :deep(svg) { color: #6A1B9A; }
.main-content {
  flex-grow: 1; padding: 40px 50px; display: flex;
  flex-direction: column; 
  justify-content: space-between; 
  align-items: center;
  position: relative; 
  overflow-y: auto; 
}
.chat-area {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-shrink: 0;
    flex-grow: 1; 
    padding-top: 50px;
    padding-bottom: 50px;
}

.chat-messages {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
}

.bot-message {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
    max-width: 80%;
    text-align: right;
    direction: rtl;
}
.initial-message {
    text-align: center;
    max-width: 400px;
}
.initial-message p {
    margin-bottom: 10px;
    font-size: 1rem;
    color: #555;
}
.test-intro-card { text-align: center; }
.test-intro-card h2 { color: #6A1B9A; margin-bottom: 15px; }
.test-intro-card p { margin-bottom: 15px; line-height: 1.6; }
.test-intro-card a { color: #6A1B9A; text-decoration: none; font-weight: bold; }

.test-intro-card .start-test-button {
    width: 100%; padding: 12px; background: #6A1B9A; color: white;
    border: none; border-radius: 10px; font-size: 1.1rem; cursor: pointer;
    margin-top: 15px; font-weight: bold; transition: background-color 0.3s;
}
.test-intro-card .start-test-button:hover { background-color: #4A148C; }
.test-question-card {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.question-text {
    font-size: 1.1rem;
    font-weight: bold;
    color: #333;
    margin-bottom: 25px;
}
.answer-options {
    display: flex;
    gap: 15px;
    justify-content: center;
    flex-wrap: wrap;
}
.answer-button {
    padding: 10px 20px;
    border: 2px solid #BA68C8;
    background-color: white;
    color: #6A1B9A;
    border-radius: 99px;
    cursor: pointer;
    font-weight: bold;
    min-width: 100px;
    transition: all 0.2s;
    font-family: inherit;
    font-size: 1rem;
}
.answer-button:hover {
    background-color: #f0e6ff;
    transform: translateY(-2px);
}
.categories-grid {
  display: flex; justify-content: center; align-items: center;
  gap: 30px; flex-wrap: wrap; width: 100%;
  max-width: 1200px; margin: 0 auto 30px auto; 
  flex-shrink: 0;
}
.category-card {
  background-color: rgba(255, 255, 255, 0.85);
  padding: 20px; border-radius: 20px; cursor: pointer;
  transition: all 0.3s ease; border: 2px solid transparent;
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 15px; width: 120px; height: 120px; 
  text-align: center;
}
.category-card:hover {
  transform: translateY(-5px); border: 2px solid #555;
  box-shadow: 0 10px 20px rgba(0,0,0,0.08);
}
.category-icon { width: 40px; height: 40px; color: #333; }
.category-icon :deep(svg) { width: 100%; height: 100%; }
.category-title { font-weight: bold; text-align: center; font-size: 0.85rem; }
.chat-input-area {
  width: 100%; max-width: 700px;
  margin: 0 auto 20px auto;
  position: relative; 
  flex-shrink: 0;
}
.chat-box {
  display: flex; align-items: center; background: #fff;
  padding: 8px 20px; border-radius: 99px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);
  border: 1px solid #eee;
}
.chat-box input {
  flex-grow: 1; border: none; outline: none;
  font-family: inherit; font-size: 1rem; text-align: right; padding: 8px;
}
.send-icon, .mic-icon { font-size: 1.5rem; cursor: pointer; color: #555; transition: color 0.2s; }
.send-icon:hover, .mic-icon:hover { color: #6A1B9A; }
.send-icon { transform: rotate(180deg); }
.mic-icon { margin-left: 15px; }

.chat-target {
    position: absolute;
    bottom: -25px;
    right: 20px;
    font-size: 0.8rem;
    color: #888;
}
</style>