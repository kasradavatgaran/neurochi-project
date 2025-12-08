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
