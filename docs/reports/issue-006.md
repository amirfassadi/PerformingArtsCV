# گزارش اجرای Issue #6 — مرحلهٔ ۴: رسانهٔ خصوصی و سهمیهٔ ذخیره‌سازی

## وضعیت تحویل

- وضعیت: `READY_FOR_REVIEW`
- تسک: Issue #6 — مرحلهٔ ۴
- اصلاح بازبینی: PR #15 — MEDIA-001 و MEDIA-002
- آخرین به‌روزرسانی: ۲۰۲۶-۱۱-۱۰ ۱۱:۵۲ (+۰۳:۳۰)
- مجری: Copilot
- شاخهٔ محلی: `codex/issue-6-private-media-storage`
- SHA کد مبنای مرحلهٔ ۴: `810b09d3928f7a84de7745235ccd91d1a608d7a7`
- SHA commit محلی اصلاح MEDIA-001/002: `55565b968f7f5a45137dce2283505fde9b8160f7`
- مبنای مرحلهٔ ۳: PR #14 باز و ادغام‌نشده است؛ PR، commit محلی مبنا را به‌عنوان منبع نسخهٔ بررسی‌شده معرفی می‌کند. کار روی شاخهٔ تازه از همان commit آغاز شد.
- وضعیت انتشار: بر عهدهٔ هماهنگ‌کننده؛ این گزارش و تغییرات فقط محلی هستند.

`READY_FOR_REVIEW` فقط آمادگی بازبینی محلی را نشان می‌دهد. push، درخواست احراز هویت، ساخت/به‌روزرسانی PR، ادغام و بستن Issue انجام نشدند. هیچ تغییر دیتابیسی یا مهاجرت به PostgreSQL صورت نگرفت؛ آزمون‌ها از SQLite موقت استفاده کردند.

## دامنه و تغییرات

منطق اصلی آپلود خصوصی، سهمیه و کنترل دسترسی در مبنا وجود داشت. این اصلاح بازبینی، دو مورد رسانه را تکمیل کرد:

- [media_validation.py](../../portfolio/media_validation.py) و [forms.py](../../portfolio/forms.py): اعتبارسنجی ساختاری کامل‌تر تصویر/ویدئو به‌جای امضای ابتدایی؛ پسوند و `Content-Type` مرورگر به‌تنهایی معتبر شمرده نمی‌شوند.
- [tests.py](../../portfolio/tests.py): رد فایل‌های ناقص، کوتاه، CRC خراب و محتوای افزوده/نامنطبق؛ نبود رکورد، blob یا مصرف سهمیه پس از رد ورودی.
- [browser_smoke.py](../../scripts/browser_smoke.py): تولید رسانهٔ ساختگی در مرورگر؛ رمزگشایی تصاویر JPEG/WebP و ضبط/آپلود/پخش MP4 واقعی با مشاهدهٔ فریم.
- [OPERATIONS.md](../OPERATIONS.md): ثبت محدوده و محدودیت‌های اعتبارسنجی ساختاری.

## معیارهای پذیرش و شواهد

