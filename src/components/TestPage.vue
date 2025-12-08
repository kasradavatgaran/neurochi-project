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
