<template>
  <main class="history-page">
    <header><router-link to="/dashboard">← بازگشت به گفتگو</router-link><h1>تاریخچهٔ تست‌های {{ childName }}</h1></header>
    <p v-if="loading" role="status">در حال دریافت تاریخچه…</p>
    <p v-else-if="error" class="error" role="alert">{{ error }} <button @click="loadHistory">تلاش دوباره</button></p>
    <p v-else-if="!tests.length" class="empty">هنوز تستی برای این فرزند ثبت نشده است.</p>
    <div v-else class="history-table">
      <table><thead><tr><th>تاریخ شروع تست</th><th>دسته‌بندی تست</th><th>نتیجهٔ تست</th></tr></thead>
        <tbody><tr v-for="test in tests" :key="test.id">
          <td>{{ formatDate(test.started_at) }}</td><td>{{ test.skill_category }}</td>
          <td><button v-if="test.is_completed" class="result-button" @click="showResult(test)" :disabled="detailLoading" :class="test.status_color">مشاهدهٔ نتیجه</button><span v-else>ناتمام</span></td>
        </tr></tbody>
      </table>
      <button v-if="tests.length < total" class="more" @click="loadHistory(true)" :disabled="loadingMore">{{ loadingMore ? 'در حال دریافت…' : 'تست‌های بیشتر' }}</button>
    </div>
    <p v-if="detailError" class="error" role="alert">{{ detailError }}</p>
    <dialog ref="resultDialog" class="result-dialog" @click="closeBackdrop">
      <template v-if="result">
        <button class="close" aria-label="بستن نتیجه" @click="$refs.resultDialog.close()">×</button>
        <h2>نتیجهٔ {{ result.skill_category }}</h2>
        <p>{{ formatDate(result.completed_at || result.started_at) }}</p>
        <div class="score" :class="result.status_color"><strong>{{ result.status }}</strong><span>{{ result.score }} از {{ result.max_score }}</span></div>
        <p class="suggestion">{{ result.suggestion }}</p>
        <details><summary>پاسخ‌های ثبت‌شدهٔ تست</summary><ul><li v-for="(answer, index) in result.answers" :key="index"><p>{{ answer.question }}</p><strong>{{ answer.answer }}</strong></li></ul></details>
        <section v-if="result.games.length"><h3>بازی‌های انجام‌شده</h3><div class="game-grid">
          <article v-for="game in result.games" :key="game.id" class="game-card">
            <img v-if="game.image_url" :src="toApiUrl(game.image_url)" :alt="game.title" loading="lazy">
            <h4>{{ game.title }}</h4><p>{{ game.response === 'can_do' ? 'توانست انجام دهد' : 'هنوز نتوانست انجام دهد' }}</p>
            <span class="played-check" aria-label="انجام شده">✓</span>
          </article>
        </div></section>
      </template>
    </dialog>
  </main>
</template>
<script>
import api, { toApiUrl } from '@/services/api';
export default {
  name: 'TestHistoryPage',
  props: { childId: { type: [String, Number], required: true } },
  data: () => ({ tests: [], childName: '', total: 0, loading: true, loadingMore: false, error: '', result: null, detailError: '', detailLoading: false }),
  methods: {
    toApiUrl,
    formatDate(value) { return value ? new Intl.DateTimeFormat('fa-IR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value.endsWith('Z') ? value : `${value}Z`)) : '—'; },
    async loadHistory(more = false) {
      // Click events are not pagination requests.
      more = more === true;
      this.error = '';
      if (more) this.loadingMore = true; else this.loading = true;
      try {
        const { data } = await api.get(`/children/${this.childId}/test-history`, { params: { phone_number: localStorage.getItem('loggedInUserPhone'), offset: more ? this.tests.length : 0 } });
        this.tests = more ? [...this.tests, ...data.tests] : data.tests;
        this.childName = data.child_name; this.total = data.total;
      } catch { this.error = 'دریافت تاریخچه با مشکل روبه‌رو شد.'; }
      finally { this.loading = false; this.loadingMore = false; }
    },
    async showResult(test) {
      this.detailError = ''; this.detailLoading = true;
      try {
        const { data } = await api.get(`/children/${this.childId}/test-history/${test.id}`, { params: { phone_number: localStorage.getItem('loggedInUserPhone') } });
        this.result = data;
        await this.$nextTick(); this.$refs.resultDialog.showModal();
      } catch { this.detailError = 'دریافت نتیجه با مشکل روبه‌رو شد؛ دوباره تلاش کنید.'; }
      finally { this.detailLoading = false; }
    },
    closeBackdrop(event) { if (event.target === this.$refs.resultDialog) { const r = event.target.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) event.target.close(); } },
  },
  mounted() { this.loadHistory(); },
};
</script>
<style scoped>
.history-page { min-height: 100dvh; background: #f8f3fc; padding: 32px max(16px, calc((100vw - 1000px) / 2)) calc(32px + env(safe-area-inset-bottom)); color: #39234e; }
header { margin-bottom: 28px; } header a { color: #6a1b9a; } h1 { font-size: clamp(1.3rem, 3vw, 2rem); }
.history-table { background: white; border-radius: 18px; padding: 12px; overflow-x: auto; } table { width: 100%; border-collapse: collapse; } th, td { padding: 16px 10px; text-align: right; border-bottom: 1px solid #eee5f4; }
button { font: inherit; cursor: pointer; } .result-button, .more { padding: 9px 12px; border: 1px solid #e6d9ef; border-radius: 9px; color: #6a1b9a; background: #f5ecfc; } button:disabled { opacity: .5; cursor: wait; }
.more { display: block; margin: 20px auto 5px; } .error { color: #ae3043; } .empty { background: white; padding: 25px; border-radius: 16px; }
.result-dialog { width: min(700px, calc(100% - 24px)); max-height: calc(100dvh - 40px); overflow-y: auto; -webkit-overflow-scrolling: touch; touch-action: pan-y; border: 1px solid #e6d9ef; border-radius: 20px; padding: 30px; color: #39234e; }
.result-dialog::backdrop { background: #30203570; } .close { float: left; min-width: 44px; min-height: 44px; border: 0; background: transparent; font-size: 28px; }
.score { display: flex; justify-content: space-between; padding: 18px; border-radius: 12px; background: #f4eafb; } .score.green { background: #e7f6ea; color: #26623a; } .score.blue { background: #e6effb; color: #285488; } .score.yellow { background: #fff4d5; color: #76580a; } .score.red { background: #fce5e8; color: #922f42; }
.suggestion, details { line-height: 2; } details li { margin-bottom: 15px; } details li p { margin-bottom: 0; }
.game-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; } .game-card { position: relative; border: 1px solid #e6d9ef; border-radius: 14px; padding: 14px 14px 30px; } .game-card img { width: 100%; height: 120px; object-fit: contain; } .game-card h4 { margin: 10px 0; } .game-card p { font-size: .85rem; }
.played-check { position: absolute; bottom: 8px; right: 12px; border-radius: 50%; background: #238347; color: white; width: 23px; height: 23px; text-align: center; }
@media (max-width: 480px) { .history-page { padding-top: 20px; } th, td { padding: 12px 5px; font-size: .8rem; } .result-button { padding: 8px 6px; } .result-dialog { padding: 22px 16px; } }
</style>
