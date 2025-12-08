
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
