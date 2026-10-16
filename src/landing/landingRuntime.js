import { savePendingQuestion } from '@/services/pendingLanding';

export function setupLanding(root, signIn) {
  const question = root.querySelector('#question');
  const form = root.querySelector('#question-form');
  const removers = [];
  const on = (target, event, handler) => {
    target.addEventListener(event, handler);
    removers.push(() => target.removeEventListener(event, handler));
  };
  function focusChat(text) {
    if (text) question.value = text;
    root.querySelector('#chat').scrollIntoView({ behavior: 'smooth', block: 'center' });
    question.focus({ preventScroll: true });
  }
  root.querySelectorAll('[data-prompt]').forEach(button => on(button, 'click', () => focusChat(button.dataset.prompt)));
  root.querySelectorAll('[data-focus]').forEach(button => on(button, 'click', () => focusChat()));
  root.querySelectorAll('[data-faq]').forEach(button => on(button, 'click', () => root.querySelector('#faq-modal').showModal()));
  root.querySelectorAll('[data-signup]').forEach(button => on(button, 'click', signIn));
  root.querySelectorAll('dialog').forEach(dialog => {
    dialog.querySelectorAll('.close,.close-action').forEach(button => on(button, 'click', () => dialog.close()));
    on(dialog, 'click', event => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });
  });
  on(form, 'submit', event => {
    event.preventDefault();
    const value = question.value.trim();
    if (!value) { question.focus(); return; }
    try { savePendingQuestion(value); }
    catch { question.setCustomValidity('برای ثبت سؤال، ذخیره‌سازی مرورگر را فعال کنید.'); question.reportValidity(); return; }
    if (localStorage.getItem('loggedInUserPhone')) { signIn(); return; }
    root.querySelector('#response').hidden = false;
    root.querySelector('#user-message').textContent = value;
    root.querySelector('#typing').hidden = true;
    root.querySelector('#answer-lock').hidden = false;
    root.querySelector('#answer-lock').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
  on(question, 'keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); form.requestSubmit(); }
  });
  const prompts = ['می‌خوام غربالگری ASQ رو برای کودکم شروع کنم', 'آیا رشد فرزند من در سن ۲۳ ماهگی نرمال هست؟', 'چندتا بازی می‌خوام که بتونم راه رفتن فرزندم رو تقویت کنم'];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let timer, index = 0, characters = 0, erasing = false, stopped = false;
  function stop() { stopped = true; clearTimeout(timer); question.placeholder = ''; question.setCustomValidity(''); }
  function animate() {
    if (stopped || document.activeElement === question || question.value) return;
    const text = prompts[index];
    characters += erasing ? -1 : 1;
    question.placeholder = text.slice(0, characters);
    let delay = erasing ? 28 : 65;
    if (!erasing && characters === text.length) { erasing = true; delay = 1900; }
    else if (erasing && characters === 0) { erasing = false; index = (index + 1) % prompts.length; delay = 450; }
    timer = setTimeout(animate, delay);
  }
  function resume() {
    if (question.value.trim()) return;
    clearTimeout(timer); stopped = false; characters = 0; erasing = false;
    if (reducedMotion.matches) question.placeholder = prompts[index];
    else { question.placeholder = ''; timer = setTimeout(animate, 450); }
  }
  on(question, 'focus', stop); on(question, 'pointerdown', stop); on(question, 'input', stop); on(question, 'blur', resume);
  on(reducedMotion, 'change', resume);
  resume();
  return () => { clearTimeout(timer); removers.forEach(remove => remove()); };
}
