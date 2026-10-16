"""Shared Persian retrieval vocabulary, age parsing and query intent.

Canonicalization is one-to-one concept matching inside the index, not a list of
extra search queries. The question sent to the semantic model remains a sentence.
"""
import re
import unicodedata

DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
NUMBERS = dict(zip('صفر یک دو سه چهار پنج شش هفت هشت نه ده یازده دوازده سیزده چهارده پانزده شانزده هفده هجده نوزده بیست سی چهل پنجاه شصت'.split(),
                  list(range(21)) + [30,40,50,60]))

STOP = set('از با به برای در را رو که و یا این آن من ما شما او چی چیه چیست چه چطور چگونه چقدر چند کدوم کدام چرا آیا ایا کنم کنه کنید کردن می باشد بوده بشه بشود است هست هستم هستند داره دارد دارم دارند داشته بود شد شده شدن شود بشه بده بدهم بدم داده بدیم کنیم کردن کنیم توانم تواند میتونم میتونه بتوانم میتوانم میتواند باید لازم لازمه نیاز مناسبه مناسب خوب خوبه بهتر راحت راحتتر بیشتر کمتر خیلی هی دیگه دیگر قبلا قبل الان وقت وقتی همچنین لطفا کودک کودکم کودکان بچه بچم بچم بچهام نوزاد نوزادم فرزند فرزندم دختر دخترم پسر پسرم کوچولو کوچولوم کوچولوی ماه ماهه ماهگی سال ساله سالگی روز روزه روزگی هفته هفتهگی سن امروز سوال سؤال پرسش درباره مورد کمک راه روش انجام تقویت مراقبت راهنمایی شروع کردن چنده چقدره هستن مثلا آیا ایا ای ام اش ات هم هر باهاش بابت ممنون مرسی سلام درود خوبی چطوری'.split())
STOP |= {'نمی','نمیشه','نیست','نداره','دارد','مهم','کافی','خودم','خودش','براش','بعدش','بهم','نشون','بدیم','کنیم','ربط','یعنی','طبیعیه','طبیعی','لازمه','دیگران','دیگه','how','what','when','where','why','do','does','is','are','the','a','an','for','to','of','and','my','your','please','need','should','much','child','children','baby','babies','kids','kid','old','month','months','year','years','week','weeks','day','days'}
STOP |= {'ولی','اما','پس','بوده','بودن','شده','میشه','هایی','چیزی','کاری','کار','ضرورت','ضروری','پیشنهاد','نشان','بدهیم','هنگام','موقع','ادامه','راهکار','بیش','کم','برخورد','رفتار','کرده','ریخته','میخورده'}
STOP |= {'تر','کی','بتونه','بررسی','مراقبتی','کمکی','کمکش','هنوز','محسوب','سالشه','ماهشه','میریزه','ریزه','اگه','اگر','انجامش','وضعیت','اقدام','اقدامی','اقدامات','تمایل','هاش','ها','های','هایش','هاشان'}
STOP |= {'باشه','باشند','کرد','کردم','کردی','کردید','اول','دوم','سوم','چهارم','پنجم','ششم','هفتم','هشتم','نهم','دهم','دقیق','دقیقا'}
STOP |= {'همه','چیز','تو'}
CANON = {
    **dict.fromkeys('بخوابد بخوابم بخوابن خوابید خوابیده خوابیدن خواباندن خواباند میخوابد میخوابه میخوابم میخوابید بخوابه خوابش خوابم sleeps sleep sleeping bedtime'.split(), 'خواب'),
    **dict.fromkeys('بپره بپرد بپرند میپرد پریدن پرید پریده میپره بپر jumping jump'.split(), 'پرش'),
    **dict.fromkeys('حرکت حرکات حرکتی'.split(),'حرکتی'),
    **dict.fromkeys('خوره خورد خوردن بخوره بخورد میخوره میخورد خوردنش خوردن eating eat'.split(),'خوردن'),
    **dict.fromkeys('دندون دندان دندونش دندانش teething teeth'.split(),'دندان'),
    **dict.fromkeys('بره برود بروند رفتن میره'.split(),'رفتن'),
    **dict.fromkeys('خروپف خرخر snoring'.split(),'خروپف'),
    **dict.fromkeys('اگزما اگزمای eczema'.split(),'اگزما'),
    **dict.fromkeys('یبوست constipation'.split(),'یبوست'),
    **dict.fromkeys('اسهال diarrhea diarrhoea'.split(),'اسهال'),
    **dict.fromkeys('چرت چرتها چرتش چرتهایش چرتهاش nap naps napping'.split(),'چرت'),
    **dict.fromkeys('نمیتونه نمیتواند نتواند نتوانستن'.split(),'ناتوانی'),
    **dict.fromkeys('میترسه ترسیده ترسیدن afraid fear fears'.split(),'ترس'),
    **dict.fromkeys('گریه crying cry'.split(),'گریه'),
    **dict.fromkeys('غذا غذای غذاشو غذایش غذاها food foods'.split(),'غذا'),
    **dict.fromkeys('بازی بازیها بازیهایی بازیهای game games play'.split(),'بازی'),
    **dict.fromkeys('گرفتن میگیرد میگیره گیرد گیره'.split(),'گرفتن'),
    **dict.fromkeys('سردرد سردردش'.split(),'سردرد'),
    **dict.fromkeys('خوابه خوابد خوابن'.split(),'خواب'),
    **dict.fromkeys('میخواد میخواهد خواستن بخواهد'.split(),'خواستن'),
    **dict.fromkeys('دماغ بینی nose'.split(),'بینی'),
    **dict.fromkeys('کولیک کولیکه colic'.split(),'کولیک'),
    **dict.fromkeys('استفراغ vomiting vomit'.split(),'استفراغ'),
    **dict.fromkeys('میترسد میترسه ترسیدن ترس'.split(),'ترس'),
    **dict.fromkeys('گفتار حرفزدن speech language talking talk'.split(),'گفتار'),
    **dict.fromkeys('گفت گه میگفت میگفتن صحبت speaking'.split(),'گفتار'),
    **dict.fromkeys('مهد مهدکودک daycare preschool'.split(),'مهدکودک'),
    **dict.fromkeys('spoon spoons'.split(),'قاشق'),
    **dict.fromkeys('دهن دهان mouth mouthing'.split(),'دهان'),
    **dict.fromkeys('جیغ فریاد جیغزدن فریادکشیدن scream screaming shout shouting'.split(),'جیغ'),
    **dict.fromkeys('افتد افتادن میافتد'.split(),'افتادن'),
    **dict.fromkeys('پرت پرتاب throw throws throwing'.split(),'پرتاب'),
    **dict.fromkeys('کوتاه short'.split(),'کوتاه'),
    **dict.fromkeys('نترسه نترسد میترسد میترسه ترسیدن ترس scared'.split(),'ترس'),
    **dict.fromkeys('میزان مقدار چقدر چقدره'.split(),'مقدار'),
    **dict.fromkeys('آب water'.split(),'اب'),
    **dict.fromkeys('safety safe'.split(),'ایمنی'),
}
PHRASES = [
    (r'\bthrow(?:s|ing)?\s+up\b', 'استفراغ'),
    (r'(?:جیغ|فریاد)\s+(?:می\s*)?(?:کشد|کشید|کشیدن|زند|زدن|زنه)', 'جیغ'),
    (r'پرسشنامه\s+سنین\s+و\s+مراحل(?:\s+رشد)?', 'ایاسکیو'),
    (r'برنامه(?:\s+ی)?\s+روزانه|روال(?:\s+های)?\s+روزانه|(?:daily\s+)?routines?|روتین(?:\s+ها)?', 'روالروزانه'),
    (r'خواب(?:\s+های)?\s+کوتاه(?:\s+روزانه)?', 'چرت'),
    (r'دور\s+شدن(?:م|\s+والد|\s+مادر)|separation|جدایی', 'جدایی'),
    (r'چهار\s+دست\s+و\s+پا|سینه\s+خیز|crawl(?:ing)?', 'چهاردستوپا'),
    (r'راه\s+(?:نمی\s*)?(?:رفتن|رود|ره|میره|می\s*رود)|\bwalk(?:ing|s|ed)?\b', 'راهرفتن'),
    (r'ای\s*اس\s*کیو|\basq\b', 'ایاسکیو'),
    (r'بی\s*ال\s*دبلیو|\bblw\b|baby[\s-]*led[\s-]*weaning', 'بیالدبلیو'),
    (r'حل\s+مساله|حل\s+مسئله|problem[\s-]*solving', 'حلمسئله'),
    (r'شب\s*ادراری|bed[\s-]*wetting', 'شبادراری'),
    (r'tummy[\s-]*time|تامی\s*تایم|(?:زمان|تمرین)\s+(?:قرار\s*گرفتن\s+)?(?:بر\s+)?روی\s+شکم', 'تامیتایم'),
    (r'شیر\s*خشک|formula', 'شیرخشک'),
    (r'fine[\s-]*motor|حرکات?\s+(?:ظریف|ریز)|مهارت(?:\s+های)?\s+حرکتی\s+(?:ظریف|ریز)', 'حرکتیظریف'),
    (r'gross[\s-]*motor|حرکات?\s+درشت|مهارت(?:\s+های)?\s+حرکتی\s+درشت', 'حرکتیدرشت'),
    (r'wake[\s-]*windows?|پنجره(?:\s+های)?\s+بیداری', 'پنجرهبیداری'),
    (r'مدت\s+(?:زمان\s+)?(?:مناسب\s+)?(?:برای\s+)?بیداری', 'پنجرهبیداری'),
    (r'(?:بینی|دماغ)\s+(?:(?:اش|بچه|کودک|نوزاد)\s+)?گرفته|گرفتگی\s*(?:بینی|دماغ)|nasal\s+congestion|stuffy\s+nose', 'گرفتگیبینی'),
    (r'خواب(?:ش)?\s+به\s+هم\s+ریخته|sleep\s+regression|رگرسیون\s+خواب|پسرفت\s+خواب', 'اختلالخواب'),
    (r'بالا\s+اورد(?:ن|ه)?', 'استفراغ'),
    (r'شیر\s+مادر|breast[\s-]*feeding|breast\s*milk', 'شیردهی'),
    (r'زبان\s+و\s+گفتار|گفتار\s+و\s+زبان', 'گفتار'),
]

