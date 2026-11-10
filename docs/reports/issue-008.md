# گزارش Issue #8 — مرحلهٔ ۶: حساب، پشتیبانی و امنیت

## وضعیت تحویل

- وضعیت: `READY_FOR_REVIEW`
- تسک: Issue #8 — مرحلهٔ ۶
- زمان گزارش: ۲۰۲۶-۱۱-۱۰ ۲۱:۱۳ (+۰۳:۳۰)
- مجری: Copilot
- شاخه: `codex/issue-8-account-support-security`
- SHA مبنای محلی بررسی‌شده: `fcf1beefb88659beaaf669611421e192437fdedc`
- SHA commit این اصلاح: `25d678495c2f7363ed05f6af09600771da76b642` (implementation commit؛ به‌روزرسانی SHA گزارش در commit محلی بعدی ثبت می‌شود).
- وضعیت انتشار: بر عهدهٔ هماهنگ‌کننده؛ push، احراز هویت، PR، merge، استقرار و بستن Issue انجام نشد.

این وضعیت به معنی آماده‌بودن برای بازبینی مستقل است، نه تأیید متن حقوقی، ارسال ایمیل خارجی یا استقرار production.

## تغییرات

- مسیرهای استاندارد Django برای درخواست، تأیید و تکمیل بازیابی رمز اضافه شد. پاسخ صفحهٔ درخواست عمومی است و وجود حساب را افشا نمی‌کند؛ backend پیش‌فرض console است و از متغیرهای محیطی قابل تنظیم است.
- مدل `RequestThrottle` و helper تراکنشی اضافه شد. محدودیت‌های login، ثبت‌نام، checkout، upload و support در SQLite نگهداری می‌شوند، قابل تنظیم‌اند و به `X-Forwarded-For` اعتماد نمی‌کنند.
- callback، تطبیق پرداخت و دسترسی فایل در rate limit دخالت داده نشدند.
- درخواست پشتیبانی، گزارش محتوا و درخواست حذف حساب اضافه شد. درخواست حذف فقط ثبت می‌شود و بدون سیاست مصوب، داده یا سوابق مالی را حذف نمی‌کند.
- شرایط استفاده، حریم خصوصی و قواعد محتوا به‌صورت صریح با برچسب «پیش‌نویس» اضافه شدند؛ نشانی تماس، SLA، استرداد و تعهد مالی جعل نشده است.
- مدیریت `SupportRequest` و دسترسی پنل Django حفظ شد؛ کاربر staff بدون مجوز مدل‌ها نمی‌تواند عملیات حساس انجام دهد.
- باگ ACCOUNT-001 اصلاح شد: فرم‌های POST خالی bound می‌مانند و پس از exhaustion پاسخ ۴۲۹، پیام قابل مشاهده و `Retry-After` می‌دهند؛ signup/upload/support نیز بررسی شدند.
- باگ ACCOUNT-002 اصلاح شد: مسیر `/admin/login/` قبل از view ادمین همان شمارندهٔ پایدار login را مصرف می‌کند و تعویض endpoint مسیر حدس‌زدن نامحدود ایجاد نمی‌کند.
- بازیابی رمز نیز با limit مستقل DB-backed محافظت شد؛ پاسخ عمومی reset همچنان بین حساب موجود/ناموجود یکسان است و ایمیل تکراری پس از حد ارسال نمی‌شود.

## نتیجهٔ معیارهای پذیرش

| معیار | نتیجه | شاهد | محدودیت/تصمیم باز |
|---|---|---|---|
| مجوز مدیریت کاربران، دعوت، رزومه، پلن، اشتراک و پرداخت | موفق فنی | `test_staff_permission_matrix_is_model_scoped` دسترسی view را برای User، Invitation/Link، Profile، Plan، Entitlement، Payment و SupportRequest با مجوزهای مشخص آزمود و حذف مجوز Payment را به ۴۰۳ تبدیل کرد؛ staff بدون مجوز نیز add پرداخت را ندارد. | بازبینی نقش‌های عملیاتی production و تفکیک مسئولیت انسانی هنوز تصمیم‌گیری نشده است. |
| بازیابی رمز و عدم افشای حساب | موفق با backend آزمایشی | `test_password_reset_is_generic_single_use_and_invalid_after_password_change`: ایمیل حساب ناموجود همان redirect عمومی را دارد، token مصرف‌شده/پس از تغییر رمز نامعتبر می‌شود. | ارسال واقعی ایمیل اجرا نشد؛ provider، دامنه فرستنده و SPF/DKIM باید خارج از Git تنظیم و تأیید شوند. |
| محدودیت ورود، ثبت‌نام، پرداخت و بارگذاری | موفق فنی | `test_empty_and_malformed_forms_return_429_with_retry_after` برای POST خالی login/signup/upload/support پاسخ ۴۲۹ و پیام/Retry-After را آزمود؛ `test_admin_login_shares_login_limit_with_normal_login` bypass ادمین را بست؛ `RateLimitConcurrencyTests` ده worker/اتصال SQLite را اجرا کرد و count مجاز از سقف ۵ بیشتر نشد. | اجرای چند process production، پراکسی واقعی و انتخاب آستانه‌های محصولی واقعی انجام نشده است؛ SQLite برای بار بالاتر محدودیت دارد. |
| شرایط، حریم خصوصی، قواعد محتوا، پشتیبانی، گزارش و حذف حساب | موفق به‌صورت پیش‌نویس | صفحات قانونی برچسب پیش‌نویس دارند؛ مسیرهای `support`, `report-content`, `account-deletion` درخواست ثبت می‌کنند؛ حذف خودکار انجام نمی‌شود. | متن حقوقی، نشانی تماس، SLA، retention، استرداد و فرآیند رسیدگی باید با مالک محصول/مسئول حقوقی تصویب شوند. |
| فارسی، RTL، فرم، صفحه‌کلید و اندازه‌ها | موفق محلی، آمادهٔ بازبینی | مرورگر Edge صفحات login/reset/legal/support/report/deletion/admin را در ۱۴۴۰، ۳۹۰ و ۳۶۰ بررسی کرد؛ `scrollWidth == clientWidth`، فرم‌ها label داشتند، کنترل‌ها با Tab قابل دسترسی بودند، حالت reset نامعتبر و login ۴۲۹ با پیام دیده شد. | valid/used reset با backend ایمیل در تست Django پوشش دارد؛ تحویل ایمیل واقعی و مرور دستی همهٔ دستگاه‌ها اجرا نشد. |

