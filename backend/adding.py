import json
import os

json_dir = 'json_articles'
txt_dir = 'farsi_translations'

if not os.path.exists(json_dir) or not os.path.exists(txt_dir):
    print("خطا: یکی از پوشه‌های json_articles یا farsi_translations یافت نشد.")
else:
    count = 0

    for filename in os.listdir(json_dir):
        if filename.endswith('.json'):
            json_path = os.path.join(json_dir, filename)
            

            txt_filename = filename.replace('.json', '.txt') 
            txt_path = os.path.join(txt_dir, txt_filename)

            if os.path.exists(txt_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        article_url = data.get('mainEntityOfPage')

                    if article_url:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            current_content = f.read()

                        if article_url not in current_content:
                            with open(txt_path, 'a', encoding='utf-8') as f:
                                f.write(f'\n\nلینک مقاله اصلی: {article_url}')
                            print(f"لینک اضافه شد به: {txt_filename}")
                            count += 1
                        else:
                            print(f"لینک از قبل موجود بود در: {txt_filename}")
                    else:
                        print(f"هشدار: فیلد mainEntityOfPage در فایل {filename} پیدا نشد.")

                except Exception as e:
                    print(f"خطا در پردازش فایل {filename}: {e}")
            else:
                print(f"هشدار: فایل متنی متناظر برای {filename} پیدا نشد.")

    print(f"\nعملیات تمام شد. تعداد فایل‌های به‌روزرسانی شده: {count}")