# Specific subjects must not disappear behind an age or a generic word such as
# "care". These are exact concept aliases, not instructions to expand a query.
TOPIC_ANCHORS = set('اگزما یبوست اسهال خروپف کولیک عسل کره قاشق واکر واکسن ناخن خفگی تب سرفه رفلاکس مدفوع بالش استفراغ بارداری افسردگی حلمسئله ایاسکیو بیالدبلیو تامیتایم پنجرهبیداری حرکتیظریف حرکتیدرشت چهاردستوپا راهرفتن شبادراری گاز پریدن پرش گفتار حافظه گرفتگیبینی جدایی مهدکودک روالروزانه دهان جیغ پرتاب'.split())


def topic_anchors(text):
    return set(tokens(text)) & TOPIC_ANCHORS


def persian_acronyms(text):
    # One exact noun phrase, not a synonym/keyword expansion. The official
    # Persian name already occurs in the NHS article and is better understood
    # semantically than the phonetic spelling of three English letters.
    return re.sub(r'(?:پرسشنامه\s+|تست\s+|آزمون\s+)?(?:\bASQ\b|ای[\s\u200c-]*اس[\s\u200c-]*کیو)',
                  'پرسشنامه سنین و مراحل رشد',str(text or ''),flags=re.I)


def normalize(text):
    text = str(text or '').lower().translate(DIGITS).replace('ي','ی').replace('ك','ک').replace('آ','ا').replace('ۀ','ه').replace('\u200c',' ')
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[\u060c\u061b\u061f\u066a-\u066d]', ' ', text)
    text = re.sub(r'[^\w\u0600-\u06ff\s]', ' ',text)
    return re.sub(r'\s+',' ',text).strip()


