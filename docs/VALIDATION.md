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

## اجرای تکمیلی ممیزی issue #3 — ۲۰۲۶-۱۱-۱۰

این ثبت تکمیلی، اجرای تازه روی همان کد `main` در `ab24f0774d91af02528090c225e5bc8a255b2e00` است؛ نتایج بخش قبلی این فایل به‌عنوان تاریخچه نگه داشته شده‌اند. Windows/PowerShell؛ Python 3.14.7، Django 5.2.19 و Waitress 3.0.2 از `.venv` موجود مخزن استفاده شدند. `DATA_ROOT` و `PRIVATE_MEDIA_ROOT` برای اجرای Django به مسیر تصادفی موقت بیرون مخزن تنظیم و در پایان پاک شدند. کلید موقت تصادفی، پذیرندگی خالی و sandbox روشن بودند؛ داده و رسانه اصلی پروژه لمس نشدند.

| فرمان/بررسی اجراشده | نتیجه واقعی |
|---|---|
| `.\.venv\Scripts\python.exe -m pip check` | `No broken requirements found.`؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py check` | `System check identified no issues (0 silenced).`؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` | `No changes detected`؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py test --verbosity 1` | ۴۳ تست، `Ran 43 tests in 2.885s`، `OK`؛ exit 0 |
| `.\.venv\Scripts\python.exe scripts\concurrency_smoke.py` | دو upload همزمان روی سهمیه ناکافی رقابت کردند؛ فقط یکی ذخیره و فایل اضافه‌ای باقی نماند؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py migrate --noinput` با `DATA_ROOT` موقت | migrationهای Django و `portfolio.0001_initial` تا `0003_entitlement_is_test` اعمال شدند؛ exit 0 |
| fixture ساختگی از طریق `manage.py shell -c` | ۲ کاربر، ۲ پروفایل، یک WorkLink، یک PNG خصوصی ۶۸ بایتی، ۲ Plan، ۲ Entitlement، یک Favorite و یک Payment ایجاد و شمار اولیه assert شد؛ exit 0 |
| `manage.py backup_site <snapshot>` و `manage.py verify_backup <snapshot>` | snapshot دو فایلی (DB و رسانه) ساخته شد؛ checksum، SQLite integrity و ارجاع رسانه تأیید شد؛ هر دو exit 0 |
| کپی DB و رسانه‌ها به `DATA_ROOT` جدا؛ `manage.py check` و assert پس از restore | check بدون خطا؛ هر ۸ شمار رکورد با fixture برابر و بایت PNG با اصل برابر بود (`RESTORE_OK`، ۶۸ بایت)؛ هر دو exit 0 |
| `.\.venv\Scripts\python.exe scripts\browser_smoke.py` | پیش از شروع مرورگر با `ModuleNotFoundError: No module named 'playwright'` متوقف شد؛ exit 1 |
| `manage.py check --deploy`، DEBUG خاموش و کلید موقت | exit 0؛ فقط `security.W005` و `security.W021` گزارش شدند |

اولین فراخوانی seed مصنوعی به‌دلیل تفکیک نادرست آرگومان چندخطی `-c` در PowerShell اجرا نشد (exit 2) و هیچ داده‌ای نساخت؛ snapshot بعدی فقط DB خالی را دربر داشت و assert بازیابی موفق نداشت، بنابراین شاهد restore محسوب نمی‌شود. فراخوانی تکراری با انتقال کد fixture به‌شکل base64 موفق شد و فقط اجرای دوم به‌عنوان شاهد ثبت شده است. پوشه‌های داده، snapshot و restore موقت پس از بررسی پاک شدند.

برای نصب پاک، `python -m venv <temp>` موفق شد؛ سپس در venv جدا `python -m pip install --no-input --retries 1 --timeout 8 -r requirements.txt` بدون proxy به timeout در `pypi.org/simple/django/` رسید (exit 1). venv پاک شد. در تلاش قبلی نصب `requirements-dev.txt` با proxy مبتنی بر SOCKS به `Missing dependencies for SOCKS support` رسید؛ تلاش مستقیم به PyPI نیز timeout شد. Playwright در `.venv` موجود نیست و مرورگر اجرا نشد. TLS verification غیرفعال نشد. برای تکرار پس از فراهم‌شدن مسیر شبکه مجاز:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\browser_smoke.py
```

استقرار VPS، دامنه، ایمیل واقعی، پذیرندگی/پرداخت زنده و مقصد دوم بکاپ در این اجرا ارائه یا بررسی نشدند. آزمون restore فقط حفظ داده ساختگی با طرح فعلی را می‌سنجد و migration دعوت یا سازگاری حساب‌های واقعی را اثبات نمی‌کند.

انتشار گزارش: commit محلی `835a1e10e31a62bb59956ea4fae11e21e0d03366` ساخته شد. `git push origin HEAD:refs/heads/docs/mvp-audit-issue-3` بدون force با exit 128 ناموفق بود: `fatal: Cannot prompt because user interactivity has been disabled` و `fatal: unable to get password from user`. پس از تلاش، `git ls-remote` و اطلاعات PR #12 نشان دادند head منتشرشده هنوز `a5c24e19a50d97e441778660395f1829a75734a2` است؛ PR باز و ادغام‌نشده است. گزارش و اعتبارسنجی در شاخه محلی حفظ شدند؛ push دیگری انجام نشد.
