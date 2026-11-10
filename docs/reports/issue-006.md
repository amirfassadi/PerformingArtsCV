# گزارش اجرای Issue #6 — مرحلهٔ ۴: رسانهٔ خصوصی و سهمیهٔ ذخیره‌سازی

## وضعیت تحویل

- وضعیت: `READY_FOR_REVIEW`
- تسک: Issue #6 — مرحلهٔ ۴
- اصلاح بازبینی: PR #15 — تکمیل MEDIA-001 پس از تأیید MEDIA-002
- آخرین به‌روزرسانی: ۲۰۲۶-۱۱-۱۰ ۱۲:۲۹ (+۰۳:۳۰)
- مجری: Copilot
- شاخهٔ محلی: `codex/issue-6-private-media-storage`
- SHA کد مبنای مرحلهٔ ۴: `810b09d3928f7a84de7745235ccd91d1a608d7a7`
- SHA commit محلی قبلی (MEDIA-002): `55565b968f7f5a45137dce2283505fde9b8160f7`
- SHA commit محلی کد این اصلاح: `4a5cf08261eed9165ecec2d80d7e901d3068c856`
- SHA commit محلی آماده‌سازی/تکمیل آزمون: `74bc937baff1765a1fedae6c2ac424db7204c409`
- مبنای مرحلهٔ ۳: PR #14 باز و ادغام‌نشده است؛ PR، commit محلی مبنا را به‌عنوان منبع نسخهٔ بررسی‌شده معرفی می‌کند. کار روی شاخهٔ تازه از همان commit آغاز شد.
- وضعیت انتشار: بر عهدهٔ هماهنگ‌کننده؛ این گزارش و تغییرات فقط محلی هستند.

`READY_FOR_REVIEW` پس از نصب وابستگی‌های ثبت‌شده و اجرای آزمون کامل و مرورگر واقعی. push، درخواست احراز هویت، ساخت/به‌روزرسانی PR، ادغام و بستن Issue انجام نشدند. هیچ تغییر دیتابیسی یا مهاجرت به PostgreSQL صورت نگرفت؛ آزمون‌ها از SQLite و مسیرهای رسانهٔ موقت استفاده کردند.

## دامنه و تغییرات

منطق اصلی آپلود خصوصی، سهمیه و کنترل دسترسی در مبنا وجود داشت. این اصلاح بازبینی، دو مورد رسانه را تکمیل کرد:

- [media_validation.py](../../portfolio/media_validation.py) و [forms.py](../../portfolio/forms.py): علاوه بر بررسی ساختار، Pillow الزاماً تصاویر را decode و PyAV/FFmpeg یک فریم ویدئو را decode می‌کند؛ نبود ابزار به خطای آشکار می‌انجامد.
- [tests.py](../../portfolio/tests.py): نمونه‌های خراب WebP و MP4 جدول‌خالی دقیقاً مطابق کامنت PR اضافه شد؛ رد ورودی نبود رکورد، blob و مصرف سهمیه را می‌سنجد.
- [browser_smoke.py](../../scripts/browser_smoke.py): MP4/H.264 قابل‌پخش قبلی حفظ شد؛ WebP، JPEG و MP4 آزمایشی به‌علاوه WebM ضبط‌شده برای مسیر پذیرش فرم پوشش داده می‌شوند.
- [requirements.txt](../../requirements.txt) و [OPERATIONS.md](../OPERATIONS.md): نسخه‌های Pillow/PyAV و راه‌اندازی پیش از اجرا مستند شد؛ در زمان آپلود نصب/دانلود انجام نمی‌شود.

## معیارهای پذیرش و شواهد

