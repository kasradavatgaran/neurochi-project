
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


<style scoped>
.game-page-wrapper { 
  display: grid; 
  grid-template-columns: 280px 1fr 300px;
  height: 100vh; 
  direction: rtl; 
  font-family: 'IBM Plex Sans Arabic', sans-serif; 
  background-image: url('@/assets/background.svg'); 
  background-size: cover; 
  overflow: hidden;
}

.sidebar { 
  background-color: rgba(255, 255, 255, 0.7); 
  backdrop-filter: blur(10px); 
  padding: 20px; 
  display: flex; 
  flex-direction: column; 
  height: 100vh; 
  box-sizing: border-box; 
  overflow-y: auto;
}
.children-sidebar { border-left: 1px solid rgba(0,0,0,0.1); }
.games-sidebar { border-right: 1px solid rgba(0,0,0,0.1); }

.sidebar-header { display: flex; align-items: center; gap: 10px; margin-bottom: 40px; }
.logo { width: 40px; }
.header-link { text-decoration: none; color: inherit; font-size: 1.2rem; font-weight: bold;}
.children-list, .games-list { flex-grow: 1; overflow-y: auto; }
.child-item { padding: 12px 15px; margin-bottom: 10px; border-radius: 12px; }
.child-item.active { background-color: #f0e6ff; color: #6A1B9A; font-weight: bold; }
.sidebar-footer { border-top: 1px solid rgba(0,0,0,0.08); padding-top: 20px; }
.profile-section { display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; text-decoration: none; color: inherit; border-radius: 10px; }
.profile-icon { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; }

.game-item { display: flex; align-items: center; padding: 10px; margin-bottom: 10px; border-radius: 12px; transition: all 0.2s; border: 1px solid transparent; }
.game-item.active { background-color: #f0e6ff; border-color: #d1b3ff; transform: scale(1.02); box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.game-item.completed { opacity: 0.6; background-color: #e8f5e9; }
.game-thumbnail { width: 50px; height: 50px; border-radius: 8px; object-fit: cover; margin-left: 10px; flex-shrink: 0; }
.game-title { font-size: 0.9rem; font-weight: bold; }
.status-icon { margin-right: auto; font-size: 1rem; }

.main-content { 
  display: flex; flex-direction: column; height: 100vh; position: relative; width: 100%; 
}
.mobile-header { display: none; }

.chat-area { 
  flex-grow: 1; 
  overflow-y: auto; 
  padding: 20px; 
  display: flex; 
  flex-direction: column; 
  gap: 20px; 
  -webkit-overflow-scrolling: touch;
}
.spacer { height: 100px; width: 100%; flex-shrink: 0; }

.message-container { display: flex; flex-direction: column; width: 100%; }
.message-bubble { 
  padding: 20px 25px; border-radius: 20px; max-width: 80%; width: fit-content; 
  box-shadow: 0 3px 10px rgba(0,0,0,0.05); line-height: 1.7; position: relative;
}

.system-bubble { background-color: #fff3e0; align-self: center; text-align: center; font-size: 0.95rem; border: 1px solid #ffe0b2; }
.game-bubble { background-color: #fff; align-self: center; max-width: 90%; border: 1px solid #f3e5f5; }
.game-bubble h3 { color: #6A1B9A; margin-top: 0; border-bottom: 1px solid #f3e5f5; padding-bottom: 10px; margin-bottom: 10px; }
.analysis-bubble { background-color: #e3f2fd; align-self: center; max-width: 90%; }
.user-bubble { background-color: #f0e6ff; align-self: flex-end; border-bottom-right-radius: 4px; }
.bot-bubble { background-color: #fff; align-self: flex-start; border-bottom-left-radius: 4px; }

.game-answer-buttons { 
  display: flex; gap: 15px; margin-top: 20px; justify-content: center; flex-wrap: wrap;
}
.answer-btn { 
  padding: 12px 25px; border: none; border-radius: 12px; font-size: 1rem; cursor: pointer; 
  font-family: inherit; font-weight: bold; flex: 1; min-width: 120px; max-width: 200px; 
  transition: transform 0.1s; color: white;
}
.btn-no { background-color: #ef5350; }
.btn-yes { background-color: #66bb6a; }
.answer-btn:active { transform: scale(0.95); }
.answer-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.final-back-button { 
  display: inline-block; margin-top: 15px; background-color: #6A1B9A; color: white; 
  padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold;
}

.chat-input-wrapper { 
  position: absolute; bottom: 0; left: 0; right: 0; padding: 15px 20px; 
  background: linear-gradient(to top, rgba(255,255,255,0.95) 80%, rgba(255,255,255,0)); z-index: 10; 
}
.chat-box { display: flex; align-items: center; background: #fff; padding: 8px 15px; border-radius: 99px; box-shadow: 0 5px 25px rgba(0,0,0,0.1); border: 1px solid #eee; }
.chat-box input { flex-grow: 1; border: none; outline: none; background: transparent; font-size: 1rem; text-align: right; padding: 8px; }
.send-icon, .mic-icon { font-size: 1.4rem; color: #999; cursor: pointer; padding: 5px; }
.send-icon { transform: rotate(180deg); color: #6A1B9A; }
.mic-button { background: none; border: none; padding: 0 5px; font-size: 1.4rem; cursor: pointer; }

.locked-overlay { 
  position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
  background-color: rgba(255, 255, 255, 0.9); backdrop-filter: blur(5px); 
  z-index: 200; display: flex; justify-content: center; align-items: center; padding: 20px; box-sizing: border-box;
}
.locked-card { 
  background: white; padding: 40px; border-radius: 30px; text-align: center; 
  box-shadow: 0 20px 60px rgba(106, 27, 154, 0.15); max-width: 500px; width: 100%; 
  border: 1px solid rgba(106, 27, 154, 0.1); 
}
.lock-icon-large { font-size: 4rem; margin-bottom: 20px; }
.back-btn { 
  display: inline-block; background: #6A1B9A; color: white; padding: 12px 30px; 
  border-radius: 99px; text-decoration: none; font-weight: bold; margin-top: 20px; 
}

.typing-indicator span { height: 8px; width: 8px; background-color: #9b59b6; border-radius: 50%; display: inline-block; margin: 0 2px; animation: bounce 1.4s infinite ease-in-out both; }
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }

@media (max-width: 900px) {
  .game-page-wrapper {
    display: flex; 
    flex-direction: column;
  }

  .desktop-only { display: none !important; }

  .mobile-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    background: #fff;
    border-bottom: 1px solid #eee;
    height: 50px;
    flex-shrink: 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
  }
  .mobile-exit-btn { text-decoration: none; color: #666; font-weight: bold; font-size: 0.9rem; }
  .mobile-title { display: flex; flex-direction: column; align-items: center; line-height: 1.2; }
  .child-name-mobile { font-weight: bold; font-size: 0.9rem; color: #333; }
  .category-mobile { font-size: 0.75rem; color: #888; }

  .chat-area {
    padding: 15px;
  }

  .message-bubble {
    max-width: 90%; 
    padding: 15px;
    font-size: 0.95rem;
  }

  .game-answer-buttons {
    gap: 10px;
  }
  .answer-btn {
    padding: 10px;
    font-size: 0.9rem;
  }

  .locked-card {
    padding: 25px;
  }
  .lock-icon-large { font-size: 3rem; }
  .locked-card h2 { font-size: 1.4rem; }
  
  .chat-input-wrapper {
    padding: 10px 15px;
  }
}
</style>