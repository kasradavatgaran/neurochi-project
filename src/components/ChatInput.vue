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

<script>
import MicRecorder from 'mic-recorder-to-mp3';

export default {
  name: 'ChatInput',
  props: {
    isActive: { type: Boolean, default: false },
    isSubmitting: { type: Boolean, default: false },
    placeholder: { type: String, default: 'پیام خود را بنویسید...' }
  },
  data() {
    return {
      userMessage: '',
      recorder: null,
      isRecording: false,
    };
  },
  methods: {
    sendMessage() {
      if (this.userMessage.trim() && this.isActive) {
        this.$emit('send-text', this.userMessage.trim());
        this.userMessage = '';
      }
    },

    initializeRecorder() {
      this.recorder = new MicRecorder({ bitRate: 128 });
    },

    startRecording() {
      if (!this.recorder || this.isRecording || !this.isActive) return;
      
      this.recorder.start().then(() => {
        this.isRecording = true;
      }).catch((error) => {
        console.error('Error starting recording:', error);
        this.isRecording = false;
        alert("لطفا دسترسی به میکروفون را فعال کنید.");
      });
    },

    stopRecording() {
      if (!this.recorder || !this.isRecording) {
        return;
      }
      
      this.recorder.stop().getMp3().then(([, blob]) => {
        this.isRecording = false; 
        
        if (blob.size < 1000) { 
          console.log("Recording too short, ignoring.");
          return;
        }
        this.$emit('send-audio', blob);

      }).catch((e) => {
        console.error('Error stopping or getting mp3:', e);
        this.isRecording = false;
      });
    }
  },
  mounted() {
    this.initializeRecorder();
  }
}
</script>

<style scoped>
.chat-input-area { width: 100%; padding-top: 20px; }
.chat-box { display: flex; align-items: center; min-width: 0; width: 100%; background: #fff; padding: 8px 20px; border-radius: 99px; box-shadow: 0 5px 25px rgba(0,0,0,0.1); }
.chat-box input { flex: 1 1 auto; min-width: 0; border: none; outline: none; background: transparent; font-size: 1rem; text-align: right; padding: 8px; }
.send-icon, .mic-icon { font-size: 1.5rem; color: #999; }
.send-icon { transform: rotate(180deg); }
.chat-box.disabled { background-color: #f5f5f5; cursor: not-allowed; }
.chat-box.disabled input { background-color: transparent; }
.mic-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0 10px;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.recording-indicator {
  color: #ef4444;
  animation: pulse 1.2s infinite ease-in-out;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}

@media (max-width: 600px) {
  .chat-input-area { padding-top: 10px; }
  .chat-box { padding: 7px 10px; }
  .chat-box input { padding: 8px 6px; font-size: 16px; }
  .send-icon, .mic-icon { font-size: 1.3rem; }
  .mic-button { padding: 0 6px; font-size: 1.3rem; }
}
</style>