| معیار | نتیجه | شاهد آزمون | محدودیت |
|---|---|---|---|
| افزودن/حذف تصویر، ویدئو و لینک خارجی با عنوان و نمایش درست | موفق | [test_upload_stores_private_file_and_accounts_actual_bytes](../../portfolio/tests.py#L436)، [test_external_work_link_can_be_added_and_removed_without_storage_use](../../portfolio/tests.py#L489) و اجرای مرورگر روی SQLite/media موقت: PNG/JPEG/WebP آزمایشی رمزگشایی شد؛ MP4 آزمایشی ضبط، آپلود و از مسیر خصوصی پخش شد. حذف فایل در [test_owner_delete_frees_space_and_removes_blob](../../portfolio/tests.py#L610) بررسی شد. | پخش واقعی با MP4/H.264 در مرورگر داخلی Chromium سنجیده شد؛ پخش WebM در این محیط تأیید نشد. |
| نمایش مصرف و سقف؛ سهمیهٔ رایگان ۱۰۰ مگابایت و تنظیم مدیر | موفق در مرحلهٔ پایه | آزمون آپلود مقدارهای `quota_mb=100` و مصرف واقعی بر حسب بایت را بررسی می‌کند؛ [test_staff_can_change_quota_from_admin](../../portfolio/tests.py#L663) تنظیم مدیر را بررسی می‌کند. | در اصلاح PR #15 دوباره اجرا نشد؛ تغییرات سهمیه در این اصلاح نبودند. تنظیمات واقعی سرور/حساب مدیر عملیاتی بررسی نشدند. |
| نوع، اندازه و محتوای فایل؛ ثبت انواع مجاز و رفتار فایل نامعتبر | MEDIA-001 موفق | [test_complete_png_is_accepted_and_extension_mismatch_is_rejected](../../portfolio/tests.py#L448) PNG کامل/پسوند نامنطبق را سنجید؛ [test_rejects_truncated_and_malformed_media_without_saving](../../portfolio/tests.py#L467) ورودی‌های کوتاه، بریده، CRC خراب، trailing data و سربرگ‌های تنها برای PNG/JPEG/WebP/MP4/WebM را رد کرد و نبود رکورد/blob/مصرف سهمیه را سنجید. JPEG و WebP واقعیِ Canvas و MP4 واقعیِ مرورگر نیز از فرم پذیرفته شدند. | اعتبارسنجی ساختاری/ابعادی است، نه اسکن بدافزار یا رمزگشایی کامل همهٔ فرمت‌ها. سقف `MAX_UPLOAD_BYTES` اندازهٔ کل درخواست multipart، شامل سربار فرم، را محدود می‌کند. |
| مجوز در هر درخواست و جلوگیری از مسیر عمومی فایل | موفق در مرحلهٔ پایه | [test_file_authorization_and_byte_ranges](../../portfolio/tests.py#L581) مهمان، حساب رایگان، مشترک مجاز، لغو اشتراک و Range را بررسی کرد؛ مسیرهای `/media/` و `/never-public/` 404 هستند. | در اصلاح PR #15 دوباره اجرا نشد؛ endpoint دسترسی تغییری نکرد. وب‌سرور زنده آزموده نشد. |
| سهمیه در بارگذاری هم‌زمان، آزادشدن فضا و عدم مصرف توسط لینک خارجی | موفق در مرحلهٔ پایه | [test_external_work_links_do_not_consume_storage](../../portfolio/tests.py#L463)، آزمون حذف و گزارش smoke پیشین [concurrency_smoke.py](../../scripts/concurrency_smoke.py). | concurrency smoke پس از اصلاح رسانه دوباره اجرا نشد؛ ظرفیت بالا آزموده نشده است. |
| حفظ فایل پس از کاهش سهمیه/انقضای اشتراک و توقف آپلود تازه پس از عبور از سقف | موفق در مرحلهٔ پایه | [test_lowering_quota_keeps_files_readable](../../portfolio/tests.py#L619) و [test_storage_entitlement_expiry_keeps_existing_files_and_blocks_new_ones](../../portfolio/tests.py#L628). | در اصلاح PR #15 دوباره اجرا نشد؛ تاریخ‌ها ساختگی‌اند و سرویس اشتراک زنده دخیل نیست. |
| تشخیص فایل مفقود/بدون رکورد و رسیدگی بدون حذف خودکار | موفق در مرحلهٔ پایه | [test_media_audit_reports_missing_untracked_and_size_mismatch_without_deleting](../../portfolio/tests.py#L506) و [audit_portfolio_media.py](../../portfolio/management/commands/audit_portfolio_media.py). اجرای audit پاک روی SQLite/media موقت نیز موفق بود. | audit لحظه‌ای و فقط‌خواندنی است؛ فایل را خودکار ترمیم/حذف نمی‌کند. |

### اصلاحات PR #15

| مورد | نتیجه | شاهد | محدودیت |
|---|---|---|---|
| MEDIA-001 — رد فایل ناقص/صرفاً دارای امضا | برطرف شد | اعتبارسنجی ساختاری پسوند-محور؛ CRC و decompress/ابعاد PNG، فریم JPEG/WebP و ساختار ترک/بلوک MP4/WebM. آزمون‌های منفی بدون ایجاد رکورد یا blob. | اسکن بدافزار و رمزگشایی کامل تمام کدک‌ها خارج از دامنه است. |
| MEDIA-002 — اثبات پخش ویدئوی واقعی | برطرف شد | Chromium روی دادهٔ ساختگی یک MP4/H.264 را با فرم خصوصی بارگذاری کرد و از endpoint خواند؛ پخش موفق با مدت `1.7355s`، ابعاد `160×90`، `readyState=4` و پیشرفت زمان به `0.31155s`. | اجرای کامل `browser_smoke.py` با Playwright Python در این محیط به‌دلیل وابستگی نصب‌نشده اجرا نشد؛ مورد آزموده‌شده با مرورگر داخلی Chromium/SQLite موقت بود، نه Edge واقعی. |

**معیار کلی تسک — دور نزدن مجوز یا سهمیه، باقی‌نماندن فایل اضافی پس از بارگذاری ناموفق و حذف‌نشدن خودکار فایل‌های پیشین در انقضا: موفق.** شواهد ردیف‌های بالا و آزمون‌های خطای سهمیه، خطای ذخیرهٔ دیتابیس، کنترل URL مستقیم و انقضای اشتراک این معیار را پوشش می‌دهند.

## اعتبارسنجی

همهٔ بررسی‌های این اصلاح با حساب‌ها و فایل‌های ساختگی انجام شدند. آزمون‌های Django و audit در `DATA_ROOT` و `PRIVATE_MEDIA_ROOT` یکتای زیر مسیر موقت اجرا شدند. بررسی تصویری/ویدئویی مرورگر نیز از SQLite و رسانهٔ موقت استفاده کرد. از دیتابیس، رسانه یا حساب واقعی استفاده نشد.

| فرمان/بررسی | نتیجه | کد خروج |
|---|---|---:|
| `python manage.py check` | بدون خطای Django | ۰ |
| `python manage.py makemigrations --check --dry-run` | migration جاافتاده نبود؛ موتور و migrationهای SQLite تغییر نکردند | ۰ |
| `python manage.py test` | هر ۶۳ آزمون موفق | ۰ |
| `python manage.py audit_portfolio_media` پس از migrate روی DB/media موقت | ۰ رکورد، ۰ اختلاف؛ داده‌ای تغییر نکرد | ۰ |
| مرورگر داخلی روی برنامهٔ محلی موقت | JPEG/WebP واقعی Canvas و MP4/H.264 ضبط‌شده از فرم آپلود شدند؛ تصویرها decode و ویدئو پخش شد (جزئیات MEDIA-002) | موفق |
| `python scripts/browser_smoke.py` | اجرا نشد: ماژول `playwright` در محیط پروژه نصب نیست | — |
| `python -m pip install -r requirements-dev.txt` | نصب به‌علت `Missing dependencies for SOCKS support` ناموفق؛ manifest تغییر نکرد | — |
| `python -m py_compile portfolio\media_validation.py portfolio\forms.py portfolio\tests.py scripts\browser_smoke.py` | نحو فایل‌های تغییرکرده معتبر | ۰ |
| `git diff --check` | خطای whitespace نداشت | ۰ |
| `python scripts/concurrency_smoke.py` | در اعتبارسنجی پایهٔ مرحلهٔ ۴ موفق بود؛ پس از اصلاح رسانه دوباره اجرا نشد | پیشین |

## موارد اجرا‌نشده و موانع

- اجرای کامل جریان مرورگر `browser_smoke.py`، مرورگر Edge واقعی، پخش WebM، provider ابری، دیسک/وب‌سرور زنده، اسکن ضدبدافزار، آزمون فشار و بازیابی فایل گمشده از بکاپ واقعی اجرا نشدند. آزمون پخش MP4/H.264 در Chromium داخلی و دادهٔ موقت موفق بود؛ محدودیت نصب Playwright و WebM در بالا ثبت شد.
- audit فقط اختلاف را گزارش می‌کند؛ هیچ حذف، بازپیوند یا اصلاح اندازه‌ای انجام نمی‌دهد. رسیدگی واقعی باید پس از snapshot و بازبینی انسانی طبق [راهنمای عملیات](../OPERATIONS.md#L50) انجام شود.
- مانع پیاده‌سازی باقی نمانده است؛ اجرای کامل browser smoke به نصب وابستگی نیاز دارد. بازبینی مستقل و انتشار بر عهدهٔ هماهنگ‌کننده است.
