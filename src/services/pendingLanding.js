const KEY = 'neurochi.pendingLandingQuestion.v1';
export function getPendingQuestion() {
  try {
    const value = JSON.parse(localStorage.getItem(KEY));
    if (!value?.id || !value?.question) return null;
    if (Date.now() - value.createdAt > 86400000) { clearPendingQuestion(); return null; }
    return value;
  } catch { return null; }
}
export function savePendingQuestion(question) {
  const id = crypto.randomUUID ? crypto.randomUUID() : '10000000-1000-4000-8000-100000000000'.replace(/[018]/g, c => (Number(c) ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (Number(c) / 4)))).toString(16));
  const value = { id, question: question.trim(), createdAt: Date.now() };
  localStorage.setItem(KEY, JSON.stringify(value));
  return value;
}
export function bindPendingQuestion(phone) {
  const value = getPendingQuestion();
  if (value && !value.phone) { value.phone = phone; localStorage.setItem(KEY, JSON.stringify(value)); }
}
export function clearPendingQuestion() { localStorage.removeItem(KEY); }
