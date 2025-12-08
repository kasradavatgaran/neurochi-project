<template>
  <div class="dashboard-wrapper">
    <div 
      class="sidebar-overlay" 
      :class="{ active: isSidebarOpen }" 
      @click="toggleSidebar"
    ></div>

    <aside class="sidebar" :class="{ open: isSidebarOpen }">
      <div class="sidebar-header">
        <img src="@/assets/logo.svg" alt="Nerochi Logo" class="logo">
        <router-link to="/dashboard" class="header-link">نوروچی</router-link>
        <span class="close-sidebar-btn" @click="toggleSidebar">✕</span>
      </div>
      
      <div class="children-list">
        <div 
          v-for="child in children" 
          :key="child.id" 
          class="child-item"
          :class="{ active: selectedChild && selectedChild.id === child.id }"
          @click="selectChild(child)">
          <div class="child-info">
            <span>{{ child.name }}</span>
          </div>
          <router-link 
            v-if="selectedChild && selectedChild.id === child.id"
            :to="{ name: 'GrowthChartPage', params: { childId: child.id } }" 
            class="growth-chart-link">
            نمودار رشد
          </router-link>
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
        <router-link to="/add-child" class="add-child-btn" @click="isSidebarOpen = false">
          <span>اضافه کردن فرزند</span>
          <span class="plus-icon">+</span>
        </router-link>
        <router-link to="/edit-profile" class="profile-section" @click="isSidebarOpen = false">
          <span>{{ user.parent_name }}</span>
          <img v-if="user.profile_image_url" :src="`/${user.profile_image_url}`" class="profile-icon">
        </router-link>
      </div>
    </aside>
    
    <main class="main-content">
      <div class="mobile-header">
        <button class="hamburger-btn" @click="toggleSidebar">☰</button>
        <div class="mobile-logo-area">
          <img src="@/assets/logo.svg" alt="Nerochi" class="mobile-logo">
          <span v-if="selectedChild" class="mobile-child-name">{{ selectedChild.name }}</span>
          <span v-else class="mobile-app-name">نوروچی</span>
        </div>
        <div class="mobile-header-spacer"></div>
      </div>
      <div class="chat-area" ref="chatArea">
        <div v-if="conversation.length === 0" class="initial-message">
          <p>برای شروع مکالمه، یک فرزند را از نوار کناری انتخاب کنید.</p>
          <p class="desktop-hint">فرزند مورد نظر را انتخاب کرده و سپس یکی از دسته‌بندی‌های زیر را انتخاب کنید.</p>
        </div>

        <div v-for="msg in conversation" :key="msg.id" class="message-bubble" :class="msg.role === 'user' ? 'user-message' : 'bot-message'">
          <p v-if="!msg.isLoading" v-html="msg.content.replace(/\n/g, '<br>')"></p>
          <div v-else class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
          <button 
            v-if="msg.role === 'assistant' && !msg.isLoading" 
            @click="playAudio(msg.content)" 
            class="play-audio-btn"
            :disabled="isAudioPlaying"
          >
            🔊
          </button>
        </div>
      </div>
      <div class="categories-grid" v-if="!isSubmitting && conversation.length < 3">
        <div class="category-card" v-for="cat in categories" :key="cat.title" @click="navigateToTest(cat)">
          <span class="category-title">{{ cat.title }}</span>
        </div>
      </div>
      <ChatInput 
        :is-active="!!selectedChild"
        :is-submitting="isSubmitting"
        placeholder="پیام خود را بنویسید..."
        @send-text="handleSendText"
        @send-audio="handleSendAudio"
      />
    </main>
  </div>
</template>


<script>
import axios from 'axios';
import ChatInput from './ChatInput.vue';

