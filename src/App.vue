<template>
  <router-view />
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
}

body, html, #app, input, select, button, textarea {
  font-family: 'IRANYekanX', Arial, sans-serif !important;
}

html {
  width: 100%;
  min-width: 0;
  min-height: 100%;
  overflow-x: hidden;
  overflow-y: auto;
}

body, html {
  direction: rtl;
  text-align: right;
  margin: 0;
  padding: 0;
  background-color: #f8f9fa; 
  width: 100%;
  min-width: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  width: 100%;
  min-height: 100dvh;
  overflow-x: hidden;
}

@media (max-width: 900px) {
  html,
  body,
  #app {
    min-height: 100%;
  }

  body {
    min-height: 100dvh;
    -webkit-text-size-adjust: 100%;
  }
}

img,
svg,
video,
canvas {
  max-width: 100%;
}

button,
input,
select,
textarea {
  max-width: 100%;
}
</style>
