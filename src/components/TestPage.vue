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
          <img v-if="user.profile_image_url" :src="toApiUrl(user.profile_image_url)" class="profile-icon">
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
        
        <div v-if="preview && !hasStarted && !testResult" class="test-intro-card">
          <div class="intro-copy">{{ preview.intro }}</div>
          <div class="child-summary">
            <strong>{{ preview.child_name }}</strong>
            <span>سن: {{ preview.age_months }} ماه</span>
            <span>{{ preview.question_count }} پرسش متناسب با این سن</span>
          </div>
          <div v-if="preview.last_completed_at" class="previous-test-note">
            این تست در تاریخ {{ formatDate(preview.last_completed_at) }} توسط شما انجام شده است.
            پاسخ‌های قبلی نمایش داده می‌شوند و قابل ویرایش هستند.
          </div>
          <div v-if="preview.last_answers && preview.last_answers.length" class="previous-answers">
            <h3>پاسخ‌های ثبت‌شده</h3>
            <p v-for="answer in preview.last_answers" :key="answer.question_id">
              {{ answer.question }}: <b>{{ answer.choice_text || answer.choice }}</b>
            </p>
          </div>
          <button class="start-test-button" @click="beginTest(false)" :disabled="isSubmitting">
            {{ preview.last_completed_at ? 'ویرایش پاسخ‌های قبلی' : 'شروع تست' }}
          </button>
        </div>

        <div v-if="currentQuestion && hasStarted && !testResult" class="test-container">
          <div class="navigation-header">
            <button
              @click="goToPreviousQuestion"
              class="prev-button"
              :disabled="isSubmitting || currentQuestion.order_index <= (preview?.first_question_order || 1)"
            >
                <span class="arrow">➜</span> سوال قبل
            </button>
          </div>

           <img v-if="currentQuestion.image_url" :src="toApiUrl(currentQuestion.image_url)" @error="hideBrokenImage" alt="راهنمای تست" class="test-image">
           <div class="question-bubble">{{ currentQuestion.text }}</div>
           <div class="answer-options">
               <button :class="['option-btn', 'option-no', { selected: currentQuestion.selected_option === 'C' }]" @click="submitAnswer('C')" :disabled="isSubmitting">{{ currentQuestion.option_C }}</button>
               <button :class="['option-btn', 'option-sometimes', { selected: currentQuestion.selected_option === 'B' }]" @click="submitAnswer('B')" :disabled="isSubmitting">{{ currentQuestion.option_B }}</button>
               <button :class="['option-btn', 'option-yes', { selected: currentQuestion.selected_option === 'A' }]" @click="submitAnswer('A')" :disabled="isSubmitting">{{ currentQuestion.option_A }}</button>
          </div>
        </div>
        <div v-if="testResult" class="final-result-container">
          <h1 class="result-title">{{ testResult.title }}</h1>
          <p class="result-status">
            وضعیت: <span :class="`status-text-${testResult.status_color}`">{{ testResult.status }}</span>
          </p>
           <p class="result-suggestion">{{ testResult.suggestion }}</p>
           <p v-if="testResult.status_color === 'yellow'" class="status-guidance">چند روز با بازی‌های پیشنهادی تمرین کنید و سپس تست این حوزه را دوباره انجام دهید.</p>
           <p v-if="testResult.status_color === 'red'" class="status-guidance danger">برای بررسی دقیق‌تر، لطفاً با پزشک کودک مشورت کنید.</p>
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
            
            <div v-for="msg in conversation" :key="msg.id" class="message-bubble" :class="[msg.role === 'user' ? 'user-message' : 'bot-message', { 'thinking-bubble': msg.isLoading }]">
                <template v-if="msg.isLoading">
                  <div class="thinking-indicator" role="status" aria-label="می‌اندیشم">
                    <span class="thinking-text">می‌اندیشم..</span>
                  </div>
                </template>
                <template v-else>
                  <div class="rich-text" v-html="renderMessageHtml(msg)"></div>
                  <details v-if="showRagDebug && msg.debugInfo" class="rag-debug">
                    <summary>RAG Debug</summary>
                    <pre>{{ msg.debugInfo }}</pre>
                  </details>
                  <button
                      v-if="msg.role === 'assistant'"
                      @click="playAudio(msg.content)"
                      class="play-audio-btn"
                      :disabled="isAudioPlaying"
                  >
                      🔊
                  </button>
                </template>
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
import api, { toApiUrl as buildApiUrl } from '@/services/api';
import { renderMessage } from '@/utils/markdown';
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
      preview: null,
      hasStarted: false,
      currentQuestion: null,
      testResult: null,
      conversation: [],
      audioPlayer: new Audio(),
      isAudioPlaying: false,
      showRagDebug: false,
    };
  },
  methods: {
    toApiUrl(path) {
      return buildApiUrl(path);
    },
    formatDate(value) {
      return value ? new Date(value).toLocaleDateString('fa-IR') : '';
    },
    hideBrokenImage(event) {
      event.target.style.display = 'none';
    },
    stripHtml(text) {
      const container = document.createElement('div');
      container.innerHTML = text || '';
      return container.textContent || container.innerText || '';
    },
    buildTestContext() {
      const question = this.currentQuestion;
      const options = question ? [
        question.option_A ? `A: ${question.option_A}` : '',
        question.option_B ? `B: ${question.option_B}` : '',
        question.option_C ? `C: ${question.option_C}` : '',
      ].filter(Boolean).join(' | ') : '';
      return [
        'Page: child development screening test',
        `Skill category: ${this.skillCategory}`,
        this.preview?.child_name ? `Child: ${this.preview.child_name}` : '',
        this.preview?.age_months ? `Child age: ${this.preview.age_months} months` : '',
        question?.text ? `Current test question: ${question.text}` : '',
        options ? `Available options: ${options}` : '',
        question?.selected_option_text ? `Selected answer: ${question.selected_option_text}` : '',
        this.testResult?.status ? `Current test result status: ${this.testResult.status}` : '',
      ].filter(Boolean).join('\n');
    },
    renderMessageHtml(message) {
      return renderMessage(message?.content, message?.sources);
    },
    buildDebugInfo(data) {
      const sources = Array.isArray(data?.debug_sources) ? data.debug_sources : [];
      const prompt = String(data?.debug_prompt || '').trim();
      if (!sources.length && !prompt) {
        return '';
      }

      const sourceLines = sources.map((source, index) => (
        `${index + 1}. ${source.title || '-'} | ${source.url || source.reference_url || '-'} | ${source.source_file || '-'} | chunk ${source.chunk_index || '-'}`
      ));
      const parts = [];
      if (sourceLines.length) {
        parts.push('Sources:');
        parts.push(...sourceLines);
      }
      if (prompt) {
        parts.push('');
        parts.push('Prompt:');
        parts.push(prompt);
      }
      return parts.join('\n').trim();
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const chatArea = this.$refs.chatArea;
        if (chatArea) {
          chatArea.scrollTop = chatArea.scrollHeight;
        }
      });
    },

    addMessageToConversation(role, content, id = null, isLoading = false, sources = [], debugInfo = '') {
      const messageId = id || (Date.now() + Math.random().toString(36).substr(2, 9));
      this.conversation.push({ id: messageId, role, content, isLoading, sources, debugInfo });
      this.scrollToBottom();
    },

    updateMessageById(id, newContent, newIsLoadingState = false, newSources = [], newDebugInfo = '') {
      const messageIndex = this.conversation.findIndex(msg => msg.id === id);
      if (messageIndex !== -1) {
        this.conversation[messageIndex].content = newContent;
        this.conversation[messageIndex].isLoading = newIsLoadingState;
        this.conversation[messageIndex].sources = newSources;
        this.conversation[messageIndex].debugInfo = newDebugInfo;
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
              context: this.buildTestContext(),
            };
            const response = await api.post('/chat', payload);
            
            if (response.data.type === 'chat_message' || response.data.response) {
                this.updateMessageById(
                  tempBotId,
                  response.data.response,
                  false,
                  Array.isArray(response.data.sources) ? response.data.sources : [],
                  this.buildDebugInfo(response.data),
                );
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
        const url = `/transcribe-audio?phone_number=${encodeURIComponent(phoneNumber)}&child_id=${this.childId}&context=${encodeURIComponent(this.buildTestContext())}`;
        
        const response = await api.post(url, formData);
        const transcribedText = response.data.transcribed_text;
        const botResponse = response.data.bot_response;
        const sources = Array.isArray(response.data.sources) ? response.data.sources : [];
        const debugInfo = this.buildDebugInfo(response.data);

        this.updateMessageById(tempUserId, `(پیام صوتی): "${transcribedText}"`, false);
        this.addMessageToConversation('assistant', botResponse, null, false, sources, debugInfo);

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
        const response = await api.get(`/me/${phoneNumber}`);
        this.user = response.data;
        this.children = response.data.children;
      } catch (error) { this.$router.push('/'); }
    },
    
    async initializeTest() {
      this.isLoading = true;
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      try {
        const response = await api.get(`/children/${this.childId}/tests/${encodeURIComponent(this.skillCategory)}/preview`);
        this.preview = response.data;
      } catch (error) {
        alert(error.response?.data?.detail || "تستی برای این کودک یافت نشد.");
        this.$router.push('/dashboard');
      } finally {
        this.isLoading = false;
      }
    },

    async beginTest(newSession = false) {
      if (this.isSubmitting) return;
      this.isSubmitting = true;
      try {
        const response = await api.post(`/children/${this.childId}/tests/start`, {
          skill_category: this.skillCategory,
          new_session: newSession,
        });
        this.sessionId = response.data.session_id;
        this.currentQuestion = response.data.question;
        this.hasStarted = true;
      } catch (error) {
        alert(error.response?.data?.detail || 'خطا در آماده‌سازی تست.');
      } finally {
        this.isSubmitting = false;
      }
    },
    
    async submitAnswer(choice) {
      if (this.isSubmitting) return;
      this.isSubmitting = true;
      const payload = { session_id: this.sessionId, answer_choice: choice };
      try {
        const response = await api.post('/tests/answer', payload);
        const data = response.data;
        if (data.is_last_question) {
          this.testResult = data.final_result;
          this.currentQuestion = null;
          this.hasStarted = false;
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
            const response = await api.post('/tests/previous', {
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
        const response = await api.post('/text-to-speech', { text: this.stripHtml(text) });
        const audioUrl = buildApiUrl(response.data.audio_url);
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
:deep(.message-bubble strong) { font-weight: 800; }
:deep(.message-bubble h4) { margin: 14px 0 6px; color: #6a1b9a; font-size: 1.05em; }
:deep(.message-bubble ul) { margin: 8px 0; padding-right: 22px; }
:deep(.message-bubble li) { margin: 5px 0; }
:deep(.message-bubble a) { color: #0b57d0; text-decoration: underline; }
:deep(.message-bubble code) { background: #f3eef8; padding: 1px 5px; border-radius: 5px; }
</style>

<style scoped>
.page-wrapper { display: flex; direction: rtl; font-family: 'IBM Plex Sans Arabic', sans-serif; width: 100%; height: 100dvh; min-height: 100dvh; background-image: url('@/assets/background.svg'); background-size: cover; overflow: hidden; }

.sidebar { width: 280px; min-width: 0; min-height: 0; background-color: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); display: flex; flex-direction: column; padding: 20px; border-left: 1px solid rgba(255, 255, 255, 0.5); flex-shrink: 0; overflow: hidden; }
.sidebar-header { display: flex; align-items: center; gap: 10px; margin-bottom: 40px; }
.logo { width: 40px; }
.header-link { text-decoration: none; color: inherit; font-size: 1.2rem; font-weight: bold;}
.children-list { flex-grow: 1; min-height: 0; overflow-y: auto; overflow-x: hidden; -webkit-overflow-scrolling: touch; overscroll-behavior-y: contain; touch-action: pan-y; }
.child-item { padding: 12px 15px; margin-bottom: 10px; border-radius: 12px; }
.child-item.active { background-color: #f0e6ff; color: #6A1B9A; font-weight: bold; }
.sidebar-footer { border-top: 1px solid rgba(0,0,0,0.08); padding-top: 20px; }
.profile-section { display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; text-decoration: none; color: inherit; border-radius: 10px; }
.profile-icon { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; }

.main-content { flex-grow: 1; min-width: 0; min-height: 0; display: flex; flex-direction: column; height: 100dvh; position: relative; width: 100%; overflow: hidden; }
.scrollable-content { 
  flex-grow: 1; 
  min-width: 0;
  min-height: 0;
  overflow-y: auto; 
  padding: clamp(12px, 2vw, 24px); 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  width: 100%; 
  box-sizing: border-box;
  -webkit-overflow-scrolling: touch;
  overflow-x: hidden;
  overscroll-behavior-y: contain;
  touch-action: pan-y;
}

.spacer { height: 100px; width: 100%; flex-shrink: 0; }

.chat-input-wrapper { 
    position: absolute; 
    bottom: 0; 
    left: 0; 
    right: 0; 
    padding: 15px 20px calc(15px + env(safe-area-inset-bottom)); 
    background: linear-gradient(to top, rgba(255,255,255,0.95) 80%, rgba(255,255,255,0)); 
    z-index: 10; 
}
.state-container { text-align: center; margin-top: 50px; color: #666; }
.loading-spinner { 
  border: 4px solid #f3f3f3; border-top: 4px solid #6A1B9A; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; 
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.test-container { width: 100%; max-width: 600px; text-align: center; margin-bottom: 30px; position: relative; }
.test-intro-card {
  box-sizing: border-box;
  width: min(760px, 100%);
  background: rgba(255, 255, 255, 0.94);
  border-radius: 26px;
  padding: 28px;
  box-shadow: 0 12px 32px rgba(74, 53, 110, 0.12);
  line-height: 2;
  white-space: pre-line;
  text-align: right;
}
.child-summary { display: flex; gap: 14px; flex-wrap: wrap; margin: 20px 0; color: #5a5268; }
.previous-test-note { background: #fff7df; border-radius: 14px; padding: 12px 16px; margin: 12px 0; }
.previous-answers { max-height: 220px; overflow: auto; border-top: 1px solid #eee; margin-top: 16px; padding-top: 12px; font-size: .9rem; }
.start-test-button { border: 0; border-radius: 999px; background: #6a1b9a; color: #fff; padding: 13px 28px; font: inherit; cursor: pointer; }
.start-test-button:disabled { opacity: .55; cursor: wait; }
.navigation-header { width: 100%; display: flex; justify-content: flex-start; margin-bottom: 15px; }
.prev-button { 
    background: rgba(255, 255, 255, 0.8); border: 1px solid #6A1B9A; color: #6A1B9A; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-family: inherit; font-size: 0.9rem; transition: all 0.2s; display: flex; align-items: center; gap: 8px; 
}
.prev-button:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
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
.option-btn.selected { outline: 3px solid rgba(106, 27, 154, 0.25); transform: translateY(-2px); }

.final-result-container { box-sizing: border-box; width: min(700px, 100%); text-align: center; max-width: 700px; color: #333; margin-bottom: 30px; background: rgba(255,255,255,0.9); padding: clamp(18px, 4vw, 30px); border-radius: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); }
.result-title { font-size: 1.8rem; font-weight: 700; margin-bottom: 10px; color: #6A1B9A; }
.result-actions { display: flex; flex-direction: column; gap: 10px; align-items: center; margin-top: 20px; }
.status-guidance { padding: 12px 16px; border-radius: 12px; background: #fff4c2; }
.status-guidance.danger { background: #ffe0e0; color: #9d2020; }
.action-link { text-decoration: none; font-size: 1rem; font-weight: bold; color: #6A1B9A; padding: 12px 25px; border-radius: 10px; border: 1px solid #ddd; background: #fff; width: 100%; max-width: 250px; box-sizing: border-box; }
.action-link.primary { background-color: #6A1B9A; color: white; border: none; }

.chat-messages-container { width: 100%; max-width: 700px; min-width: 0; margin-top: 10px; display: flex; flex-direction: column; gap: 10px; padding-bottom: 20px; }
.divider { display: flex; align-items: center; text-align: center; color: #888; font-size: 0.8rem; margin: 15px 0; }
.divider::before, .divider::after { content: ''; flex: 1; border-bottom: 1px solid #ddd; }
.divider span { padding: 0 10px; }
.message-bubble { padding: 12px 18px; border-radius: 18px; max-width: min(85%, 760px); width: fit-content; line-height: 1.6; position: relative; box-shadow: 0 2px 6px rgba(0,0,0,0.05); font-size: 0.95rem; overflow-wrap: anywhere; }
.user-message { background-color: #f0e6ff; align-self: flex-start; border-bottom-right-radius: 4px; }
.bot-message { background-color: #fff; align-self: flex-end; border-bottom-left-radius: 4px; }
.message-bubble.thinking-bubble { width: 100%; max-width: 100%; padding: 14px 0 14px 14px; background: transparent; box-shadow: none; text-align: left; align-self: stretch; }
.thinking-indicator { display: inline-flex; align-items: center; justify-content: center; min-width: 150px; padding: 4px 0; }
.thinking-text {
  display: inline-block;
  color: #c9a9e8;
  font-size: 1.28rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  background: linear-gradient(90deg, #c9a9e8 0%, #c9a9e8 30%, #6a1b9a 48%, #c9a9e8 66%, #c9a9e8 100%);
  background-size: 240% 100%;
  background-position: 100% 0;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: test-thinking-sweep 1.8s ease-in-out infinite;
}
@keyframes test-thinking-sweep {
  0% { background-position: 100% 0; }
  50% { background-position: 0% 0; }
  100% { background-position: 100% 0; }
}

:deep(.rag-source-link) { color: #0b57d0; text-decoration: underline; font-weight: 600; word-break: break-word; unicode-bidi: isolate; }
:deep(.rag-source-citation) { display: inline-block; margin-inline-start: 0.35rem; color: #5f6368; font-size: 0.92em; unicode-bidi: isolate; }
:deep(.rag-source-separator) { margin-inline: 0.18rem; color: #7a7a7a; }
:deep(.rag-source-site) { unicode-bidi: isolate; }

.rag-debug {
  margin-top: 10px;
  border-top: 1px dashed rgba(0, 0, 0, 0.15);
  padding-top: 8px;
  font-size: 0.78rem;
  color: #555;
}

.rag-debug pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 8px 0 0;
  font-family: Consolas, monospace;
}

.mobile-header { display: none; } 
@media (max-width: 900px) {
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
    padding: 12px 12px calc(92px + env(safe-area-inset-bottom));
  }

  .test-intro-card,
  .final-result-container { border-radius: 20px; }

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
    min-width: min(100px, 42vw);
  }

  .chat-input-wrapper {
    padding: 10px 15px calc(10px + env(safe-area-inset-bottom));
  }
  
  .spacer { height: calc(80px + env(safe-area-inset-bottom)); }
}

@media (max-width: 480px) {
  .mobile-header { height: 54px; padding-inline: 10px; }
  .mobile-title { max-width: 55vw; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .test-intro-card { padding: 18px 15px; line-height: 1.85; }
  .child-summary { gap: 8px; margin: 14px 0; }
  .previous-test-note { padding: 10px 12px; }
  .test-image { max-height: 170px; margin-bottom: 14px; }
  .question-bubble { padding: 14px 12px; font-size: 0.95rem; }
  .answer-options { flex-direction: column; align-items: stretch; }
  .option-btn { width: 100%; max-width: none; min-width: 0; }
  .result-title { font-size: 1.4rem; }
  .message-bubble { max-width: 100%; padding: 11px 12px; font-size: 0.9rem; }
}
</style>
