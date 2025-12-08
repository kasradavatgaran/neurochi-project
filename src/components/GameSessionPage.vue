
<template>
  <div v-if="isLocked" class="locked-overlay">
    <div class="locked-card">
      <div class="lock-icon-large">🔒</div>
      <h2>تمرینات هفتگی تکمیل شد!</h2>
      <p>{{ lockMessage }}</p>
      <p class="sub-text">استراحت و تکرار بازی‌های قبلی به تثبیت یادگیری کمک می‌کند.</p>
      <router-link to="/dashboard" class="back-btn">بازگشت به داشبورد</router-link>
    </div>
  </div>

  <div class="game-page-wrapper">
    <aside class="sidebar children-sidebar desktop-only">
       <div class="sidebar-header">
        <img src="@/assets/logo.svg" alt="Nerochi Logo" class="logo">
        <router-link to="/dashboard" class="header-link">نوروچی</router-link>
      </div>
       <div class="children-list">
        <div 
          v-for="child in children" 
          :key="child.id" 
          class="child-item"
          :class="{ active: child.id == childId }">
          <span>{{ child.name }}</span>
        </div>
      </div>
       <div class="sidebar-footer">
        <router-link to="/edit-profile" class="profile-section">
          <span>{{ user.parent_name }}</span>
          <img v-if="user.profile_image_url" :src="`/${user.profile_image_url}`" class="profile-icon">
        </router-link>
      </div>
    </aside>
    <main class="main-content">
      <div class="mobile-header">
        <router-link to="/dashboard" class="mobile-exit-btn">✕ خروج</router-link>
        <div class="mobile-title">
            <span class="child-name-mobile">{{ childName }}</span>
            <span class="category-mobile">{{ skillCategory }}</span>
        </div>
        <div style="width: 40px"></div> 
      </div>

      <div class="chat-area" ref="chatArea">
        <div v-for="(msg, index) in conversation" :key="index" class="message-container" :class="msg.type">
          
          <div v-if="msg.type === 'system-message'" class="message-bubble system-bubble">
            <p v-html="msg.content"></p>
          </div>
          <div v-else-if="msg.type === 'game-message'" class="message-bubble game-bubble">
            <div class="game-card-content">
                <h3>{{ msg.content.title }}</h3>
                <p>{{ msg.content.description }}</p>
            </div>
            <div v-if="msg.content.id === currentGame?.id" class="game-answer-buttons">
              <button class="answer-btn btn-no" @click="submitGameAnswer('cannot_do')" :disabled="isSubmitting">نمی‌تواند ❌</button>
              <button class="answer-btn btn-yes" @click="submitGameAnswer('can_do')" :disabled="isSubmitting">می‌تواند ✅</button>
            </div>
          </div>
          
          <div v-else-if="msg.type === 'analysis-message'" class="message-bubble analysis-bubble">
            <div v-if="isAnalysisLoading">
              <div class="typing-indicator"><span></span><span></span><span></span></div>
              <p class="loading-text">هوش مصنوعی در حال تحلیل...</p>
            </div>
            <div v-else>
              <h3>تحلیل نهایی نوروچی</h3>
              <p style="white-space: pre-wrap;">{{ msg.content }}</p>
              <router-link to="/dashboard" class="final-back-button">بازگشت به داشبورد</router-link>
            </div>
          </div>

          <div v-else-if="msg.type === 'user-message'" class="message-bubble user-bubble">
            <p>{{ msg.content }}</p>
          </div>

          <div v-else-if="msg.type === 'bot-message'" class="message-bubble bot-bubble">
            <p>{{ msg.content }}</p>
          </div>
        </div>
        
        <div class="spacer"></div>
      </div>
      <div class="chat-input-wrapper">
        <div class="chat-box" :class="{ disabled: !isChatActive || isSubmitting }">
          <button 
            @mousedown="startRecording"
            @mouseup="stopRecording"
            @touchstart.prevent="startRecording"
            @touchend.prevent="stopRecording"
            class="mic-button" 
            :disabled="!isChatActive || isSubmitting"
          >
            <span v-if="!isRecording">🎙️</span>
            <span v-else class="recording-indicator">🛑</span>
          </button>
          <input 
            type="text" 
            v-model="userMessage"
            placeholder="پیام..." 
            :disabled="!isChatActive || isSubmitting"
            @keyup.enter="sendUserMessage"
          >
          <span class="send-icon" @click="sendUserMessage">➤</span>
        </div>
      </div>
    </main>

    <aside class="sidebar games-sidebar desktop-only">
      <h2 class="sidebar-title">لیست بازی‌ها</h2>
      <div v-if="games.length > 0" class="games-list">
        <div 
          v-for="(game, index) in games" 
          :key="game.id" 
          class="game-item"
          :class="{ 
              active: index === completedGamesCount && !isSessionComplete, 
              completed: index < completedGamesCount 
          }"
        >
          <img :src="`/${game.image_url}`" class="game-thumbnail" alt="Game">
          <div class="game-info">
            <span class="game-title">{{ game.title }}</span>
          </div>
          <span v-if="index < completedGamesCount" class="status-icon">✅</span>
          <span v-else-if="index === completedGamesCount && !isSessionComplete" class="status-icon">▶️</span>
        </div>
      </div>
    </aside>
  </div>
