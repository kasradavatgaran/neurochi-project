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
          <button
            type="button"
            class="new-chat-button"
            @click.stop="startNewChat(child)"
            :disabled="isSubmitting"
            title="چت جدید"
          >
            + چت جدید
          </button>
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

      <div
        class="general-chat-item"
        :class="{ active: !selectedChild }"
        @click="selectGeneralChat"
      >
        <span>چت عمومی</span>
        <button
          type="button"
          class="new-chat-button"
          @click.stop="startNewChat()"
          :disabled="isSubmitting"
          title="چت جدید"
        >
          + چت جدید
        </button>
      </div>

      <div class="chat-session-list">
        <div class="chat-session-heading">{{ selectedChild ? `گفتگوهای ${selectedChild.name}` : 'گفتگوهای عمومی' }}</div>
        <div
          v-for="session in chatSessions"
          :key="session.id"
          class="chat-session-row"
        >
          <button
            type="button"
            class="chat-session-item"
            :class="{ active: session.id === activeChatSessionId }"
            @click="selectChatSession(session)"
          >
            <span>{{ session.title }}</span>
            <small>{{ session.message_count || 0 }}</small>
          </button>
          <button
            type="button"
            class="delete-session-button"
            @click.stop="deleteChatSession(session)"
            :disabled="isSubmitting"
            title="حذف دائمی گفتگو"
            aria-label="حذف دائمی گفتگو"
          >×</button>
        </div>
      </div>

      <div class="sidebar-footer">
        <router-link to="/add-child" class="add-child-btn" @click="isSidebarOpen = false">
          <span>اضافه کردن فرزند</span>
          <span class="plus-icon">+</span>
        </router-link>
        <router-link to="/edit-profile" class="profile-section" @click="isSidebarOpen = false">
          <span>{{ user.parent_name }}</span>
          <img v-if="user.profile_image_url" :src="toApiUrl(user.profile_image_url)" class="profile-icon">
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
        <router-link
          v-if="selectedChild"
          :to="{ name: 'GrowthChartPage', params: { childId: selectedChild.id } }"
          class="mobile-chart-btn"
          title="نمودار رشد"
          aria-label="نمودار رشد"
        >
          📈
        </router-link>
        <div v-else class="mobile-header-spacer"></div>
      </div>

      <section class="conversation-stage">
        <div class="chat-area" ref="chatArea">
          <div v-if="conversation.length === 0" class="initial-message">
            <p class="welcome-copy">{{ selectedChild ? welcomeMessage() : generalWelcomeMessage() }}</p>
          </div>

          <div v-for="msg in conversation" :key="msg.id" class="message-bubble" :class="[msg.role === 'user' ? 'user-message' : 'bot-message', { 'thinking-bubble': msg.isLoading }]">
            <template v-if="msg.isLoading">
              <div class="thinking-indicator" role="status" aria-label="می‌اندیشم">
                <span class="thinking-text">می‌اندیشم..</span>
              </div>
            </template>
            <template v-else>
              <div class="rich-text" :class="{ 'is-streaming': msg.isStreaming }" v-html="renderMessageHtml(msg)"></div>
              <div v-if="msg.role === 'assistant' && msg.sources && msg.sources.length" class="message-actions">
                <button type="button" class="sources-button" @click="openSources(msg)">
                  <span class="sources-button-icon">▱</span>
                  Sources <span class="sources-count">{{ msg.sources.length }}</span>
                </button>
              </div>
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
      </section>

      <section class="bottom-dock" :class="{ suggested: selectedChild && shouldHighlightSkills }">
        <div v-if="selectedChild" class="categories-grid">
          <button
            v-for="cat in categories"
            :key="cat.skillCategory"
            type="button"
            class="category-card"
            :style="{ '--card-accent': cat.accent, '--card-glow': cat.glow }"
            :disabled="isSubmitting"
            :title="`شروع مسیر ${cat.title}`"
            :aria-label="cat.title"
            @click="navigateToTest(cat)"
          >
            <span class="category-icon">{{ cat.icon }}</span>
            <span class="category-label">{{ cat.title }}</span>
          </button>
        </div>

        <div class="composer-shell">
          <ChatInput
            :is-active="true"
            :is-submitting="isSubmitting"
            :placeholder="chatPlaceholder"
            @send-text="handleSendText"
            @send-audio="handleSendAudio"
          />
        </div>
      </section>
    </main>

    <div v-if="sourcesPanelOpen" class="sources-overlay" @click="closeSources"></div>
    <aside v-if="sourcesPanelOpen" class="sources-panel" aria-label="منابع پاسخ" @click.stop>
      <div class="sources-panel-header">
        <div>
          <span class="sources-eyebrow">REFERENCE DESK</span>
          <h2>منابع پاسخ</h2>
          <p>{{ selectedSources.length }} منبع مرتبط با این پاسخ</p>
        </div>
        <button type="button" class="sources-close" aria-label="بستن منابع" @click="closeSources">×</button>
      </div>
      <div class="sources-panel-body">
        <article v-for="(source, index) in selectedSources" :key="`${source.url}-${source.source_file}-${index}`" class="source-detail-card">
          <div class="source-card-topline">
            <span class="source-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="source-kind">بخش {{ source.chunk_index || '-' }}<template v-if="source.chunk_count"> از {{ source.chunk_count }}</template></span>
          </div>
          <h3>{{ source.title || 'منبع بدون عنوان' }}</h3>
          <div class="source-meta">
            <span>{{ source.source_name || source.source_file || 'آرشیو محلی' }}</span>
            <a v-if="source.url" :href="source.url" target="_blank" rel="noopener noreferrer">باز کردن مقاله ↗</a>
          </div>
          <p class="source-chunk-text">{{ source.content || 'متن این chunk برای پیام‌های قدیمی ذخیره نشده است.' }}</p>
        </article>
      </div>
    </aside>
  </div>