| معیار | نتیجه | شاهد آزمون | محدودیت |
|---|---|---|---|
| افزودن/حذف تصویر، ویدئو و لینک خارجی با عنوان و نمایش درست | موفق | [test_upload_stores_private_file_and_accounts_actual_bytes](../../portfolio/tests.py#L436)، [test_external_work_link_can_be_added_and_removed_without_storage_use](../../portfolio/tests.py#L489) و اجرای مرورگر روی SQLite/media موقت: PNG/JPEG/WebP آزمایشی رمزگشایی شد؛ MP4 آزمایشی ضبط، آپلود و از مسیر خصوصی پخش شد. حذف فایل در [test_owner_delete_frees_space_and_removes_blob](../../portfolio/tests.py#L610) بررسی شد. | پخش واقعی با MP4/H.264 در مرورگر داخلی Chromium سنجیده شد؛ پخش WebM در این محیط تأیید نشد. |
| نمایش مصرف و سقف؛ سهمیهٔ رایگان ۱۰۰ مگابایت و تنظیم مدیر | موفق در مرحلهٔ پایه | آزمون آپلود مقدارهای `quota_mb=100` و مصرف واقعی بر حسب بایت را بررسی می‌کند؛ [test_staff_can_change_quota_from_admin](../../portfolio/tests.py#L663) تنظیم مدیر را بررسی می‌کند. | در اصلاح PR #15 دوباره اجرا نشد؛ تغییرات سهمیه در این اصلاح نبودند. تنظیمات واقعی سرور/حساب مدیر عملیاتی بررسی نشدند. |
| نوع، اندازه و محتوای فایل؛ ثبت انواع مجاز و رفتار فایل نامعتبر | موفق | [test_rejects_truncated_and_malformed_media_without_saving](../../portfolio/tests.py#L472) نمونهٔ ۳۰ بایتی `invalid.webp` و MP4 صدوسی‌وسه‌بایتی با جدول‌های خالی را رد کرد و نبود رکورد/blob/مصرف سهمیه را سنجید؛ decode واقعی Pillow/PyAV برای رسانهٔ سالم نیز در suite و smoke اجرا شد. نسخه‌ها در `requirements.txt` پین شده‌اند؛ سقف درخواست multipart و decode فریم محدود باقی می‌ماند. |
| مجوز در هر درخواست و جلوگیری از مسیر عمومی فایل | موفق در مرحلهٔ پایه | [test_file_authorization_and_byte_ranges](../../portfolio/tests.py#L581) مهمان، حساب رایگان، مشترک مجاز، لغو اشتراک و Range را بررسی کرد؛ مسیرهای `/media/` و `/never-public/` 404 هستند. | در اصلاح PR #15 دوباره اجرا نشد؛ endpoint دسترسی تغییری نکرد. وب‌سرور زنده آزموده نشد. |
| سهمیه در بارگذاری هم‌زمان، آزادشدن فضا و عدم مصرف توسط لینک خارجی | موفق در مرحلهٔ پایه | [test_external_work_links_do_not_consume_storage](../../portfolio/tests.py#L463)، آزمون حذف و گزارش smoke پیشین [concurrency_smoke.py](../../scripts/concurrency_smoke.py). | concurrency smoke پس از اصلاح رسانه دوباره اجرا نشد؛ ظرفیت بالا آزموده نشده است. |
| حفظ فایل پس از کاهش سهمیه/انقضای اشتراک و توقف آپلود تازه پس از عبور از سقف | موفق در مرحلهٔ پایه | [test_lowering_quota_keeps_files_readable](../../portfolio/tests.py#L619) و [test_storage_entitlement_expiry_keeps_existing_files_and_blocks_new_ones](../../portfolio/tests.py#L628). | در اصلاح PR #15 دوباره اجرا نشد؛ تاریخ‌ها ساختگی‌اند و سرویس اشتراک زنده دخیل نیست. |
| تشخیص فایل مفقود/بدون رکورد و رسیدگی بدون حذف خودکار | موفق در مرحلهٔ پایه | [test_media_audit_reports_missing_untracked_and_size_mismatch_without_deleting](../../portfolio/tests.py#L506) و [audit_portfolio_media.py](../../portfolio/management/commands/audit_portfolio_media.py). اجرای audit پاک روی SQLite/media موقت نیز موفق بود. | audit لحظه‌ای و فقط‌خواندنی است؛ فایل را خودکار ترمیم/حذف نمی‌کند. |

### اصلاحات PR #15

| مورد | نتیجه | شاهد | محدودیت |
|---|---|---|---|
| MEDIA-001 — فایل WebP بی‌داده و MP4 با جدول‌های خالی | تأیید شد | WebP ناقص و MP4 با جدول‌های خالی رد شدند؛ MP4 چندبخشیِ سالمِ ضبط‌شده توسط Edge پس از اصلاح تشخیص ساختار `mvex/moof` با PyAV یک فریم decode کرد. آزمون منفی endpoint نبود رکورد/blob/مصرف سهمیه را کنترل کرد. |
| MEDIA-002 — پخش واقعی MP4 | تأییدشده و حفظ شد | آخرین کامنت PR #15 تأیید می‌کند هماهنگ‌کننده کل `browser_smoke.py` را با Playwright و Edge واقعی اجرا کرده و MP4/H.264 با ابعاد 160×90، مدت حدود 1.74s، `readyState=4` و پیشرفت زمان پخش شده است. این اصلاح به کد پخش دست نمی‌زند. | اجرای دوبارهٔ Edge برای commit حاضر به‌دلیل نبود Playwright و decoderهای لازم انجام نشده است. |

**معیار کلی تسک — دور نزدن مجوز یا سهمیه، باقی‌نماندن فایل اضافی پس از بارگذاری ناموفق و حذف‌نشدن خودکار فایل‌های پیشین در انقضا: موفق.** شواهد ردیف‌های بالا و آزمون‌های خطای سهمیه، خطای ذخیرهٔ دیتابیس، کنترل URL مستقیم و انقضای اشتراک این معیار را پوشش می‌دهند.

## اعتبارسنجی

همهٔ بررسی‌های این اصلاح با حساب‌ها و فایل‌های ساختگی انجام شدند. آزمون‌های Django و audit در `DATA_ROOT` و `PRIVATE_MEDIA_ROOT` یکتای زیر مسیر موقت اجرا شدند. بررسی تصویری/ویدئویی مرورگر نیز از SQLite و رسانهٔ موقت استفاده کرد. از دیتابیس، رسانه یا حساب واقعی استفاده نشد.

| فرمان/بررسی | نتیجه | کد خروج |
|---|---|---:|
| دو آزمون هدفمند Django برای نمونه‌های خراب و خطای وابستگی تصویر | هر دو موفق؛ آزمون‌ها از SQLite و فایل‌های ساختگی/مسیر موقت استفاده کردند | ۰ |
| `python manage.py check` | بدون خطای Django | ۰ |
| `python manage.py makemigrations --check --dry-run` | migration جاافتاده نبود؛ موتور و migrationهای SQLite تغییر نکردند | ۰ |
| `python -m py_compile portfolio\media_validation.py portfolio\forms.py portfolio\tests.py scripts\browser_smoke.py` | نحو فایل‌های تغییرکرده معتبر | ۰ |
| `git diff --check` | خطای whitespace نداشت | ۰ |
| `python manage.py test` کامل | برای این اصلاح اجرا نشد | — |
| نصب اولیه `python -m pip install -r requirements-dev.txt` با مفسر `.venv\Scripts\python.exe` | شکست؛ کد خروج ۱، خطای پاک‌سازی‌شده `Missing dependencies for SOCKS support`؛ متغیرهای `HTTP_PROXY`/`HTTPS_PROXY` روی `socks5://127.0.0.1:1081` بودند و PySocks نصب نبود | ۱ |
| تلاش مستقیم بدون proxy برای همان فرمان | شکست؛ کد خروج ۱، `ConnectionResetError(10054)` و سپس `No matching distribution found for Pillow==13.0.0`؛ wheel ویندوز/CPython 3.14 برای pin اولیه موجود نبود | ۱ |
| آماده‌سازی wheelهای سازگار در `.venv` | موفق؛ Pillow 12.3.0، PyAV 18.1.0، Playwright 1.64.1 و وابستگی‌های `pyee`/`greenlet`/`typing-extensions` نصب شدند؛ PyAV wheel، FFmpeg را همراه دارد | ۰ |
| `python manage.py test` | هر ۶۴ آزمون موفق | ۰ |
| `python scripts/browser_smoke.py` | موفق با Edge واقعی؛ H.264 ضبط‌شده و پخش‌شده: مدت `1.7418s`، ابعاد `160×90`، `readyState=4` و پیشرفت `0.2204s`؛ مسیرهای موقت و دادهٔ ساختگی | ۰ |
| decode مستقیم WebP و MP4 سالم | موفق؛ Pillow WebP را decode کرد و PyAV MP4 مرورگر را `video/mp4` پذیرفت | ۰ |
| `python manage.py check` و `makemigrations --check --dry-run` | بدون خطا و بدون migration جدید | ۰ |
| `python -m py_compile ...` و `git diff --check` | موفق | ۰ |
| `python scripts/concurrency_smoke.py` | در اعتبارسنجی پایهٔ مرحلهٔ ۴ موفق بود؛ پس از اصلاح رسانه دوباره اجرا نشد | پیشین |

## موارد اجرا‌نشده و موانع

- پخش WebM، provider ابری، دیسک/وب‌سرور زنده، اسکن ضدبدافزار، آزمون فشار و بازیابی فایل گمشده از بکاپ واقعی اجرا نشدند. browser smoke Edge و decode سالم این revision اجرا شدند.
- audit فقط اختلاف را گزارش می‌کند؛ هیچ حذف، بازپیوند یا اصلاح اندازه‌ای انجام نمی‌دهد. رسیدگی واقعی باید پس از snapshot و بازبینی انسانی طبق [راهنمای عملیات](../OPERATIONS.md#L50) انجام شود.
- مانع اجرایی باقی نمانده است. pinهای وابستگی برای wheel سازگار با Python 3.14/Windows اصلاح و در محیط نصب شدند؛ بازبینی مستقل و انتشار بر عهدهٔ هماهنگ‌کننده است.