</template>

<script>
import axios from 'axios';
import MicRecorder from 'mic-recorder-to-mp3';
export default {
  name: 'GameSessionPage',
  props: {
    childId: { type: [String, Number], required: true },
    skillCategory: { type: String, required: true }
  },
  data() {
    return {
    isLoading: true,
    isSubmitting: false,
    user: {},
    children: [],
    childName: '',
    games: [],
    conversation: [],
    completedGamesCount: 0,
    isSessionComplete: false,
    isAnalysisLoading: false,
    isChatActive: false,
    userMessage: '',
    recorder: null,
    isRecording: false,
    isLocked: false,
    lockMessage: '',
  };
  },
  computed: {
    currentGame() {
      return this.games.length > this.completedGamesCount ? this.games[this.completedGamesCount] : null;
    }
  },
  methods: {
    addMessage(type, content) {
      this.conversation.push({ type, content });
      this.scrollToBottom();
    },

    async fetchInitialData() {
  this.isLoading = true;
  const phoneNumber = localStorage.getItem('loggedInUserPhone');
  if (!phoneNumber) { this.$router.push('/'); return; }
  
  try {
    const userResponse = await axios.get(`/me/${phoneNumber}`);
    this.user = userResponse.data;
    this.children = userResponse.data.children;
    const currentChild = this.children.find(c => c.id == this.childId);
    if (currentChild) this.childName = currentChild.name;
    
    const gamesResponse = await axios.get(`/children/${this.childId}/suggested-games?skill_category=${this.skillCategory}`);
    const data = gamesResponse.data;

    if (data.status === 'locked') {
        this.isLocked = true;
        this.lockMessage = data.message;
    } else if (data.status === 'available' && data.games.length > 0) {
        this.games = data.games;
        this.isLocked = false;
        
        this.addMessage('system-message', `
          ${this.user.parent_name} عزیز،<br>
          ${this.childName} در مهارت «${this.skillCategory}» نیاز به تمرین دارد!<br>
          برای بهبود این مهارت، ۵ بازی منتخب برای این هفته آماده کرده‌ایم.
        `);
        this.showNextGame();
    } else {
        this.addMessage('system-message', 'متاسفانه در حال حاضر بازی پیشنهادی برای این مهارت یافت نشد.');
        this.isSessionComplete = true;
    }

  } catch (error) {
    console.error(error);
    alert("خطا در بارگذاری اطلاعات.");
    this.$router.push('/dashboard');
  } finally {
    this.isLoading = false;
  }
},

    showNextGame() {
        if (this.currentGame) {
            this.addMessage('game-message', {
                id: this.currentGame.id,
                title: this.currentGame.title,
                description: this.currentGame.description
            });
        }
    },

    async submitGameAnswer(response) {
      if (this.isSubmitting || !this.currentGame) return;
      this.isSubmitting = true;

      const payload = {
        child_id: parseInt(this.childId, 10),
        game_id: this.currentGame.id,
        response: response
      };
      
      try {
        await axios.post('/games/answer', payload);
        
        this.completedGamesCount++;
        
        if (this.completedGamesCount >= this.games.length) {
          this.isSessionComplete = true;
          await this.getFinalAnalysis();
        } else {
          this.showNextGame();
        }
      } catch (error) {
        alert("خطا در ثبت پاسخ بازی.");
      } finally {
        this.isSubmitting = false;
      }
    },
    
    async getFinalAnalysis() {
        this.isAnalysisLoading = true;
        this.addMessage('analysis-message', '');
        try {
            const response = await axios.get(`/children/${this.childId}/final-analysis?skill_category=${this.skillCategory}`);
            const lastMessageIndex = this.conversation.length - 1;
            this.conversation[lastMessageIndex].content = response.data.analysis;
            this.isChatActive = true; 
        } catch (error) {
            const lastMessageIndex = this.conversation.length - 1;
            this.conversation[lastMessageIndex].content = "متاسفانه در دریافت تحلیل نهایی خطایی رخ داد.";
        } finally {
            this.isAnalysisLoading = false;
            this.scrollToBottom();
        }
    },
    
    async sendUserMessage() {
      const message = this.userMessage.trim();
      if (!message || !this.isChatActive || this.isSubmitting) return;

      this.addMessage('user-message', message);
      this.userMessage = '';
      this.isSubmitting = true;

      try {
        const payload = {
          phone_number: localStorage.getItem('loggedInUserPhone'),
          message: message,
          child_id: parseInt(this.childId, 10),
        };
        const response = await axios.post('/chat', payload);
        this.addMessage('bot-message', response.data.response);
      } catch (error) {
        this.addMessage('bot-message', "متاسفانه در حال حاضر امکان پاسخگویی وجود ندارد.");
      } finally {
        this.isSubmitting = false;
      }
    },
    initializeRecorder() {
      this.recorder = new MicRecorder({ bitRate: 128 });
    },

    startRecording() {
      if (!this.recorder || this.isRecording || !this.isChatActive) return;
      
      this.recorder.start().then(() => {
        this.isRecording = true;
      }).catch((error) => {
        console.error('Error starting recording:', error);
        this.isRecording = false; 
        alert("لطفا دسترسی به میکروفون را فعال کنید.");
      });
    },

    stopRecording() {
      if (!this.recorder || !this.isRecording) return;
      
      this.recorder.stop().getMp3().then(async ([, blob]) => {
        this.isRecording = false; 
        
        if (blob.size < 1000) { 
          console.log("Recording too short, ignoring.");
          return;
        }

        const formData = new FormData();
        formData.append('file', blob, 'recording.mp3');
        
        this.isSubmitting = true;
        try {
            const phoneNumber = localStorage.getItem('loggedInUserPhone');
            const url = `/transcribe-audio?phone_number=${phoneNumber}&child_id=${this.childId}`;
            
            const response = await axios.post(url, formData);

            const transcribedText = response.data.transcribed_text;
            const botResponse = response.data.bot_response;
            
            this.addMessage('user-message', `(پیام صوتی): "${transcribedText}"`);
            this.addMessage('bot-message', botResponse);

        } catch (error) {
            console.error('Error uploading audio:', error.response || error);
            this.addMessage('system-message', 'خطا در پردازش فایل صوتی.');
        } finally {
            this.isSubmitting = false;
        }

      }).catch((e) => {
        console.error('Error stopping or getting mp3:', e);
        this.isRecording = false;
        this.isSubmitting = false;
      });
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const chatArea = this.$refs.chatArea;
        if (chatArea) {
          chatArea.scrollTop = chatArea.scrollHeight;
        }
      });
    }
  },
    
  
  mounted() {
    this.fetchInitialData();
    this.initializeRecorder(); 
  }
}
</script>
