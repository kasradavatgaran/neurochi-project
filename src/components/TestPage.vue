<template>
  <div class="page-wrapper">
    <aside class="sidebar desktop-only">
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
        <router-link to="/dashboard" class="mobile-back-btn">✕ خروج</router-link>
        <span class="mobile-title">تست {{ skillCategory }}</span>
        <div style="width: 40px"></div> 
      </div>

      <div class="scrollable-content" ref="chatArea">
        
        <div v-if="isLoading" class="state-container">
          <div class="loading-spinner"></div>
          <p>در حال آماده‌سازی تست...</p>
        </div>
        
        <div v-if="currentQuestion && !testResult" class="test-container">
          <div class="navigation-header" v-if="currentQuestion.order_index > 1">
            <button @click="goToPreviousQuestion" class="prev-button" :disabled="isSubmitting">
                <span class="arrow">➜</span> سوال قبل
            </button>
          </div>

          <img v-if="currentQuestion.image_url" :src="`/${currentQuestion.image_url}`" alt="Test Image" class="test-image">
          <div class="question-bubble">{{ currentQuestion.text }}</div>
          <div class="answer-options">
              <button class="option-btn option-no" @click="submitAnswer('C')" :disabled="isSubmitting">هنوز نه</button>
              <button class="option-btn option-sometimes" @click="submitAnswer('B')" :disabled="isSubmitting">گاهی</button>
              <button class="option-btn option-yes" @click="submitAnswer('A')" :disabled="isSubmitting">بله</button>
          </div>
        </div>
        <div v-if="testResult" class="final-result-container">
          <h1 class="result-title">{{ testResult.title }}</h1>
          <p class="result-status">
            وضعیت: <span :class="`status-text-${testResult.status_color}`">{{ testResult.status }}</span>
          </p>
          <p class="result-suggestion">{{ testResult.suggestion }}</p>
          <div class="result-actions">
            <router-link to="/dashboard" class="action-link">بازگشت به داشبورد</router-link>
            <button
              v-if="testResult.needs_games"
              @click="navigateToGames"
              class="action-link primary"
            >
              شروع بازی‌های سرگرم‌کننده
            </button>
          </div>
        </div>

        <div v-if="conversation.length > 0" class="chat-messages-container">
            <div class="divider"><span>گفتگو با هوش مصنوعی</span></div>
            
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

        <div class="spacer"></div>

      </div>

      <div class="chat-input-wrapper">
          <ChatInput 
            :is-active="true"
            :is-submitting="isSubmitting"
            placeholder="سوالی دارید؟ بپرسید..."
            @send-text="handleSendText"
            @send-audio="handleSendAudio"
          />
      </div>

    </main>
  </div>
</template>


<script>
import axios from 'axios';
import ChatInput from './ChatInput.vue';