</template>


<script>
import api, { toApiUrl as buildApiUrl } from '@/services/api';
import ChatInput from './ChatInput.vue';
import { renderMessage } from '@/utils/markdown';

export default {
  name: 'DashboardPage',
  components: { ChatInput },
  data() {
    return {
      user: {},
      children: [],
      selectedChild: null,
      activeChatScope: null,
      chatSessions: [],
      activeChatSessionId: null,
      activeMenu: null,
      conversation: [],
      isSubmitting: false,
      audioPlayer: new Audio(),
      isAudioPlaying: false,
      isSidebarOpen: false,
      sourcesPanelOpen: false,
      selectedSources: [],
      showRagDebug: false,
      shouldHighlightSkills: false,
      categories: [
        {
          title: 'حرکتی درشت',
          skillCategory: 'مهارت های حرکتی درشت',
          subtitle: 'تعادل، نشستن و راه رفتن',
          icon: '🏃',
          accent: 'rgba(255, 202, 167, 0.9)',
          glow: 'rgba(255, 154, 102, 0.18)',
        },
        {
          title: 'حرکات ظریف',
          skillCategory: 'مهارت های حرکتی ریز',
          subtitle: 'گرفتن، لمس و هماهنگی دست',
          icon: '🖐️',
          accent: 'rgba(255, 226, 184, 0.95)',
          glow: 'rgba(242, 180, 65, 0.18)',
        },
        {
          title: 'حل مسئله',
          skillCategory: 'حل مسئله',
          subtitle: 'کشف، آزمون و تجربه',
          icon: '🧩',
          accent: 'rgba(202, 228, 255, 0.95)',
          glow: 'rgba(94, 160, 255, 0.18)',
        },
        {
          title: 'ارتباطات',
          skillCategory: 'ارتباطات',
          subtitle: 'زبان، صدا و اشاره',
          icon: '💬',
          accent: 'rgba(220, 214, 255, 0.95)',
          glow: 'rgba(132, 116, 255, 0.18)',
        },
        {
          title: 'شخصی اجتماعی',
          skillCategory: 'شخصی - اجتماعی',
          subtitle: 'رابطه، آرامش و تعامل',
          icon: '🌱',
          accent: 'rgba(214, 245, 220, 0.95)',
          glow: 'rgba(92, 179, 116, 0.18)',
        },
      ],
    };
  },
  computed: {
    chatPlaceholder() {
      if (!this.selectedChild) {
        return 'سؤال خود را دربارهٔ کودک و فرزندپروری بپرسید.';
      }
      return `اگر در مورد ${this.selectedChild.name} سوالی داری بپرس.`;
    },
  },
  methods: {
    welcomeMessage() {
      return `سلام 👋 به نوروچی، دستیار هوشمند والدین خوش اومدی 🌱
نوروچی اینجاست تا در مسیر رشد و تکامل فرزندت همراهت باشه؛ از پاسخ دادن به سوال‌های روزمره درباره رشد، رفتار، بازی و یادگیری کودک گرفته تا کمک در انجام تست‌های رشدی متناسب با سن فرزندت. هر زمان که نگرانی، ابهام یا حتی یک سوال ساده داشتی، می‌تونی با من صحبت کنی و راهنمایی بگیری. اگر هم دوست داشته باشی، می‌تونیم با هم تست‌های مربوط به فرزندت رو شروع کنیم و قدم‌به‌قدم وضعیت رشدش رو بررسی کنیم. 💜`;
    },
    generalWelcomeMessage() {
      return 'سلام 👋 این چت عمومی نوروجی است. می‌توانید بدون ثبت فرزند دربارهٔ رشد، خواب، تغذیه و فرزندپروری سؤال بپرسید. برای دریافت تحلیل شخصی، تست‌ها و نمودار رشد، هر زمان خواستید یک فرزند اضافه کنید.';
    },
    toApiUrl(path) {
      return buildApiUrl(path);
    },
    stripHtml(text) {
      const container = document.createElement('div');
      container.innerHTML = text || '';
      return container.textContent || container.innerText || '';
    },
    renderMessageHtml(message) {
      return renderMessage(message?.content, message?.sources || []);
    },
    openSources(message) {
      this.selectedSources = Array.isArray(message?.sources) ? message.sources : [];
      this.sourcesPanelOpen = this.selectedSources.length > 0;
    },
    closeSources() {
      this.sourcesPanelOpen = false;
    },
    chatScopeKey(child = null) {
      return child?.id ? `child:${child.id}` : 'general';
    },
    isCurrentChatScope(scopeKey) {
      return this.chatScopeKey(this.selectedChild) === scopeKey;
    },
    sessionMatchesScope(session, scopeKey) {
      if (!session) return false;
      if (scopeKey === 'general') return session.child_id === null || session.child_id === undefined;
      return scopeKey === `child:${session.child_id}`;
    },
    syncChatSession(session, scopeKey = this.chatScopeKey(this.selectedChild)) {
      if (!session || !session.id || !this.isCurrentChatScope(scopeKey) || !this.sessionMatchesScope(session, scopeKey)) return;
      const index = this.chatSessions.findIndex(item => item.id === session.id);
      if (index === -1) {
        this.chatSessions.unshift(session);
      } else {
        this.chatSessions.splice(index, 1, session);
      }
      this.activeChatSessionId = session.id;
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
        if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
      });
    },
    addMessageToConversation(role, content, id = null, isLoading = false, sources = [], debugInfo = '', isStreaming = false) {
      const messageId = id || (Date.now() + Math.random().toString(36).substr(2, 9));
      this.conversation.push({ id: messageId, role, content, isLoading, sources, debugInfo, isStreaming });
      this.scrollToBottom();
    },
    
    toggleSidebar() {
  this.isSidebarOpen = !this.isSidebarOpen;
},
    updateMessageById(id, newContent, newIsLoadingState = false, newSources = [], newDebugInfo = '', newIsStreamingState = false) {
      const messageIndex = this.conversation.findIndex(msg => msg.id === id);
      if (messageIndex !== -1) {
        this.conversation[messageIndex].content = newContent;
        this.conversation[messageIndex].isLoading = newIsLoadingState;
        this.conversation[messageIndex].sources = newSources;
        this.conversation[messageIndex].debugInfo = newDebugInfo;
        this.conversation[messageIndex].isStreaming = newIsStreamingState;
        this.$forceUpdate(); 
      }
      this.scrollToBottom();
    },
    async fetchUserData() {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      if (!phoneNumber) { this.$router.push('/'); return; }
      try {
        const response = await api.get(`/me/${phoneNumber}`);
        this.user = response.data;
        this.children = response.data.children;
        await this.selectGeneralChat();
      } catch (error) {
        localStorage.removeItem('loggedInUserPhone');
        this.$router.push('/');
      }
    },

    async loadChatHistory(child = null, sessionId = null, scopeKey = this.chatScopeKey(child)) {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      const url = child
        ? `/chat/history/${phoneNumber}/${child.id}`
        : `/chat/history/${phoneNumber}`;
      const response = await api.get(url, {
        params: sessionId ? { session_id: sessionId } : {},
      });
      if (!this.isCurrentChatScope(scopeKey) || this.activeChatSessionId !== sessionId) return false;
      this.conversation = response.data.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        isLoading: false,
        sources: Array.isArray(msg.sources) ? msg.sources : [],
        debugInfo: '',
      }));
      this.scrollToBottom();
      return true;
    },

    async loadChatSessions(child = null, preferredId = null, scopeKey = this.chatScopeKey(child)) {
      const phoneNumber = localStorage.getItem('loggedInUserPhone');
      const url = child ? `/children/${child.id}/chat-sessions` : '/chat-sessions';
      const response = await api.get(url, {
        params: { phone_number: phoneNumber },
      });
      if (!this.isCurrentChatScope(scopeKey)) return false;
      this.chatSessions = Array.isArray(response.data) ? response.data : [];
      const selected = this.chatSessions.find(item => item.id === preferredId);
      this.activeChatSessionId = selected?.id || this.chatSessions[0]?.id || null;
      if (this.activeChatSessionId) {
        await this.loadChatHistory(child, this.activeChatSessionId, scopeKey);
      } else {
        this.conversation = [];
      }
      return true;
    },

    async selectGeneralChat() {
      const scopeKey = 'general';
      this.selectedChild = null;
      this.activeChatScope = 'general';
      this.activeMenu = null;
      this.isSidebarOpen = false;
      this.shouldHighlightSkills = false;
      this.conversation = [];
      this.chatSessions = [];
      this.activeChatSessionId = null;
      this.isSubmitting = true;
      try {
        await this.loadChatSessions(null, null, scopeKey);
      } catch (error) {
        console.error('Error fetching general chat sessions/history:', error);
      } finally {
        if (this.isCurrentChatScope(scopeKey)) this.isSubmitting = false;
      }
    },

    async selectChild(child) {
      if (this.selectedChild?.id === child.id) {
        this.isSidebarOpen = false;
        return;
      }
      const scopeKey = this.chatScopeKey(child);
      this.selectedChild = child;
      this.activeChatScope = 'child';
      this.activeMenu = null;
      this.isSidebarOpen = false;
      this.shouldHighlightSkills = false;
      this.conversation = [];
      this.chatSessions = [];
      this.activeChatSessionId = null;
      this.isSubmitting = true;

      try {
        await this.loadChatSessions(child, null, scopeKey);
      } catch (error) {
        console.error('Error fetching chat sessions/history:', error);
      } finally {
        if (this.isCurrentChatScope(scopeKey)) this.isSubmitting = false;
      }
    },

    async selectChatSession(session) {
      if (session.id === this.activeChatSessionId) return;
      const child = this.selectedChild;
      const scopeKey = this.chatScopeKey(child);
      this.isSubmitting = true;
      this.activeChatSessionId = session.id;
      try {
        await this.loadChatHistory(child, session.id, scopeKey);
      } catch (error) {
        console.error('Error fetching chat session history:', error);
      } finally {
        if (this.isCurrentChatScope(scopeKey)) this.isSubmitting = false;
      }
    },

    async startNewChat(child = null) {
      const scopeKey = this.chatScopeKey(child);
      this.selectedChild = child;
      this.activeChatScope = child ? 'child' : 'general';
      this.activeMenu = null;
      this.isSidebarOpen = false;
      this.shouldHighlightSkills = false;
      this.conversation = [];
      this.chatSessions = [];
      this.activeChatSessionId = null;
      this.isSubmitting = true;
      try {
        const phoneNumber = localStorage.getItem('loggedInUserPhone');
        const url = child ? `/children/${child.id}/chat-sessions` : '/chat-sessions';
        const response = await api.post(
          url,
          { title: 'گفتگوی جدید' },
          { params: { phone_number: phoneNumber } },
        );
        if (!this.isCurrentChatScope(scopeKey)) return;
        await this.loadChatSessions(child, response.data.id, scopeKey);
      } catch (error) {
        console.error('Error creating chat session:', error);
      } finally {
        if (this.isCurrentChatScope(scopeKey)) this.isSubmitting = false;
      }
    },

    async deleteChatSession(session) {
      const child = this.selectedChild;
      const scopeKey = this.chatScopeKey(child);
      if (!confirm('این گفتگو و همهٔ پیام‌ها و منابع آن برای همیشه حذف شود؟')) return;
      this.isSubmitting = true;
      try {
        const phoneNumber = localStorage.getItem('loggedInUserPhone');
        await api.delete(`/chat-sessions/${session.id}`, { params: { phone_number: phoneNumber } });
        if (!this.isCurrentChatScope(scopeKey)) return;
        this.chatSessions = this.chatSessions.filter(item => item.id !== session.id);
        if (session.id === this.activeChatSessionId) {
          const nextSession = this.chatSessions[0] || null;
          this.activeChatSessionId = nextSession?.id || null;
          if (nextSession) {
            await this.loadChatHistory(child, nextSession.id, scopeKey);
          } else {
            this.conversation = [];
          }
        }
      } catch (error) {
        console.error('Error deleting chat session:', error);
        alert('خطا در حذف گفتگو.');
      } finally {
        if (this.isCurrentChatScope(scopeKey)) this.isSubmitting = false;
      }
    },

    async handleSendText(message) {
      if (!message || this.isSubmitting) return;
      
      this.addMessageToConversation('user', message);
      
      await this.getBotResponse(message);
    },

    async handleSendAudio(blob) {
      if (this.isSubmitting) return;
      const child = this.selectedChild;
      const scopeKey = this.chatScopeKey(child);
      const chatSessionId = this.activeChatSessionId;
      
      this.isSubmitting = true;
      
      const tempUserId = 'audio-user-' + Date.now();
      this.addMessageToConversation('user', '(در حال پردازش صدا...)', tempUserId, true);
      
      const formData = new FormData();
      formData.append('file', blob, 'recording.mp3');
      
      try {
        const phoneNumber = localStorage.getItem('loggedInUserPhone');
        const params = new URLSearchParams({ phone_number: phoneNumber });
        if (child) params.set('child_id', child.id);
        if (chatSessionId) params.set('chat_session_id', chatSessionId);
        const url = `/transcribe-audio?${params.toString()}`;
        
        const response = await api.post(url, formData);
        
        const transcribedText = response.data.transcribed_text;
        const botResponse = response.data.bot_response;
        const sources = Array.isArray(response.data.sources) ? response.data.sources : [];
        const debugInfo = this.buildDebugInfo(response.data);
        if (!this.isCurrentChatScope(scopeKey)) return;
        
        this.updateMessageById(tempUserId, `(پیام صوتی): "${transcribedText}"`, false);
        if (response.data.show_tests && child) {
          this.shouldHighlightSkills = true;
        }
        
        this.addMessageToConversation('assistant', botResponse, null, false, sources, debugInfo);
        this.syncChatSession(response.data.chat_session, scopeKey);

      } catch (error) {
        console.error('Error processing audio:', error);
        this.updateMessageById(tempUserId, '(خطا در پردازش فایل صوتی)', false);
      } finally {
        if (this.isCurrentChatScope(scopeKey)) this.isSubmitting = false;
      }
    },
    
    async getBotResponse(userMessage) {
        const child = this.selectedChild;
        const scopeKey = this.chatScopeKey(child);
        const chatSessionId = this.activeChatSessionId;
        this.isSubmitting = true;
        const tempBotId = 'bot-' + Date.now();
        this.addMessageToConversation('assistant', '...', tempBotId, true);

        try {
            const payload = {
              phone_number: localStorage.getItem('loggedInUserPhone'),
              message: userMessage,
              stream: true,
            };
            if (child) payload.child_id = child.id;
            if (chatSessionId) payload.chat_session_id = chatSessionId;

            const response = await fetch(buildApiUrl('/chat'), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
              body: JSON.stringify(payload),
            });
            if (!response.ok) {
              throw new Error(`Chat request failed with status ${response.status}`);
            }

            const contentType = response.headers.get('content-type') || '';
            if (!response.body || !contentType.includes('text/event-stream')) {
              const data = await response.json();
              this.updateMessageById(
                tempBotId,
                data.response || 'متاسفانه پاسخی دریافت نشد.',
                false,
                Array.isArray(data.sources) ? data.sources : [],
                this.buildDebugInfo(data),
              );
              this.syncChatSession(data.chat_session, scopeKey);
              if (data.show_tests && child && this.isCurrentChatScope(scopeKey)) this.shouldHighlightSkills = true;
              return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            let streamedText = '';
            let pendingText = '';
            let streamFinished = false;
            let streamTimer = null;
            let resolveStreamDrain;
            const streamDrain = new Promise(resolve => { resolveStreamDrain = resolve; });
            const streamCharsPerTick = 5;
            const streamTickMs = 30;

            const finishStreamDrain = () => {
              if (resolveStreamDrain) {
                resolveStreamDrain();
                resolveStreamDrain = null;
              }
            };

            const flushStream = () => {
              const nextText = pendingText.slice(0, streamCharsPerTick);
              pendingText = pendingText.slice(nextText.length);
              if (nextText) {
                streamedText += nextText;
                this.updateMessageById(tempBotId, streamedText, false, [], '', true);
              }

              if (pendingText) {
                streamTimer = window.setTimeout(flushStream, streamTickMs);
              } else {
                streamTimer = null;
                if (streamFinished) finishStreamDrain();
              }
            };

            const enqueueStreamText = (text) => {
              pendingText += text;
              if (!streamTimer) flushStream();
            };
            let completedPayload = null;

            const handleEvent = (block) => {
              const lines = block.split(/\r?\n/);
              const eventName = lines.find(line => line.startsWith('event:'))?.slice(6).trim() || 'message';
              const dataLine = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n');
              if (!dataLine) return;
              const data = JSON.parse(dataLine);

              if (eventName === 'chunk') {
                enqueueStreamText(data.text || '');
              } else if (eventName === 'done') {
                completedPayload = data;
                streamFinished = true;
                if (!pendingText && !streamTimer) finishStreamDrain();
                else if (pendingText && !streamTimer) flushStream();
              } else if (eventName === 'error') {
                throw new Error(data.message || 'Streaming chat failed');
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
            if (!completedPayload) throw new Error('Streaming response ended before completion');
            streamFinished = true;
            if (pendingText && !streamTimer) flushStream();
            if (pendingText || streamTimer) await streamDrain;

            this.updateMessageById(
              tempBotId,
              completedPayload.response || streamedText,
              false,
              Array.isArray(completedPayload.sources) ? completedPayload.sources : [],
              this.buildDebugInfo(completedPayload),
              false,
            );
            this.syncChatSession(completedPayload.chat_session, scopeKey);
            if (completedPayload.show_tests && child && this.isCurrentChatScope(scopeKey)) this.shouldHighlightSkills = true;
        } catch (error) {
            console.error("Error getting bot response:", error);
            this.updateMessageById(tempBotId, 'متاسفانه خطایی در ارتباط با سرور رخ داد.', false);
        } finally {
            if (this.isCurrentChatScope(scopeKey)) this.isSubmitting = false;
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
            alert("خطا در پخش صدا.");
            this.isAudioPlaying = false;
        }
    },
    navigateToTest(category) {
      if (!this.selectedChild) {
        alert("برای شروع تست، لطفا ابتدا یک فرزند را انتخاب کنید.");
        return;
      }
      this.shouldHighlightSkills = false;
      this.$router.push({
        name: 'TestPage',
        params: { childId: this.selectedChild.id, skillCategory: category.skillCategory }
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
          await api.delete(`/children/${childId}`);
          if (this.selectedChild && this.selectedChild.id === childId) {
              this.selectedChild = null;
              this.shouldHighlightSkills = false;
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
  width: 100%;
  height: 100dvh; 
  min-height: 100dvh;
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
  min-height: 0;
  overflow: hidden;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-header { display: flex; align-items: center; gap: 10px; margin-bottom: 30px; }
.logo { width: 40px; }
.header-link { text-decoration: none; color: inherit; font-size: 1.2rem; font-weight: bold; }
.close-sidebar-btn { display: none; font-size: 1.5rem; cursor: pointer; margin-right: auto; }

.general-chat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 15px;
  margin-bottom: 12px;
  border: 1px solid transparent;
  border-radius: 12px;
  color: #403348;
  cursor: pointer;
}
.general-chat-item:hover { background-color: rgba(240, 230, 255, 0.5); }
.general-chat-item.active { background-color: #f0e6ff; color: #6A1B9A; font-weight: bold; border-color: #d1b3ff; }

.children-list {
  flex-grow: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-left: 5px;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  touch-action: pan-y;
}
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
.new-chat-button {
  border: 0;
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(106, 27, 154, 0.1);
  color: #6a1b9a;
  font: inherit;
  font-size: 0.72rem;
  cursor: pointer;
  white-space: nowrap;
}
.new-chat-button:hover { background: rgba(106, 27, 154, 0.18); }
.new-chat-button:disabled { opacity: 0.55; cursor: wait; }

.chat-session-list {
  min-height: 0;
  max-height: 190px;
  overflow-y: auto;
  overflow-x: hidden;
  margin: 0 0 12px;
  padding: 10px 4px 0;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  touch-action: pan-y;
}
.chat-session-heading {
  padding: 0 8px 7px;
  color: #76647f;
  font-size: 0.78rem;
}
.chat-session-row { display: flex; align-items: center; gap: 3px; }
.chat-session-item {
  flex: 1;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  border: 0;
  border-radius: 9px;
  padding: 8px;
  background: transparent;
  color: #403348;
  font: inherit;
  font-size: 0.82rem;
  text-align: right;
  cursor: pointer;
}
.chat-session-item:hover,
.chat-session-item.active { background: rgba(240, 230, 255, 0.8); color: #6a1b9a; }
.chat-session-item small { opacity: 0.6; }
.delete-session-button {
  flex: 0 0 auto;
  width: 27px;
  height: 27px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #a26876;
  font-size: 1.15rem;
  line-height: 1;
  cursor: pointer;
}
.delete-session-button:hover { background: #fff0f2; color: #c0392b; }
.delete-session-button:disabled { opacity: 0.5; cursor: wait; }

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
  min-width: 0;
  min-height: 0;
  width: 100%;
  height: 100%;
  padding: 22px 28px 20px;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 16px;
  overflow: hidden;
}

.mobile-header { display: none; }

.conversation-stage,
.bottom-dock {
  width: min(1120px, 100%);
  min-width: 0;
  margin: 0 auto;
}

.conversation-stage {
  min-height: 0;
  display: flex;
  padding: 14px;
  border-radius: 30px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.58);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.chat-area {
  width: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 6px;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  touch-action: pan-y;
}

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

.initial-message {
  align-self: center;
  text-align: center;
  max-width: 560px;
  margin: auto;
  padding: 22px 26px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.54);
  border: 1px solid rgba(255, 255, 255, 0.7);
  color: #57536b;
  box-shadow: 0 16px 35px rgba(100, 80, 137, 0.08);
}

.welcome-copy {
  white-space: pre-line;
  line-height: 2;
}

.message-bubble {
  min-width: 0;
  padding: 18px 20px;
  border-radius: 24px;
  max-width: min(78%, 760px);
  width: fit-content;
  line-height: 1.85;
  position: relative;
  box-shadow: 0 12px 26px rgba(83, 63, 118, 0.08);
  word-break: break-word;
  overflow-wrap: anywhere;
}

.user-message {
  background: linear-gradient(135deg, #f3e9ff, #eadbff);
  align-self: flex-start;
  border-bottom-right-radius: 10px;
  border-bottom-left-radius: 24px;
}

.bot-message {
  background: rgba(255, 255, 255, 0.96);
  align-self: flex-end;
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 24px;
}

.message-bubble.thinking-bubble {
  width: 100%;
  max-width: 100%;
  padding: 14px 0 14px 14px;
  background: transparent;
  box-shadow: none;
  text-align: left;
  align-self: stretch;
}

.play-audio-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  margin-top: 10px;
  display: block;
  opacity: 0.68;
}

.thinking-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 150px;
  padding: 4px 0;
}

.thinking-text {
  display: inline-block;
  color: #c9a9e8;
  font-size: 1.28rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  background: linear-gradient(
    90deg,
    #c9a9e8 0%,
    #c9a9e8 30%,
    #6a1b9a 48%,
    #c9a9e8 66%,
    #c9a9e8 100%
  );
  background-size: 240% 100%;
  background-position: 100% 0;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: thinking-sweep 1.8s ease-in-out infinite;
}

.rich-text.is-streaming {
  position: relative;
  padding-left: 11px;
}

.rich-text.is-streaming::after {
  content: '';
  display: inline-block;
  width: 2px;
  height: 1.05em;
  margin-right: 3px;
  vertical-align: -0.16em;
  border-radius: 999px;
  background: #8e44ad;
  animation: stream-caret 0.9s ease-in-out infinite;
}

@keyframes thinking-sweep {
  0% { background-position: 100% 0; }
  50% { background-position: 0% 0; }
  100% { background-position: 100% 0; }
}

@keyframes stream-caret {
  0%, 100% { opacity: 0.2; transform: scaleY(0.75); }
  50% { opacity: 1; transform: scaleY(1); }
}

.bottom-dock {
  position: relative;
  min-width: 0;
  padding: 14px 14px 12px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(20px);
  box-shadow: 0 22px 55px rgba(74, 53, 110, 0.12);
}

.bottom-dock::before {
  content: '';
  position: absolute;
  inset: 0 auto auto 18px;
  width: 54px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, #6a1b9a, #d4b0ff);
}

.bottom-dock.disabled {
  opacity: 0.88;
}

.bottom-dock.suggested {
  box-shadow: 0 22px 60px rgba(125, 98, 227, 0.2);
  border-color: rgba(125, 98, 227, 0.22);
}

.categories-grid {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  overflow-x: auto;
  padding: 2px 2px 8px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.categories-grid::-webkit-scrollbar { display: none; }

.category-card {
  appearance: none;
  border: 1px solid rgba(98, 75, 133, 0.1);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.72));
  border-radius: 22px;
  width: 94px;
  height: 104px;
  min-width: 94px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  box-shadow: 0 10px 28px var(--card-glow);
  font: inherit;
  color: #231b37;
  flex-direction: column;
  gap: 6px;
  padding: 8px 5px;
  box-sizing: border-box;
}

.category-card:hover:not(:disabled) {
  transform: translateY(-3px);
  border-color: rgba(106, 27, 154, 0.22);
  box-shadow: 0 16px 32px var(--card-glow);
}

.category-card:disabled {
  cursor: not-allowed;
  opacity: 0.56;
  box-shadow: none;
}

.category-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--card-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
}

.category-label {
  font-size: 0.78rem;
  font-weight: 700;
  white-space: normal;
  text-align: center;
  line-height: 1.25;
}

:deep(.message-bubble strong) { font-weight: 800; }
:deep(.message-bubble h4) { margin: 14px 0 6px; color: #6a1b9a; font-size: 1.05em; }
:deep(.message-bubble ul) { margin: 8px 0; padding-right: 22px; }
:deep(.message-bubble li) { margin: 5px 0; }
:deep(.message-bubble a) { color: #0b57d0; text-decoration: underline; }
:deep(.message-bubble code) { background: #f3eef8; padding: 1px 5px; border-radius: 5px; }

.message-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid rgba(93, 67, 127, 0.1);
}
.sources-button {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 1px solid rgba(106, 27, 154, 0.18);
  border-radius: 999px;
  padding: 7px 12px;
  background: linear-gradient(135deg, #fff, #f7efff);
  color: #6a1b9a;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}
.sources-button:hover {
  transform: translateY(-1px);
  background: #f1e3ff;
  box-shadow: 0 8px 18px rgba(106, 27, 154, 0.12);
}
.sources-button-icon { font-size: 1.05rem; line-height: 1; transform: rotate(90deg); }
.sources-count {
  min-width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #6a1b9a;
  color: #fff;
  font-size: 0.68rem;
}

.sources-overlay {
  position: fixed;
  inset: 0;
  z-index: 1100;
  background: rgba(29, 17, 45, 0.28);
  backdrop-filter: blur(4px);
}
.sources-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 1200;
  width: min(440px, 92vw);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(255, 253, 255, 0.97);
  border-left: 1px solid rgba(106, 27, 154, 0.12);
  box-shadow: -20px 0 60px rgba(57, 33, 78, 0.2);
  animation: source-panel-in 0.24s ease-out;
}
@keyframes source-panel-in { from { transform: translateX(24px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
.sources-panel-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 26px 22px;
  color: #2d2037;
  background: radial-gradient(circle at 20% 0%, #f3ddff, transparent 58%), #fff;
  border-bottom: 1px solid rgba(106, 27, 154, 0.1);
}
.sources-eyebrow { color: #8b55a8; font-size: 0.65rem; letter-spacing: 0.18em; font-weight: 900; }
.sources-panel-header h2 { margin: 5px 0 3px; font-size: 1.45rem; }
.sources-panel-header p { margin: 0; color: #7d6c84; font-size: 0.82rem; }
.sources-close {
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  border: 0;
  border-radius: 50%;
  background: #f3e8f8;
  color: #6a1b9a;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
}
.sources-panel-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 18px;
  background: #fbf8fc;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  touch-action: pan-y;
}
.source-detail-card {
  padding: 18px;
  margin-bottom: 14px;
  border: 1px solid rgba(106, 27, 154, 0.1);
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 8px 22px rgba(67, 38, 86, 0.06);
}
.source-card-topline { display: flex; justify-content: space-between; align-items: center; color: #a17bb4; font-size: 0.68rem; font-weight: 900; letter-spacing: 0.08em; }
.source-index { color: #6a1b9a; font-size: 1rem; }
.source-detail-card h3 { margin: 12px 0 8px; color: #2f2437; font-size: 1rem; line-height: 1.7; white-space: normal; overflow-wrap: anywhere; word-break: normal; }
.source-meta { display: flex; align-items: center; justify-content: space-between; gap: 10px; color: #806f87; font-size: 0.78rem; }
.source-meta a { color: #1769aa; text-decoration: none; white-space: nowrap; }
.source-meta a:hover { text-decoration: underline; }
.source-chunk-text { margin: 16px 0 0; padding-top: 14px; border-top: 1px solid #eee7f2; color: #4b4052; font-size: 0.88rem; line-height: 2; white-space: pre-line; }

.composer-shell {
  margin-top: 8px;
}

:deep(.chat-input-area) {
  padding-top: 0;
}

:deep(.chat-box) {
  background: rgba(255, 255, 255, 0.96);
  padding: 12px 18px;
  border: 1px solid rgba(111, 91, 145, 0.12);
  box-shadow: 0 10px 24px rgba(84, 62, 122, 0.09);
}

:deep(.chat-box input) {
  font-family: inherit;
  color: #2b2540;
}

:deep(.send-icon) {
  color: #6A1B9A;
  cursor: pointer;
}

:deep(.mic-button) {
  color: #4b3e64;
}

:deep(.chat-box.disabled) {
  background-color: rgba(245, 243, 249, 0.94);
}

.growth-chart-link {
  padding: 6px 12px;
  border-radius: 10px;
  font-size: 0.8rem;
  margin-right: auto;
  margin-left: 10px;
  white-space: nowrap;
}

.growth-chart-link,
.mobile-chart-btn {
  background-color: #e8dcff;
  color: #5a2f8f;
  text-decoration: none;
  border: 1px solid rgba(106, 27, 154, 0.12);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.growth-chart-link:hover,
.mobile-chart-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(106, 27, 154, 0.12);
}

@media (max-width: 1100px) {
  .main-content {
    padding-inline: 18px;
  }
}

@media (max-width: 900px) {
  .dashboard-wrapper {
    flex-direction: column;
    height: 100dvh;
    min-height: 100dvh;
  }

  .sidebar {
    position: fixed;
    top: 0;
    right: 0;
    height: 100dvh;
    width: min(86vw, 320px);
    max-width: 320px;
    transform: translateX(100%);
    box-shadow: -5px 0 25px rgba(0,0,0,0.15);
    z-index: 1000;
    overscroll-behavior-y: contain;
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .close-sidebar-btn { display: block; }

  .sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.4);
    z-index: 900;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s;
    backdrop-filter: blur(2px);
  }

  .sidebar-overlay.active {
    opacity: 1;
    visibility: visible;
    touch-action: none;
  }

  .main-content {
    padding: 0 0 14px;
    width: 100%;
    height: 100dvh;
    min-height: 0;
    grid-template-rows: auto minmax(0, 1fr) auto;
    gap: 12px;
    min-height: 0;
  }

  .sources-panel {
    top: 7vh;
    right: 0;
    bottom: 0;
    width: 100%;
    border-radius: 24px 24px 0 0;
    border-left: 0;
    box-shadow: 0 -18px 50px rgba(57, 33, 78, 0.22);
    animation: source-modal-in 0.24s ease-out;
  }
  @keyframes source-modal-in { from { transform: translateY(28px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
  .sources-panel-header { padding: 22px 18px 17px; }
  .sources-panel-body { padding: 14px; }
  .source-detail-card { padding: 15px; border-radius: 16px; }

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
    background: none;
    border: none;
    font-size: 1.8rem;
    cursor: pointer;
    color: #555;
    padding: 0;
  }

  .mobile-logo-area {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: bold;
    color: #333;
  }

  .mobile-logo { width: 30px; }
  .mobile-header-spacer { width: 24px; }

  .mobile-chart-btn {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.05rem;
    flex-shrink: 0;
  }

  .conversation-stage,
  .bottom-dock {
    width: calc(100% - 20px);
    max-width: none;
  }

  .conversation-stage {
    padding: 10px;
    border-radius: 24px;
  }

  .chat-area {
    padding: 2px;
    gap: 12px;
  }

  .initial-message {
    max-width: 100%;
    margin-inline: 4px;
    padding: 18px 16px;
  }

  .message-bubble {
    max-width: 96%;
    padding: 12px 13px;
    font-size: 0.95rem;
    line-height: 1.8;
  }

  .bottom-dock {
    padding: 12px 12px calc(14px + env(safe-area-inset-bottom));
    border-radius: 26px;
  }

  .categories-grid {
    justify-content: flex-start;
    gap: 8px;
  }

  .category-card {
    width: 82px;
    height: 96px;
    min-width: 82px;
    border-radius: 18px;
  }

  .category-icon {
    width: 50px;
    height: 50px;
    font-size: 1.55rem;
  }

  .category-label {
    font-size: 0.72rem;
    max-width: 100%;
  }

  .desktop-hint { display: none; }
}

@media (max-width: 480px) {
  .main-content { padding-bottom: calc(8px + env(safe-area-inset-bottom)); gap: 8px; }
  .mobile-header { height: 54px; padding-inline: 10px; }
  .mobile-child-name,
  .mobile-app-name {
    max-width: 45vw;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .conversation-stage { padding: 7px; border-radius: 20px; }
  .bottom-dock { padding: 9px 8px 10px; border-radius: 20px; }
  .category-card { width: 78px; min-width: 78px; height: 90px; padding-inline: 3px; }
  .category-icon { width: 44px; height: 44px; font-size: 1.35rem; border-radius: 13px; }
  .category-label { font-size: 0.67rem; }
  .message-bubble { max-width: 100%; font-size: 0.9rem; }
  .sources-panel { top: 4vh; }
  .sources-panel-header { padding-inline: 14px; }
  .source-meta { align-items: flex-start; flex-direction: column; }
}
</style>
