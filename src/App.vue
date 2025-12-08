<template>
  <router-view />
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
body, html, #app, input, select, button, textarea {
  font-family: 'IRANYekanX', Arial, sans-serif !important;
}

body, html {
  direction: rtl;
  text-align: right;
  margin: 0;
  padding: 0;
  background-color: #f8f9fa; 
}

#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
}
</style>