export default {
  name: 'TestPage',
  components: { ChatInput },
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
      sessionId: null,
      currentQuestion: null,
      testResult: null,
      conversation: [],
      audioPlayer: new Audio(),
      isAudioPlaying: false,
    };
  },
  methods: {
    scrollToBottom() {
      this.$nextTick(() => {
        const chatArea = this.$refs.chatArea;
        if (chatArea) {
          chatArea.scrollTop = chatArea.scrollHeight;
        }
      });
    },

    addMessageToConversation(role, content, id = null, isLoading = false) {
      const messageId = id || (Date.now() + Math.random().toString(36).substr(2, 9));
      this.conversation.push({ id: messageId, role, content, isLoading });
      this.scrollToBottom();
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

    async handleSendText(message) {
      if (!message || this.isSubmitting) return;
      this.addMessageToConversation('user', message);
      await this.getBotResponse(message);
    },

    async getBotResponse(userMessage) {
        this.isSubmitting = true;
        const tempBotId = 'bot-' + Date.now();
        this.addMessageToConversation('assistant', '...', tempBotId, true);

        try {
            const payload = {
              phone_number: localStorage.getItem('loggedInUserPhone'),
              message: userMessage,
              child_id: parseInt(this.childId, 10),
            };
            const response = await axios.post('/chat', payload);
            
            if (response.data.type === 'chat_message' || response.data.response) {
                this.updateMessageById(tempBotId, response.data.response, false);
            } else {
                 this.updateMessageById(tempBotId, "متوجه شدم.", false);
            }
        } catch (error) {
            console.error("Error getting bot response:", error);
            this.updateMessageById(tempBotId, 'متاسفانه خطایی در ارتباط با سرور رخ داد.', false);
        } finally {
            this.isSubmitting = false;
        }
    },

    async handleSendAudio(blob) {
      if (this.isSubmitting) return;
      this.isSubmitting = true;
      const tempUserId = 'audio-user-' + Date.now();
      this.addMessageToConversation('user', '(در حال پردازش صدا...)', tempUserId, true);

      const formData = new FormData();
      formData.append('file', blob, 'recording.mp3');
      
      try {
        const phoneNumber = localStorage.getItem('loggedInUserPhone');
        const url = `/transcribe-audio?phone_number=${phoneNumber}&child_id=${this.childId}`;
        
        const response = await axios.post(url, formData);
        const transcribedText = response.data.transcribed_text;
        const botResponse = response.data.bot_response;
        
        this.updateMessageById(tempUserId, `(پیام صوتی): "${transcribedText}"`, false);
        this.addMessageToConversation('assistant', botResponse);

      } catch (error) {
        console.error('Error uploading audio:', error);
        this.updateMessageById(tempUserId, '(خطا در پردازش فایل صوتی)', false);
      } finally {
        this.isSubmitting = false;
      }
    },

    async fetchSidebarData() {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      if (!phoneNumber) { this.$router.push('/'); return; }
      try {
        const response = await axios.get(`/me/${phoneNumber}`);
        this.user = response.data;
        this.children = response.data.children;
      } catch (error) { this.$router.push('/'); }
    },
    
    async initializeTest() {
      this.isLoading = true;
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      const payload = {
        phone_number: phoneNumber,
        message: `/start_test_now ${this.skillCategory}`,
        child_id: parseInt(this.childId, 10),
      };
      try {
        const response = await axios.post('/chat', payload);
        const data = response.data;
        if (data.type === 'start_test' && data.question) {
          this.sessionId = data.session_id;
          this.currentQuestion = data.question;
        } else {
          alert(data.response || "تستی برای این کودک یافت نشد.");
          this.$router.push('/dashboard');
        }
      } catch (error) {
        alert("خطا در شروع تست.");
        this.$router.push('/dashboard');
      } finally {
        this.isLoading = false;
      }
    },
    
    async submitAnswer(choice) {
      if (this.isSubmitting) return;
      this.isSubmitting = true;
      const payload = { session_id: this.sessionId, answer_choice: choice };
      try {
        const response = await axios.post('/tests/answer', payload);
        const data = response.data;
        if (data.is_last_question) {
          this.testResult = data.final_result;
          this.currentQuestion = null;
        } else {
          this.currentQuestion = data.question;
        }
      } catch (error) {
        alert(error.response?.data?.detail || 'خطا در ثبت پاسخ.');
      } finally {
        this.isSubmitting = false;
      }
    },

    async goToPreviousQuestion() {
        if (this.isSubmitting) return;
        this.isSubmitting = true;
        try {
            const response = await axios.post('/tests/previous', {
                session_id: this.sessionId
            });
            this.currentQuestion = response.data;
        } catch (error) {
            console.error("Error going back:", error);
            if (error.response && error.response.status === 400) {
                alert("این اولین سوال است و نمی‌توانید به عقب برگردید.");
            } else {
                alert("خطا: امکان بازگشت وجود ندارد (سرور را بررسی کنید).");
            }
        } finally {
            this.isSubmitting = false;
        }
    },
    
    navigateToGames() {
      if (this.childId && this.skillCategory) {
        this.$router.push({
          name: 'GameSessionPage',
          params: { childId: this.childId, skillCategory: this.skillCategory }
        });
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
        this.isAudioPlaying = false;
      }
    }
  },
  async mounted() {
    await this.fetchSidebarData();
    await this.initializeTest();
  }
}
</script>

<style scoped>
.page-wrapper { display: flex; direction: rtl; font-family: 'IBM Plex Sans Arabic', sans-serif; height: 100vh; background-image: url('@/assets/background.svg'); background-size: cover; overflow: hidden; }

