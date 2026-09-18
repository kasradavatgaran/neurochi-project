
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
          <img v-if="user.profile_image_url" :src="toApiUrl(user.profile_image_url)" class="profile-icon">
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
            <div class="rich-text" v-html="formatRichText(msg.content)"></div>
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
          
          <div v-else-if="msg.type === 'analysis-message'" class="message-bubble analysis-bubble" :class="{ 'analysis-loading-bubble': isAnalysisLoading && !msg.content }">
            <div v-if="isAnalysisLoading && !msg.content" class="thinking-indicator" role="status" aria-label="می‌اندیشم">
              <span class="thinking-text">می‌اندیشم..</span>
            </div>
            <div v-else-if="analysisError" class="analysis-error-state">
              <h3>تحلیل نهایی نوروچی</h3>
              <p>دریافت تحلیل موقتاً با مشکل روبه‌رو شد.</p>
              <button type="button" class="retry-analysis-button" @click="getFinalAnalysis" :disabled="isAnalysisLoading">
                ↻ امتحان مجدد
              </button>
              <router-link to="/dashboard" class="final-back-button">بازگشت به داشبورد</router-link>
            </div>
            <div v-else>
              <h3>تحلیل نهایی نوروچی</h3>
              <div class="analysis-rich-text" :class="{ 'is-streaming': isAnalysisLoading }" v-html="formatRichText(msg.content)"></div>
              <router-link v-if="!isAnalysisLoading" to="/dashboard" class="final-back-button">بازگشت به داشبورد</router-link>
            </div>
          </div>

          <div v-else-if="msg.type === 'user-message'" class="message-bubble user-bubble">
            <p>{{ msg.content }}</p>
          </div>

          <div v-else-if="msg.type === 'bot-message'" class="message-bubble bot-bubble">
            <div class="rich-text" v-html="formatRichText(msg.content, msg.sources)"></div>
            <details v-if="showRagDebug && msg.debugInfo" class="rag-debug">
              <summary>RAG Debug</summary>
              <pre>{{ msg.debugInfo }}</pre>
            </details>
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
          <img :src="toApiUrl(game.image_url)" class="game-thumbnail" alt="Game">
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
import api, { toApiUrl as buildApiUrl } from '@/services/api';
import { renderMessage } from '@/utils/markdown';
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
    analysisError: false,
    isChatActive: false,
    userMessage: '',
    recorder: null,
    isRecording: false,
    isLocked: false,
    lockMessage: '',
    testStatus: null,
    showRagDebug: false,
  };
  },
  computed: {
    currentGame() {
      return this.games.length > this.completedGamesCount ? this.games[this.completedGamesCount] : null;
    }
  },
  methods: {
    formatRichText(text, sources = []) {
      return renderMessage(text, sources);
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
    toApiUrl(path) {
      return buildApiUrl(path);
    },
    addMessage(type, content, sources = [], debugInfo = '') {
      this.conversation.push({ type, content, sources, debugInfo });
      this.scrollToBottom();
    },
    buildGameContext() {
      const currentGame = this.currentGame;
      const analysisMessage = [...this.conversation].reverse().find(
        message => message.type === 'analysis-message' && message.content,
      );
      const completedGameTitles = this.games
        .slice(0, this.completedGamesCount)
        .map(game => game.title)
        .filter(Boolean);
      return [
        'Page: child development game session',
        `Skill category: ${this.skillCategory}`,
        this.childName ? `Child: ${this.childName}` : '',
        `Completed games: ${this.completedGamesCount}`,
        completedGameTitles.length ? `Completed game titles: ${completedGameTitles.join(' | ')}` : '',
        currentGame?.title ? `Current game: ${currentGame.title}` : '',
        currentGame?.description ? `Current game instructions: ${currentGame.description}` : '',
        analysisMessage ? `Current game analysis:\n${analysisMessage.content}` : '',
      ].filter(Boolean).join('\n');
    },

    async fetchInitialData() {
  this.isLoading = true;
  const phoneNumber = localStorage.getItem('loggedInUserPhone');
  if (!phoneNumber) { this.$router.push('/'); return; }
  
  try {
    const userResponse = await api.get(`/me/${phoneNumber}`);
    this.user = userResponse.data;
    this.children = userResponse.data.children;
    const currentChild = this.children.find(c => c.id == this.childId);
    if (currentChild) this.childName = currentChild.name;
    
    const gamesResponse = await api.get(`/children/${this.childId}/suggested-games?skill_category=${this.skillCategory}`);
    const data = gamesResponse.data;
    this.testStatus = data.test_status || null;

    if (data.status === 'locked') {
        this.isLocked = true;
        this.lockMessage = data.message;
    } else if (data.status === 'available' && data.games.length > 0) {
        this.games = data.games;
        this.isLocked = false;
        
        const statusMessage = this.testStatus === 'red'
          ? 'برای بررسی دقیق‌تر، علاوه بر انجام بازی‌ها لطفاً با پزشک کودک مشورت کنید.'
          : 'چند روز با این بازی‌ها تمرین کنید و سپس برای انجام دوباره تست به نوروچی برگردید.';
        this.addMessage('system-message', `
          ${this.user.parent_name} عزیز،<br>
          ${this.childName} در مهارت «${this.skillCategory}» نیاز به تمرین دارد.<br>
          برای بهبود این مهارت، ۵ بازی منتخب برای این هفته آماده کرده‌ایم.<br>
          ${statusMessage}
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
        await api.post('/games/answer', payload);
        
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
        if (this.isAnalysisLoading) return;
        this.isAnalysisLoading = true;
        this.analysisError = false;
        let analysisMessage = null;
        for (let index = this.conversation.length - 1; index >= 0; index -= 1) {
          if (this.conversation[index].type === 'analysis-message') {
            analysisMessage = this.conversation[index];
            break;
          }
        }
        if (!analysisMessage) {
          this.addMessage('analysis-message', '');
          analysisMessage = this.conversation[this.conversation.length - 1];
        }
        analysisMessage.content = '';
        try {
            const streamUrl = buildApiUrl(
              `/children/${this.childId}/final-analysis?skill_category=${encodeURIComponent(this.skillCategory)}&stream=true`,
            );
            const response = await fetch(streamUrl, {
              headers: { Accept: 'text/event-stream' },
            });
            if (!response.ok) {
              throw new Error(`Final analysis request failed with status ${response.status}`);
            }

            const contentType = response.headers.get('content-type') || '';
            if (!response.body || !contentType.includes('text/event-stream')) {
              const data = await response.json();
              if (!data?.analysis) throw new Error('Final analysis response was empty');
              analysisMessage.content = data.analysis;
            } else {
              const reader = response.body.getReader();
              const decoder = new TextDecoder('utf-8');
              let buffer = '';
              let streamedText = '';
              let completedPayload = null;

              const handleEvent = (block) => {
                const lines = block.split(/\r?\n/);
                const eventName = lines.find(line => line.startsWith('event:'))?.slice(6).trim() || 'message';
                const dataLine = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n');
                if (!dataLine) return;
                const data = JSON.parse(dataLine);
                if (eventName === 'chunk') {
                  streamedText += data.text || '';
                  analysisMessage.content = streamedText;
                  this.$forceUpdate();
                  this.scrollToBottom();
                } else if (eventName === 'done') {
                  completedPayload = data;
                } else if (eventName === 'error') {
                  throw new Error(data.message || 'Final analysis streaming failed');
                }
              };

              while (true) {
                const { value, done } = await reader.read();
                buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
                const blocks = buffer.split(/\r?\n\r?\n/);
                buffer = blocks.pop() || '';
                blocks.filter(Boolean).forEach(handleEvent);
                if (done) break;
              }
              if (buffer.trim()) handleEvent(buffer);
              if (!completedPayload?.analysis && !streamedText) {
                throw new Error('Streaming response ended before completion');
              }
              analysisMessage.content = completedPayload?.analysis || streamedText;
            }
            this.isChatActive = true; 
        } catch (error) {
            console.error('Error getting final analysis:', error.response?.data || error);
            this.analysisError = true;
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
          context: this.buildGameContext(),
        };
        const response = await api.post('/chat', payload);
        this.addMessage(
          'bot-message',
          response.data.response,
          Array.isArray(response.data.sources) ? response.data.sources : [],
          this.buildDebugInfo(response.data),
        );
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
            const url = `/transcribe-audio?phone_number=${encodeURIComponent(phoneNumber)}&child_id=${this.childId}&context=${encodeURIComponent(this.buildGameContext())}`;
            
            const response = await api.post(url, formData);

            const transcribedText = response.data.transcribed_text;
            const botResponse = response.data.bot_response;
            
            this.addMessage('user-message', `(پیام صوتی): "${transcribedText}"`);
            this.addMessage(
              'bot-message',
              botResponse,
              Array.isArray(response.data.sources) ? response.data.sources : [],
              this.buildDebugInfo(response.data),
            );

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
:deep(.analysis-rich-text strong), :deep(.message-bubble strong) { font-weight: 800; }
:deep(.analysis-rich-text h4), :deep(.message-bubble h4) { margin: 14px 0 6px; color: #6a1b9a; font-size: 1.05em; }
:deep(.analysis-rich-text ul), :deep(.message-bubble ul) { margin: 8px 0; padding-right: 22px; }
:deep(.analysis-rich-text li), :deep(.message-bubble li) { margin: 5px 0; }
:deep(.analysis-rich-text a), :deep(.message-bubble a) { color: #0b57d0; text-decoration: underline; }
:deep(.analysis-rich-text code), :deep(.message-bubble code) { background: #f3eef8; padding: 1px 5px; border-radius: 5px; }
</style>


<style scoped>
.game-page-wrapper { 
  display: grid; 
  grid-template-columns: 280px 1fr 300px;
  width: 100%;
  height: 100dvh; 
  min-height: 100dvh;
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
  height: 100dvh; 
  min-height: 0;
  box-sizing: border-box; 
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  touch-action: pan-y;
}
.children-sidebar { border-left: 1px solid rgba(0,0,0,0.1); }
.games-sidebar { border-right: 1px solid rgba(0,0,0,0.1); }

.sidebar-header { display: flex; align-items: center; gap: 10px; margin-bottom: 40px; }
.logo { width: 40px; }
.header-link { text-decoration: none; color: inherit; font-size: 1.2rem; font-weight: bold;}
.children-list, .games-list {
  flex-grow: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  touch-action: pan-y;
}
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
  display: flex; flex-direction: column; height: 100dvh; min-height: 0; position: relative; width: 100%; min-width: 0; overflow: hidden;
}
.mobile-header { display: none; }

.chat-area { 
  flex-grow: 1; 
  min-width: 0;
  min-height: 0;
  overflow-y: auto; 
  overflow-x: hidden;
  padding: 20px 20px 125px; 
  display: flex; 
  flex-direction: column; 
  gap: 20px; 
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  touch-action: pan-y;
}
.spacer { height: 100px; width: 100%; flex-shrink: 0; }

:deep(.rag-source-link) {
  color: #0b57d0;
  text-decoration: underline;
  font-weight: 600;
  word-break: break-word;
  unicode-bidi: isolate;
}

:deep(.rag-source-citation) {
  display: inline-block;
  margin-inline-start: 0.35rem;
  color: #5f6368;
  font-size: 0.92em;
  unicode-bidi: isolate;
}

:deep(.rag-source-separator) {
  margin-inline: 0.18rem;
  color: #7a7a7a;
}

:deep(.rag-source-site) {
  unicode-bidi: isolate;
}

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

.message-container { display: flex; flex-direction: column; width: 100%; min-width: 0; }
.message-bubble { 
  min-width: 0; padding: 20px 25px; border-radius: 20px; max-width: min(80%, 900px); width: fit-content;
  box-shadow: 0 3px 10px rgba(0,0,0,0.05); line-height: 1.7; position: relative;
  overflow-wrap: anywhere;
}

.system-bubble { background-color: #fff3e0; align-self: center; text-align: center; font-size: 0.95rem; border: 1px solid #ffe0b2; }
.game-bubble { background-color: #fff; align-self: center; max-width: 90%; border: 1px solid #f3e5f5; }
.game-bubble h3 { color: #6A1B9A; margin-top: 0; border-bottom: 1px solid #f3e5f5; padding-bottom: 10px; margin-bottom: 10px; }
.analysis-bubble { background-color: #e3f2fd; align-self: center; max-width: 90%; }
.analysis-loading-bubble { background: transparent; box-shadow: none; padding: 16px 0; text-align: left; align-self: flex-start; margin-right: auto; margin-left: 0; }
.analysis-error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
}
.analysis-error-state h3 { margin-bottom: 2px; }
.analysis-error-state p { margin: 0; color: #5f536a; }
.retry-analysis-button {
  min-height: 44px;
  padding: 0 20px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #7b1fa2, #5e1590);
  color: #fff;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(106, 27, 154, 0.2);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}
.retry-analysis-button:hover {
  transform: translateY(-2px);
  filter: brightness(1.06);
  box-shadow: 0 12px 24px rgba(106, 27, 154, 0.26);
}
.retry-analysis-button:disabled { opacity: 0.6; cursor: wait; transform: none; }
.user-bubble { background-color: #f0e6ff; align-self: flex-start; border-bottom-right-radius: 4px; }
.bot-bubble { background-color: #fff; align-self: flex-end; border-bottom-left-radius: 4px; }

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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 18px;
  min-height: 44px;
  padding: 0 22px;
  box-sizing: border-box;
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 14px;
  background: linear-gradient(135deg, #7b1fa2, #5e1590);
  color: #fff !important;
  text-decoration: none !important;
  font-weight: 800;
  line-height: 1;
  box-shadow: 0 8px 18px rgba(106, 27, 154, 0.22);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}
.final-back-button:hover {
  color: #fff !important;
  text-decoration: none !important;
  transform: translateY(-2px);
  filter: brightness(1.06);
  box-shadow: 0 12px 24px rgba(106, 27, 154, 0.28);
}
.final-back-button:focus-visible {
  outline: 3px solid rgba(106, 27, 154, 0.28);
  outline-offset: 3px;
}

.chat-input-wrapper { 
  position: absolute; bottom: 0; left: 0; right: 0; padding: 15px 20px calc(15px + env(safe-area-inset-bottom)); 
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
  animation: analysis-thinking-sweep 1.8s ease-in-out infinite;
}
.analysis-rich-text.is-streaming::after {
  content: '';
  display: inline-block;
  width: 2px;
  height: 1.05em;
  margin-right: 3px;
  vertical-align: -0.16em;
  border-radius: 999px;
  background: #8e44ad;
  animation: analysis-stream-caret 0.9s ease-in-out infinite;
}
@keyframes analysis-thinking-sweep {
  0% { background-position: 100% 0; }
  50% { background-position: 0% 0; }
  100% { background-position: 100% 0; }
}
@keyframes analysis-stream-caret {
  0%, 100% { opacity: 0.2; transform: scaleY(0.75); }
  50% { opacity: 1; transform: scaleY(1); }
}

@media (max-width: 1024px) {
  .game-page-wrapper {
    display: flex; 
    flex-direction: column;
    height: 100dvh;
    min-height: 100dvh;
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
    padding: 15px 12px calc(116px + env(safe-area-inset-bottom));
  }

  .message-bubble {
    max-width: 96%; 
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
    padding: 10px 15px calc(10px + env(safe-area-inset-bottom));
  }
}

@media (max-width: 600px) {
  .mobile-header { height: 54px; padding-inline: 10px; }
  .mobile-title { max-width: 58vw; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .chat-area { padding: 12px 8px calc(108px + env(safe-area-inset-bottom)); gap: 12px; }
  .message-bubble { max-width: 100%; padding: 12px 13px; font-size: 0.9rem; line-height: 1.8; }
  .game-answer-buttons { flex-direction: column; gap: 8px; }
  .answer-btn { width: 100%; max-width: none; min-width: 0; }
  .analysis-bubble, .game-bubble, .system-bubble { max-width: 100%; }
  .analysis-bubble { padding: 16px 13px; }
  .analysis-bubble h3 { font-size: 1.05rem; }
  .locked-overlay { padding: 12px; }
  .locked-card { padding: 22px 16px; border-radius: 22px; }
  .lock-icon-large { font-size: 2.6rem; }
  .final-back-button { width: 100%; padding-inline: 14px; }
}
</style>