export default {
  name: 'DashboardPage',
  components: { ChatInput },
  data() {
    return {
      user: {},
      children: [],
      selectedChild: null,
      activeMenu: null,
      conversation: [],
      isSubmitting: false,
      audioPlayer: new Audio(),
      isAudioPlaying: false,
      isSidebarOpen: false,
      categories: [
        { title: 'مهارت های حرکتی درشت' },
        { title: 'مهارت های حرکتی ریز' },
        { title: 'حل مسئله' },
        { title: 'ارتباطات' },
        { title: 'شخصی - اجتماعی' },
      ],
    };
  },
  methods: {
    scrollToBottom() {
      this.$nextTick(() => {
        const chatArea = this.$refs.chatArea;
        if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
      });
    },
    addMessageToConversation(role, content, id = null, isLoading = false) {
      const messageId = id || (Date.now() + Math.random().toString(36).substr(2, 9));
      this.conversation.push({ id: messageId, role, content, isLoading });
      this.scrollToBottom();
    },
    
    toggleSidebar() {
  this.isSidebarOpen = !this.isSidebarOpen;
},
    updateMessageById(id, newContent, newIsLoadingState = false) {
      const messageIndex = this.conversation.findIndex(msg => msg.id === id);
      if (messageIndex !== -1) {
        this.conversation[messageIndex].content = newContent;
        this.conversation[messageIndex].isLoading = newIsLoadingState;
        this.$forceUpdate(); 
      }
      this.scrollToBottom();
    },
    async fetchUserData() {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      if (!phoneNumber) { this.$router.push('/'); return; }
      try {
        const response = await axios.get(`/me/${phoneNumber}`);
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

    async selectChild(child) {
  if (this.selectedChild?.id === child.id) {
      this.isSidebarOpen = false;
      return;
  }
  this.selectedChild = child;
  this.activeMenu = null;
  this.isSidebarOpen = false;
  
  this.conversation = [];
  this.isSubmitting = true;

  try {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      
      const response = await axios.get(`/chat/history/${phoneNumber}/${child.id}`);
      const history = response.data;

      if (history.length > 0) {
          this.conversation = history.map(msg => ({
              id: msg.id,
              role: msg.role,
              content: msg.content,
              isLoading: false
          }));
      } else {
          this.addMessageToConversation(
              'assistant', 
              `سلام! خوشحالم که در مورد ${child.name} گفتگو می‌کنیم. چطور می‌توانم امروز به شما کمک کنم؟ 😊`
          );
      }
      
      this.scrollToBottom();

  } catch (error) {
      console.error("Error fetching chat history:", error);
      this.addMessageToConversation(
          'assistant', 
          `سلام! خوشحالم که در مورد ${child.name} گفتگو می‌کنیم.`
      );
  } finally {
      this.isSubmitting = false;
  }
},

    async handleSendText(message) {
      if (!message || !this.selectedChild || this.isSubmitting) return;
      
      this.addMessageToConversation('user', message);
      
      await this.getBotResponse(message);
    },

    async handleSendAudio(blob) {
      if (!this.selectedChild || this.isSubmitting) return;
      
      this.isSubmitting = true;
      
      const tempUserId = 'audio-user-' + Date.now();
      this.addMessageToConversation('user', '(در حال پردازش صدا...)', tempUserId, true);
      
      const formData = new FormData();
      formData.append('file', blob, 'recording.mp3');
      
      try {
        const phoneNumber = localStorage.getItem('loggedInUserPhone');
        const url = `/transcribe-audio?phone_number=${phoneNumber}&child_id=${this.selectedChild.id}`;
        
        const response = await axios.post(url, formData);
        
        const transcribedText = response.data.transcribed_text;
        const botResponse = response.data.bot_response;
        
        this.updateMessageById(tempUserId, `(پیام صوتی): "${transcribedText}"`, false);
        
        this.addMessageToConversation('assistant', botResponse);

      } catch (error) {
        console.error('Error processing audio:', error);
        this.updateMessageById(tempUserId, '(خطا در پردازش فایل صوتی)', false);
      } finally {
        this.isSubmitting = false;
      }
    },
    
    async getBotResponse(userMessage) {
        this.isSubmitting = true;
        const tempBotId = 'bot-' + Date.now();
        this.addMessageToConversation('assistant', '...', tempBotId, true);

        try {
            const payload = {
              phone_number: localStorage.getItem('loggedInUserPhone'),
              message: userMessage,
              child_id: this.selectedChild.id,
            };
            const response = await axios.post('/chat', payload);
            
            this.updateMessageById(tempBotId, response.data.response, false);
        } catch (error) {
            console.error("Error getting bot response:", error);
            this.updateMessageById(tempBotId, 'متاسفانه خطایی در ارتباط با سرور رخ داد.', false);
        } finally {
            this.isSubmitting = false;
        }
    },
    async playAudio(text) {
        if (this.isAudioPlaying) {
            this.audioPlayer.pause();
            this.isAudioPlaying = false;
            return;
        }
        this.isAudioPlaying = true;
        try {
            const response = await axios.post('/text-to-speech', { text });
            const audioUrl = `${response.data.audio_url}`;
            this.audioPlayer.src = audioUrl;
            this.audioPlayer.play();
            this.audioPlayer.onended = () => { this.isAudioPlaying = false; };
        } catch (error) {
            console.error("Error playing audio:", error);
            alert("خطا در پخش صدا.");
            this.isAudioPlaying = false;
        }
    },
    navigateToTest(category) {
      if (!this.selectedChild) {
        alert("برای شروع تست، لطفا ابتدا یک فرزند را انتخاب کنید.");
        return;
      }
      this.$router.push({
        name: 'TestPage',
        params: { childId: this.selectedChild.id, skillCategory: category.title }
      });
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
          await axios.delete(`/children/${childId}`);
          if (this.selectedChild && this.selectedChild.id === childId) {
              this.selectedChild = null;
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
.dashboard-wrapper { 
  display: flex; 
  direction: rtl; 
  font-family: 'IBM Plex Sans Arabic', sans-serif; 
  height: 100vh; 
  background-image: url('@/assets/background.svg'); 
  background-size: cover; 
  overflow: hidden; 
  position: relative; 
}

.sidebar { 
  width: 280px; 
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(15px); 
  display: flex; 
  flex-direction: column; 
  padding: 20px; 
  border-left: 1px solid rgba(255, 255, 255, 0.6); 
  flex-shrink: 0; 
  z-index: 100;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-header { display: flex; align-items: center; gap: 10px; margin-bottom: 30px; }
.logo { width: 40px; }
.header-link { text-decoration: none; color: inherit; font-size: 1.2rem; font-weight: bold; }
.close-sidebar-btn { display: none; font-size: 1.5rem; cursor: pointer; margin-right: auto; }

.children-list { flex-grow: 1; overflow-y: auto; padding-left: 5px; } 
.child-item { 
  display: flex; flex-wrap: wrap; 
  justify-content: space-between; align-items: center; 
  padding: 12px 15px; margin-bottom: 10px; 
  border-radius: 12px; cursor: pointer; transition: all 0.2s; 
  border: 1px solid transparent; 
}
.child-item:not(.active):hover { background-color: rgba(240, 230, 255, 0.5); }
.child-item.active { background-color: #f0e6ff; color: #6A1B9A; font-weight: bold; border: 1px solid #d1b3ff; }

.child-info { display: flex; align-items: center; gap: 12px; flex-grow: 1; }

.options-menu { position: relative; }
.options-icon { font-size: 1.5rem; color: #888; padding: 0 8px; }
.dropdown-menu { 
  position: absolute; left: 0; top: 25px; 
  background: white; border-radius: 8px; 
  box-shadow: 0 4px 15px rgba(0,0,0,0.15); z-index: 10; 
  width: 110px; overflow: hidden; 
}
.dropdown-menu a { display: block; padding: 10px; text-decoration: none; color: #333; font-size: 0.9rem; }
.dropdown-menu a:hover { background-color: #f5f5f5; }
.dropdown-menu a.delete { color: #c0392b; }

.sidebar-footer { border-top: 1px solid rgba(0,0,0,0.1); padding-top: 15px; margin-top: 10px; }
.add-child-btn, .profile-section { 
  display: flex; justify-content: space-between; align-items: center; 
  padding: 12px; text-decoration: none; color: inherit; border-radius: 10px; 
  margin-bottom: 5px;
}
.add-child-btn:hover, .profile-section:hover { background-color: rgba(255,255,255,0.6); }
.plus-icon { font-size: 1.5rem; font-weight: bold; }
.profile-icon { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 2px solid white; }

.main-content { 
  flex-grow: 1; 
  padding: 30px 50px; 
  display: flex; 
  flex-direction: column; 
  justify-content: space-between; 
  align-items: center; 
  position: relative;
  width: 100%; 
}

.mobile-header { display: none; } 

.chat-area { 
  width: 100%; 
  display: flex; 
  flex-direction: column; 
  gap: 15px; 
  flex-grow: 1; 
  overflow-y: auto; 
  padding: 10px 5px; 
  -webkit-overflow-scrolling: touch; 
}

.initial-message { 
  align-self: center; text-align: center; max-width: 500px; margin-top: auto; margin-bottom: auto; color: #555;
}

.message-bubble { 
  padding: 15px 20px; border-radius: 20px; 
  max-width: 75%; width: fit-content; 
  line-height: 1.6; position: relative; 
  box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
  word-wrap: break-word;
}
.user-message { background-color: #f0e6ff; align-self: flex-end; border-bottom-right-radius: 4px; }
.bot-message { background-color: #fff; align-self: flex-start; border-bottom-left-radius: 4px; }

.play-audio-btn {
  background: none; border: none; cursor: pointer; font-size: 1.1rem;
  margin-top: 5px; display: block; opacity: 0.6;
}

.categories-grid { 
  display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; 
  width: 100%; max-width: 800px; margin: 10px auto; 
}
.category-card { 
  background-color: rgba(255, 255, 255, 0.9); padding: 10px 20px; 
  border-radius: 99px; cursor: pointer; transition: all 0.2s; 
  border: 1px solid #eee; font-size: 0.9rem; white-space: nowrap;
}
.category-card:hover { transform: translateY(-3px); border-color: #6A1B9A; color: #6A1B9A; }

.growth-chart-link {
  background-color: #e3d4f5; color: #6A1B9A; text-decoration: none;
  padding: 5px 12px; border-radius: 8px; font-size: 0.8rem;
  margin-right: auto; margin-left: 10px; white-space: nowrap;
}

.typing-indicator span {
  height: 6px; width: 6px; background-color: #9b59b6; border-radius: 50%; 
  display: inline-block; margin: 0 2px; animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }

@media (max-width: 768px) {
  .dashboard-wrapper {
    flex-direction: column; 
  }

  .sidebar {
    position: fixed;
    top: 0;
    right: 0;
    height: 100%;
    width: 80%; 
    max-width: 300px;
    transform: translateX(100%); 
    box-shadow: -5px 0 25px rgba(0,0,0,0.15);
    z-index: 1000;
  }
  .sidebar.open {
    transform: translateX(0); 
  }
  .close-sidebar-btn { display: block; } 

  .sidebar-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.4); z-index: 900;
    opacity: 0; visibility: hidden; transition: all 0.3s;
    backdrop-filter: blur(2px);
  }
  .sidebar-overlay.active { opacity: 1; visibility: visible; }

  .main-content {
    padding: 0; 
    width: 100%;
    height: 100%;
    padding-bottom: 10px; 
  }

  .mobile-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    padding: 10px 15px;
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(0,0,0,0.05);
    box-sizing: border-box;
    z-index: 50;
    height: 60px;
    flex-shrink: 0;
  }
  .hamburger-btn {
    background: none; border: none; font-size: 1.8rem; cursor: pointer; color: #555; padding: 0;
  }
  .mobile-logo-area {
    display: flex; align-items: center; gap: 8px; font-weight: bold; color: #333;
  }
  .mobile-logo { width: 30px; }
  .mobile-header-spacer { width: 24px; } 

  .chat-area {
    padding: 15px;
    width: 100%;
    box-sizing: border-box;
  }
  .message-bubble {
    max-width: 85%;
    padding: 12px 16px;
    font-size: 0.95rem;
  }
  
  .categories-grid {
    padding: 0 15px;
    margin-bottom: 10px;
    justify-content: flex-start; 
    overflow-x: auto; 
    flex-wrap: nowrap;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 10px; 
  }
  .category-card {
    flex-shrink: 0;
    font-size: 0.85rem;
    padding: 8px 16px;
  }
  
  .desktop-hint { display: none; }
}
.user-message {
  background-color: #f0e6ff;
  align-self: flex-start; 
  border-bottom-right-radius: 4px; 
  border-bottom-left-radius: 18px;
}

.bot-message {
  background-color: #fff;
  align-self: flex-end;
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 18px;
}
</style>