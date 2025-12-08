<template>
  <div class="chat-input-area">
    <div class="chat-box" :class="{ disabled: !isActive || isSubmitting }">
      <button 
        @mousedown="startRecording"
        @mouseup="stopRecording"
        @touchstart.prevent="startRecording"
        @touchend.prevent="stopRecording"
        class="mic-button" 
        :disabled="!isActive || isSubmitting"
      >
        <span v-if="!isRecording">🎙️</span>
        <span v-else class="recording-indicator">🛑</span>
      </button>
      
      <input 
        type="text" 
        v-model="userMessage"
        :placeholder="placeholder" 
        :disabled="!isActive || isSubmitting"
        @keyup.enter="sendMessage"
      >
      <span class="send-icon" @click="sendMessage">➤</span>
    </div>
  </div>
</template>
