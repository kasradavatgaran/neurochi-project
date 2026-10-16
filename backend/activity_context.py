"""Preserve activity facts while sending detailed answers only when relevant."""
import re

SKILL_TERMS = {
    'مهارت های حرکتی درشت': ('درشت','پرید','راه رفت','نشستن','دویدن','خزیدن'),
    'مهارت های حرکتی ریز': ('ریز','ظریف','دست','انگشت','مداد','قیچی'),
    'ارتباطات': ('ارتباط','حرف','گفتار','زبان'),
    'حل مسئله': ('مسئله','مساله','یادگیری','شناخت'),
    'شخصی - اجتماعی': ('اجتماعی','شخصی','استقلال','ارتباط با دیگران'),
}


def compact_activities(tests, games, question):
    text = (question or '').replace('\u200c',' ')
    relevant = {skill for skill,words in SKILL_TERMS.items() if any(word in text for word in words)}
    all_details = any(word in text for word in ('تاریخچه','تست های قبلی','پاسخ های قبلی'))
    if not relevant and any(word in text for word in ('تست','ارزیابی','غربالگری')):
        relevant = set(SKILL_TERMS)
    lines = ['خلاصهٔ همهٔ تست‌های تکمیل‌شده (جدیدترین در ابتدا):']
    latest_seen = set()
    for test in tests:
        skill = test['skill_category']
        lines.append(f"{test['completed_at'][:10]} | {skill} | {test['status']} | {test['score_percentage']}٪")
        if all_details or (skill in relevant and skill not in latest_seen):
            lines.extend(f"  {answer['question']} → {answer['answer']}" for answer in test.get('answers',[]))
        latest_seen.add(skill)
    if not tests:
        lines.append('تست تکمیل‌شده‌ای ثبت نشده است.')
    lines.append('نتایج همهٔ بازی‌های ثبت‌شده:')
    for game in games:
        outcome = 'توانست' if game['result']=='can_do' else 'نتوانست'
        lines.append(f"{game['completed_at'][:10]} | {game['title']} ({game['skill_category']}) | {outcome}")
    if not games:
        lines.append('نتیجه‌ای برای بازی ثبت نشده است.')
    return '\n'.join(lines)
