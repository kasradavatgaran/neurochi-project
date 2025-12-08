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