def tokens(text):
    text = normalize(text)
    for pattern, canonical in PHRASES:
        text = re.sub(pattern, canonical, text)
    result=[]
    for token in text.split():
        if token in STOP or token in NUMBERS or token.isdigit(): continue
        if token.endswith('م') and token[:-1] in STOP: continue
        if token.endswith('ش') and token[:-1] in CANON: token=token[:-1]
        if token.startswith('می') and token[2:] in CANON: token=token[2:]
        if token.startswith('نمی') and token[3:] in CANON: token=token[3:]
        for suffix in ('هایشان','هاشان','هایش','هاش','هایی','های','ها','ام','مان','تان','شان'):
            if token.endswith(suffix) and len(token)-len(suffix)>2:
                token=token[:-len(suffix)];break
        # Persian ezafe after a vowel: اگزمای -> اگزما. Do not mutilate بیداری.
        if token.endswith(('ای','وی')) and len(token)>3: token=token[:-1]
        token=CANON.get(token,token)
        if len(token)>1 and not token.isdigit() and token not in NUMBERS and token not in STOP:
            result.append(token)
    return result


def age_text(text):
    text=str(text or '').lower().translate(DIGITS).replace('ي','ی').replace('ك','ک').replace('\u200c',' ')
    text=re.sub(r'(\d+)\s+([13])[_/]4',lambda m:str(float(m[1])+int(m[2])/4),text)
    text=re.sub(r'(\d+)\s+1[_/]2',lambda m:str(float(m[1])+.5),text).replace('_',' ')
    for fraction, decimal in [('¼','.25'),('½','.5'),('¾','.75')]:
        text=re.sub(r'(\d+)\s*'+fraction,lambda m:m[1]+decimal,text)
    for word,number in NUMBERS.items():
        text=re.sub(r'\b'+word+r'\s+و\s+نیم\s+(سال|ماه)',str(number+.5)+r' \1',text)
        text=re.sub(r'\b'+word+r'\s+(سال|ماه)(?:ه)?\s+و\s+نیم',str(number+.5)+r' \1',text)
    # Compound written numbers such as بیست و چهار ماهه.
    for tens in ('بیست','سی','چهل','پنجاه','شصت'):
        for unit in list(NUMBERS)[1:10]:
            text=text.replace(f'{tens} و {unit}', str(NUMBERS[tens]+NUMBERS[unit]))
    for word, number in sorted(NUMBERS.items(),key=lambda item:-len(item[0])):
        text=re.sub(r'\b'+word+r'(?=\s+(?:ماه|سال|روز|هفته))',str(number),text)
    return re.sub(r'\s+',' ',text)