## آزمون‌های اجراشده

با `E:\miranco.project\Performing Arts-CV\.venv\Scripts\python.exe` و داده/دیتابیس/رسانهٔ آزمون موقت:

- `manage.py test portfolio.tests.AccountSecurityTests portfolio.tests.RateLimitConcurrencyTests`: **۱۱ آزمون موفق**.
- `manage.py check`: موفق.
- `manage.py makemigrations --check --dry-run`: موفق، migration جاافتاده وجود ندارد.
- `python -m py_compile portfolio/security.py portfolio/views.py portfolio/payment_views.py portfolio/tests.py`: موفق.
- `git diff --check`: موفق.
- `manage.py test`: **۸۱ آزمون موفق**.
- `scripts/browser_smoke.py --screenshots C:\Users\Amir\.copilot\session-state\44294bc1-b077-4868-9450-f3de6874a2e3\files\issue-008-browser`: **موفق** با Edge و دادهٔ موقت؛ جریان دعوت، privacy، پروفایل، رسانهٔ خصوصی و پخش MP4، paywall، پرداخت mock، منتخب‌ها، موبایل و backup/restore حفظ شدند.
- smoke مرورگر اختصاصی روی سرور موقت `127.0.0.1:61009`: صفحات `/login/`, `/password-reset/`, سه `/legal/`, `/support/`, `/support/content/`, `/support/account-deletion/` و `/admin/login/` در اندازه‌های ۱۴۴۰/۳۹۰/۳۶۰؛ همه بدون overflow افقی، با فرم/label قابل مشاهده. مسیرهای محافظت‌شده با حساب synthetic بررسی شدند.
- حالت ۴۲۹ login پس از exhaustion با پیام و `Retry-After` در مرورگر دیده شد؛ `/reset/MQ/set-password/` حالت token نامعتبر را با پیام فارسی نشان داد؛ Tab traversal به input/buttonها رسید.
- screenshotها: `C:\Users\Amir\.copilot\session-state\44294bc1-b077-4868-9450-f3de6874a2e3\files\issue-008-browser\reset-invalid-390.png` و `account-deletion-1440.png`.
- `manage.py check --deploy`: اجرا شد؛ فقط هشدارهای شناخته‌شدهٔ محیط توسعه دربارهٔ DEBUG، HTTPS/HSTS، SECRET_KEY و کوکی secure باقی است و در production باید با متغیرهای محیطی رفع شود.

## موارد اجرا‌نشده و محدودیت‌ها

- ایمیل واقعی خارجی، provider production، دامنه/تحویل DNS و پرداخت واقعی اجرا نشد؛ backend آزمایشی موفقیت بانکی یا تحویل بیرونی محسوب نمی‌شود.
- متن حقوقی نهایی، نشانی تماس، SLA، سیاست retention، استرداد و قواعد مالی مصوب در اختیار نبود و جعل نشد.
- PostgreSQL، توزیع چند worker در production، WAF، پایش بیرونی و آزمون بار انجام نشد.
- مرور دستی کامل روی دستگاه‌های فیزیکی و همهٔ ترکیب‌های حالت خطا/خالی در هر سه اندازه اجرا نشد؛ بررسی Playwright مسیرهای جدید، اندازه‌ها، labelها، focus و حالت‌های ۴۲۹/invalid را پوشش داد و بازبینی مستقل بصری باقی است.
- ایمیل reset معتبر/مصرف‌شده با backend locmem در تست Django پوشش دارد، اما valid reset form به‌صورت مرورگر با ایمیل واقعی/SMTP اجرا نشد؛ هیچ ایمیل خارجی ارسال نشد.
- هیچ رمز، کلید، دادهٔ شخصی واقعی، حساب واقعی، پرداخت یا رسانهٔ واقعی در Git/گزارش استفاده نشد.
