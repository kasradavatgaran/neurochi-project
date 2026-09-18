const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,
  devServer: {
    proxy: {
      '^/(request-otp|verify-otp|me|users|create-profile|children|chat|tests|games|transcribe-audio|text-to-speech|audio|images|rag)': {
        target: process.env.VUE_APP_API_BASE_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