UNIT = r'(ماه(?:ه|گی|شه)?|months?(?:[\s-]*old)?|mo\.?|سال(?:ه|گی|شه)?|years?(?:[\s-]*old)?|روز(?:ه|گی)?|days?(?:[\s-]*old)?|هفته(?:ای|گی|ه)?|weeks?(?:[\s-]*old)?)'
AGE = re.compile(r'(?<!\d)(\d+(?:\.\d+)?)[\s-]*'+UNIT)
RANGE = re.compile(r'(?<!\d)(\d+(?:\.\d+)?)[\s-]*(?:تا|to|–|—|-)[\s-]*(\d+(?:\.\d+)?)[\s-]*'+UNIT)


def unit_months(number,unit):
    if unit.startswith(('سال','year')): return float(number)*12
    if unit.startswith(('روز','day')): return float(number)/30.4375
    if unit.startswith(('هفته','week')): return float(number)*7/30.4375
    return float(number)


def document_age_ranges(metadata):
    # Prefer translated title, but legacy titles often omit age. Original file
    # names keep explicit English age ranges, including fractional years.
    text=age_text(' '.join(str(metadata.get(k) or '') for k in ('title','source_file')))
    ranges=[]
    for match in RANGE.finditer(text):
        low,high=unit_months(match[1],match[3]),unit_months(match[2],match[3])
        # "13–18 months" includes month 18, not only the instant it starts.
        width=(2.99 if '.' in match[2] else 11.99) if match[3].startswith(('سال','year')) else .99 if match[3].startswith(('ماه','month')) else 0
        if low<=high: ranges.append((low,high+width))
    if ranges: return ranges
    for match in AGE.finditer(text):
        value=unit_months(match[1],match[2])
        width=(2.99 if '.' in match[1] else 11.99) if match[2].startswith(('سال','year')) else 0.99 if 'month' in match[2] or match[2].startswith('ماه') else 0.03
        ranges.append((value,value+width))
    if ranges: return ranges
    url=str(metadata.get('url') or '').lower()
    if re.search(r'preschool|پیش دبستان',text+' '+url): return [(36,72)]
    if re.search(r'kindergart',text+' '+url): return [(60,84)]
    if re.search(r'newborn|تازه متولد',text) and not re.search(r'and babies|و نوزادان|and toddler',text): return [(0,3)]
    if re.search(r'toddler|نوپا',text): return [(12,36)] if not re.search(r'bab(?:y|ies)|نوزاد',text) else [(0,36)]
    if '/baby/' in url or re.search(r'\bbab(?:y|ies)\b|نوزاد',text): return [(0,36)]
    return []