.sidebar { width: 280px; background-color: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); display: flex; flex-direction: column; padding: 20px; border-left: 1px solid rgba(255, 255, 255, 0.5); flex-shrink: 0; }
.sidebar-header { display: flex; align-items: center; gap: 10px; margin-bottom: 40px; }
.logo { width: 40px; }
.header-link { text-decoration: none; color: inherit; font-size: 1.2rem; font-weight: bold;}
.children-list { flex-grow: 1; overflow-y: auto; }
.child-item { padding: 12px 15px; margin-bottom: 10px; border-radius: 12px; }
.child-item.active { background-color: #f0e6ff; color: #6A1B9A; font-weight: bold; }
.sidebar-footer { border-top: 1px solid rgba(0,0,0,0.08); padding-top: 20px; }
.profile-section { display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; text-decoration: none; color: inherit; border-radius: 10px; }
.profile-icon { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; }

.main-content { flex-grow: 1; display: flex; flex-direction: column; height: 100vh; position: relative; width: 100%; }
.scrollable-content { 
  flex-grow: 1; 
  overflow-y: auto; 
  padding: 20px; 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  width: 100%; 
  box-sizing: border-box;
  -webkit-overflow-scrolling: touch;
}

.spacer { height: 100px; width: 100%; flex-shrink: 0; }

.chat-input-wrapper { 
    position: absolute; 
    bottom: 0; 
    left: 0; 
    right: 0; 
    padding: 15px 20px; 
    background: linear-gradient(to top, rgba(255,255,255,0.95) 80%, rgba(255,255,255,0)); 
    z-index: 10; 
}
.state-container { text-align: center; margin-top: 50px; color: #666; }
.loading-spinner { 
  border: 4px solid #f3f3f3; border-top: 4px solid #6A1B9A; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; 
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.test-container { width: 100%; max-width: 600px; text-align: center; margin-bottom: 30px; position: relative; }
.navigation-header { width: 100%; display: flex; justify-content: flex-start; margin-bottom: 15px; }
.prev-button { 
    background: rgba(255, 255, 255, 0.8); border: 1px solid #6A1B9A; color: #6A1B9A; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-family: inherit; font-size: 0.9rem; transition: all 0.2s; display: flex; align-items: center; gap: 8px; 
}
.test-image { max-width: 100%; max-height: 300px; border-radius: 20px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); object-fit: contain; }
.question-bubble { background: #fff; padding: 20px 25px; border-radius: 20px; font-size: 1.1rem; box-shadow: 0 5px 15px rgba(0,0,0,0.07); margin-bottom: 25px; line-height: 1.6; font-weight: bold; color: #333; }

.answer-options { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
.option-btn { 
  padding: 12px 30px; border: none; color: white; border-radius: 99px; font-size: 1rem; font-family: inherit; font-weight: bold; cursor: pointer; transition: transform 0.1s; min-width: 100px; flex: 1; max-width: 150px;
}
.option-yes { background-color: #4CAF50; }
.option-sometimes { background-color: #FF9800; }
.option-no { background-color: #F44336; }
.option-btn:active { transform: scale(0.95); }
.option-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.final-result-container { text-align: center; max-width: 700px; color: #333; margin-bottom: 30px; background: rgba(255,255,255,0.9); padding: 30px; border-radius: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); }
.result-title { font-size: 1.8rem; font-weight: 700; margin-bottom: 10px; color: #6A1B9A; }
.result-actions { display: flex; flex-direction: column; gap: 10px; align-items: center; margin-top: 20px; }
.action-link { text-decoration: none; font-size: 1rem; font-weight: bold; color: #6A1B9A; padding: 12px 25px; border-radius: 10px; border: 1px solid #ddd; background: #fff; width: 100%; max-width: 250px; box-sizing: border-box; }
.action-link.primary { background-color: #6A1B9A; color: white; border: none; }

.chat-messages-container { width: 100%; max-width: 700px; margin-top: 10px; display: flex; flex-direction: column; gap: 10px; padding-bottom: 20px; }
.divider { display: flex; align-items: center; text-align: center; color: #888; font-size: 0.8rem; margin: 15px 0; }
.divider::before, .divider::after { content: ''; flex: 1; border-bottom: 1px solid #ddd; }
.divider span { padding: 0 10px; }
.message-bubble { padding: 12px 18px; border-radius: 18px; max-width: 85%; width: fit-content; line-height: 1.6; position: relative; box-shadow: 0 2px 6px rgba(0,0,0,0.05); font-size: 0.95rem; }
.user-message { background-color: #f0e6ff; align-self: flex-end; border-bottom-right-radius: 4px; }
.bot-message { background-color: #fff; align-self: flex-start; border-bottom-left-radius: 4px; }

.mobile-header { display: none; } 
@media (max-width: 768px) {
  .desktop-only { display: none; } 
  
  .main-content { padding: 0; }
  
  .mobile-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    padding: 10px 15px;
    background: #fff;
    border-bottom: 1px solid #eee;
    box-sizing: border-box;
    height: 50px;
    flex-shrink: 0;
  }
  .mobile-back-btn {
    text-decoration: none; color: #666; font-weight: bold; font-size: 0.9rem;
  }
  .mobile-title {
    font-weight: bold; color: #333; font-size: 1rem;
  }

  .scrollable-content {
    padding: 15px;
  }

  .test-image {
    max-height: 200px; 
  }

  .question-bubble {
    padding: 15px;
    font-size: 1rem;
    margin-bottom: 20px;
  }

  .answer-options {
    gap: 8px;
  }
  .option-btn {
    padding: 12px 15px;
    font-size: 0.95rem;
  }

  .chat-input-wrapper {
    padding: 10px 15px;
  }
  
  .spacer { height: 80px; }
}
</style>