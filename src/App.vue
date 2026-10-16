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
input:not([type="checkbox"]):not([type="radio"]):not([type="file"]), select, textarea {
  min-width: 0;
  min-height: 44px;
}

/* The date picker is shared by both child forms. Its fixed-width, vertically
   centered dialog must still fit narrow phones and short/keyboard viewports. */
.vpd-input-group input { min-width: 0; min-height: 44px; }
.vpd-input-group label { min-width: 44px; }
.vpd-wrapper { overflow-y: auto; -webkit-overflow-scrolling: touch; touch-action: pan-y; }
.vpd-wrapper .vpd-container { max-width: calc(100% - 24px); }
.vpd-wrapper .vpd-content { max-width: 100%; max-height: calc(100dvh - 24px); overflow-y: auto; overflow-x: hidden; }
.vpd-addon-list { -webkit-overflow-scrolling: touch; touch-action: pan-y; }
.vpd-wrapper .vpd-day, .vpd-wrapper .vpd-weekday { width: calc(100% / 7); }
.vpd-wrapper .vpd-week { padding-inline: 18px; }
.vpd-wrapper .vpd-days { width: 100%; }
.vpd-wrapper .vpd-day-effect { left: 50%; margin-left: -18px; }
.vpd-wrapper .vpd-actions button { min-height: 44px; }
@media (max-width: 360px) {
  .vpd-wrapper .vpd-days, .vpd-wrapper .vpd-week { padding-inline: 8px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; animation-duration: .01ms !important; transition-duration: .01ms !important; }
}
</style>
