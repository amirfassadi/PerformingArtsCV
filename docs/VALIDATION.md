# شواهد بررسی نسخه اولیه

تاریخ بررسی: ۲۰۲۶-۱۱-۰۹. محیط محلی ویندوز، Python 3.14 و Django 5.2.19.

## نتیجه

- ۴۳ آزمون خودکار محصول، کنترل دسترسی، فایل، سهمیه، پرداخت و سلامت بکاپ گذشت.
- دو بارگذاری هم‌زمان روی SQLite واقعی برای سهمیه ناکافی رقابت کردند؛ فقط یکی ذخیره شد و فایل اضافی باقی نماند.
- `manage.py check` بدون مسئله و بررسی مهاجرت بدون تغییر ثبت‌نشده بود.
- مسیر واقعی مرورگر با Edge در اندازه دسکتاپ و موبایل بررسی شد: ثبت‌نام دو حساب، ویرایش رزومه، انتشار برای مشترکان، آپلود و نمایش تصویر، بسته بودن صفحه و فایل برای حساب رایگان، باز شدن پس از ثبت اشتراک، جست‌وجو و منتخب‌ها.
- در صفحات بررسی‌شده خطای JavaScript یا پاسخ سرور ۵۰۰ مشاهده نشد و صفحات موبایل بررسی‌شده اسکرول افقی نداشتند.
- snapshot داده آزمایشی شامل دو حساب و یک فایل ساخته و بررسی شد؛ سپس در مسیر جدا بازیابی شد، برنامه روی داده بازیابی‌شده check شد و شمار رزومه‌ها و محتوای فایل تطبیق داده شد.
- بررسی تنظیمات تولید خطای پیکربندی اصلی نداشت؛ دو هشدار HSTS زیردامنه و preload عمداً باقی‌اند و در راهنمای عملیات توضیح داده شده‌اند.

## محدوده اعتبار

پاسخ‌های زرین‌پال در آزمون‌های خودکار شبیه‌سازی شده‌اند. درگاه sandbox واقعی، پرداخت بانکی واقعی، اتصال دو دستگاه، قطع برق، خرابی دیسک و بار عمومی آزمایش نشده‌اند. تصاویر نمونه و حساب‌های مرورگر فقط در محیط موقت ساخته شدند و اطلاعات ورود یا داده شخصی وارد مخزن نشده است.

آزمون مستقل سهمیه هم‌زمان در `scripts/concurrency_smoke.py` و آزمون مرورگر و بازیابی در `scripts/browser_smoke.py` قابل تکرارند. CI آزمون‌های سمت سرور و سهمیه هم‌زمان را اجرا می‌کند؛ آزمون مرورگر محلی و اختیاری است.

## ممیزی MVP دعوتی — ۲۰۲۶-۱۱-۱۰

مبنای کد: `main` در `ab24f0774d91af02528090c225e5bc8a255b2e00`. تعریف پذیرفته‌شده از PR باز #11 خوانده شد. جزئیات وضعیت هر قابلیت و یافته‌های AUD-001 تا AUD-010 در [گزارش ممیزی MVP](MVP-AUDIT.md) است.

محیط: Windows/PowerShell؛ Python 3.14.7 از `.venv` موجود (از نو ساخته نشد)، Django 5.2.19 و Waitress 3.0.2. برای بررسی‌ها از `DATA_ROOT` و `PRIVATE_MEDIA_ROOT` تصادفی و موقت بیرون مخزن، کلید تصادفی موقت، پذیرندگی خالی و sandbox روشن استفاده شد. داده/رسانهٔ معمول پروژه دست‌نخورده ماندند و ریشه‌های موقت پس از اجرا پاک شدند.

| فرمان واقعی | نتیجه |
|---|---|
| `.\.venv\Scripts\python.exe -m pip check` | خروجی `No broken requirements found.`؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py check` | بدون مشکل؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` | `No changes detected`؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py test --verbosity 1` | 43 تست، همگی قبول در 3.281 ثانیه؛ exit 0 |
| `.\.venv\Scripts\python.exe scripts\concurrency_smoke.py` | دو upload همزمان، یکی ذخیره، فایل اضافه‌ای باقی نماند؛ exit 0 |
| `manage.py backup_site`، `manage.py verify_backup` و restore از داده ساختگی | snapshot دو فایلی تأیید شد؛ DB جدا `check` شد و یک پروفایل/فایل 68 بایتی تطبیق داده شد؛ همه exit 0 |
| `.\.venv\Scripts\python.exe scripts\browser_smoke.py` | `ModuleNotFoundError: No module named 'playwright'`؛ exit 1، مرورگر شروع نشد |
| `manage.py check --deploy` با DEBUG خاموش و کلید تصادفی موقت | exit 0؛ فقط `security.W005` و `security.W021` |

علت نصب‌نشدن Playwright 1.64.1: proxyهای محیط با scheme `socks5` بودند و PySocks در `.venv` موجود نبود. `.\.venv\Scripts\python.exe -m pip install --no-input --retries 0 --timeout 8 -r requirements-dev.txt` با proxy فعال خطای `Missing dependencies for SOCKS support` (exit 1) داد. تلاش مستقیم با proxy environment موقتاً حذف‌شده، `.\.venv\Scripts\python.exe -m pip install --no-input --retries 1 --timeout 8 -r requirements-dev.txt`، به timeout HTTPS در `pypi.org/simple/playwright/` (exit 1) رسید. TLS verification غیرفعال نشد. Microsoft Edge محلی موجود بود ولی smoke script پیش از شروع مرورگر به import خطا خورد. فرمان اجرای دوباره پس از فراهم‌شدن دسترسی pip در [گزارش](MVP-AUDIT.md) آمده است.

شناسه پذیرندگی خالی و sandbox روشن صرفاً مقادیر محیط آزمایش بودند. وضعیت VPS، دامنه، سرویس ایمیل، پذیرندگی واقعی و مقصد دوم بکاپ در این ممیزی ارائه یا بررسی نشد؛ پرداخت زنده انجام نشد. بخش تاریخی بالای این فایل حفظ شده و شواهد مرورگر/بازیابی آن به اجرای تازه نسبت داده نمی‌شوند. هیچ معیار تازه‌ای برای تأیید تلفن، تحصیلات/همکاران ساختاریافته، تأیید ایمیل یا استرداد اضافه نشده است.