def explicit_age_days(query):
    text=age_text(query)
    matches=[m for m in AGE.finditer(text) if not re.search(r'(?:زیر|کمتر از|بیشتر از|قبل از|under|over)\s*$',text[:m.start()])]
    if not matches: return None
    # The latest stated age wins in "my child is 2, but I ask about a 6-month-old".
    match=matches[-1]
    return int(unit_months(match[1],match[2])*30.4375)


def query_scope(query):
    text=normalize(query)
    if re.search(r'باردار|بارداری|pregnan',text) and not re.search(r'نارس|هنگام تولد|سن اصلاح',text): return 'pregnancy'
    if re.search(r'برای خودم|خوابم|افسردگی بعد از زایمان|من موقع شیر|به خودم|من مادر',text): return 'parent'
    return 'child'


def uses_child_age(query):
    """A tool definition is not a developmental assessment of this child."""
    text=normalize(query)
    if query_scope(query)!='child': return False
    if explicit_age_days(query) is not None: return True
    if topic_anchors(query) & {'ایاسکیو'} and re.search(r'چیه|چیست|چه چیزی|تشخیص قطعی|غربال',text): return False
    return True


def skip_retrieval(query):
    text=normalize(query)
    if not text: return 'empty'
    # These replies are interpreted from chat history, not from an article that
    # happens to contain "yes" or "OK". Do not suppress a substantive question.
    if re.fullmatch(r'بله|اره|خیر|نه|باشه|اوکی|اها|متوجه شدم|yes|no|ok',text): return 'acknowledgement'
    if re.search(r'نوروچی|نوروجی',text) and re.search(r'حذف|گفتگو|چت|ثبت نام|ورود|امکانات|استفاده|کار با',text): return 'product'
    chat_operation=re.search(r'چت|گفتگو',text) and re.search(r'حذف|پاک|جدید|سشن',text)
    outside_app=re.search(r'تلگرام|واتساپ|واتس اپ|اینستاگرام|telegram|whatsapp|instagram|با (?:کودک|بچه|فرزند|همسر|دختر|پسر)',text)
    if chat_operation and not outside_app: return 'product'
    if re.search(r'اخرین|آخرین|قبلی|ثبت شده|ثبت کردم|دیروز|کامل کرده|انجام داده|انجام دادم',text) and re.search(r'تست|بازی|قد|وزن|نمره|نتیجه',text) and not re.search(r'تمرین|تقویت|توصیه|تفسیر|چگونه|چطور|کمک',text): return 'personal_record'
    if re.search(r'کلید\s*(?:api|ای پی ای)|دستورهای قبلی|system prompt|پرامپت سیستم',text): return 'control_request'
    if re.search(r'قیمت دلار|قیمت طلا|نرخ ارز|تابع پایتون|کد پایتون|لپ تاپ|وای فای',text) and not re.search(r'کودک|بچه|نوزاد|فرزند',text): return 'off_domain'
    if not tokens(text) or set(tokens(text)) <= {'سلام','خوبی','ممنون','خوب','بابت'}: return 'social'
    return ''


def needs_history(query):
    text=normalize(query)
    if re.search(r'(?:سوال|سؤال|موضوع) جدید',text): return False
    if explicit_age_days(query) is not None and not tokens(text): return True
    return bool(re.search(r'این|اون|براش|بعدش|انجامش|مدتش|چرت.*چی|ماهگی چطور',text) and len(tokens(text))<=4)


def document_body(doc):
    text=doc.page_content
    if text.startswith('موضوع مقاله:') and '\n\n' in text: return text.split('\n\n',1)[1]
    return text
