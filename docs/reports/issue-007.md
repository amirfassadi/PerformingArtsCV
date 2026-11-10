# گزارش Issue #7 — مرحلهٔ ۵: پلن‌ها و پرداخت

## وضعیت تحویل

- وضعیت: `BLOCKED`
- تسک: Issue #7 — مرحلهٔ ۵
- زمان گزارش: ۲۰۲۶-۱۱-۱۰ ۲۰:۲۸ (+۰۳:۳۰)
- شاخه: `codex/issue-7-payment-plans`
- SHA مبنای تأییدشده: `ca0fa823fea5a155b4e108a83d31dfdbf1fae331`
- SHA commit محلی این اصلاح: `43cd6fa20db31c17a43d367d8496b0278ca01ca9` (commit implementation; this report update follows).
- وضعیت انتشار: بر عهدهٔ هماهنگ‌کننده؛ push، احراز هویت، PR، merge، استقرار و بستن Issue انجام نشد.

`BLOCKED` فقط به این دلیل است که پذیرندگی، دامنهٔ callback عمومی و محیط sandbox واقعی در اختیار این اجرا نیست؛ بنابراین خرید واقعی از ابتدا تا فعال‌شدن دقیقاً یک اشتراک قابل ادعا نیست. مسیر شبیه‌سازی‌شده و قرارداد درگاه با دادهٔ ساختگی آزموده شد.

## بررسی مبنا و تصمیم‌های مالی

کد موجود پیش از این اصلاح، قیمت، مدت، نوع و ظرفیت را از `Plan` فعال روی سرور می‌گرفت و در `Payment` به‌صورت snapshot ذخیره می‌کرد. مبلغ‌ها و قواعد زیر در کد جعل یا تغییر نشدند:

- قیمت ریالی، مدت پلن‌ها، ظرفیت پلن‌های فضا و قواعد ارتقا باید توسط مالک محصول/مدیر تعیین شوند؛ در این محیط مقدار مصوب تازه‌ای ارائه نشده است.
- خرید یک‌باره است و تمدید خودکار اضافه نشده است.
- اشتراک مشاهده و فضا مستقل‌اند و می‌توانند هم‌زمان برای یک حساب فعال باشند.
- خرید پلن متفاوت مابه‌التفاوت یا ارتقای خودکار ایجاد نمی‌کند؛ تصمیم محصول برای ارتقا هنوز لازم است.
- پذیرنده، دامنهٔ HTTPS عمومی، سیاست استرداد، SLA پشتیبانی و روند مالی تطبیق باید پیش از فروش واقعی توسط مالک محصول نهایی شوند.

## تغییرات پیاده‌سازی

- `portfolio/models.py` و migration `0005_alter_payment_status.py`: وضعیت‌های `canceled` و `unknown` به وضعیت‌های پرداخت اضافه شدند.
- `portfolio/payment_views.py`: callback با authority ثبت‌شده تطبیق می‌شود؛ `NOK` به لغوشده، وضعیت callback نامعتبر یا خطای تأیید به نامشخص تبدیل می‌شود و هیچ‌کدام اشتراک فعال نمی‌کنند.
- `portfolio/billing.py`: سفارش‌های لغوشده/ناموفق دوباره قابل تأیید نیستند؛ idempotency قبلی برای پرداخت تأییدشده حفظ شد.
- `portfolio/management/commands/reconcile_payments.py`: فهرست‌کردن سفارش‌های `pending`/`unknown` و استعلام مجدد اختیاری آن‌ها برای پشتیبانی اضافه شد.
- `portfolio/tests.py`: مالکیت سفارش، مبلغ سروری و snapshot، خطای درگاه، callback لغوشده/نامشخص، استعلام مجدد و جلوگیری از فعال‌سازی تکراری پوشش داده شد.
- `templates/portfolio/payment.html`: پیام‌های جداگانه و قابل پیگیری برای لغوشده و نامشخص.
- `docs/PAYMENTS.md`: راهنمای پشتیبانی و تطبیق سفارش‌های بلاتکلیف، بدون ثبت کلید یا اطلاعات کارت.

## معیارهای پذیرش

| معیار | نتیجه | شاهد | محدودیت/کار باقی‌مانده |
|---|---|---|---|
| مبلغ و مشخصات سفارش از سرور تعیین و ثابت ثبت شوند | موفق در شبیه‌سازی | `test_checkout_uses_server_price_and_saved_plan_snapshot` و `test_plan_edits_do_not_change_existing_purchase`; تغییر قیمت قبل از POST نیز در `test_price_change_requires_customer_to_confirm_again` رد شد. | قیمت و مدت نهایی کسب‌وکار هنوز باید توسط مالک محصول تأیید شوند. |
| استقلال اشتراک مشاهده و فضا و نبود تمدید خودکار | موفق | `test_storage_payment_does_not_grant_browse`، `test_same_plan_renewal_starts_after_existing_entitlement` و اجرای مرورگر paywall/paid browsing؛ مدل `Entitlement.kind` جداست و هیچ job تمدید خودکار وجود ندارد. | خرید هم‌زمان واقعی در درگاه اجرا نشد. |
| درخواست، بازگشت، تأیید و وضعیت‌های ناموفق/لغوشده/نامشخص | موفق در شبیه‌سازی | `test_forged_authority_and_cancelled_callback_do_not_verify`، `test_success_callback_timeout_marks_payment_unknown_without_grant`، تست کد منفی gateway و وضعیت failed هنگام خطای request. | callback عمومی واقعی و پاسخ‌های sandbox واقعی در دسترس نبودند. |
| فعال‌سازی فقط پس از تأیید معتبر و جلوگیری از تکرار | موفق در شبیه‌سازی | `test_verified_payment_creates_one_grant_even_after_repeat`، `test_same_gateway_receipt_cannot_fulfill_two_orders`، قفل تراکنشی و `OneToOneField` اشتراک پرداخت؛ callback تکراری مجوز دوم نمی‌سازد. | هم‌زمانی درگاه واقعی و sandbox واقعی اجرا نشد؛ تست DB روی SQLite موقت بود. |
| پیگیری و تطبیق سفارش بلاتکلیف | موفق فنی | command `reconcile_payments` بدون `--verify` فهرست می‌کند و با `--verify` فقط `pending`/`unknown` را استعلام می‌کند؛ `test_reconcile_command_lists_and_verifies_unresolved_orders` هر دو مسیر را آزمود. | تطبیق با پنل پذیرنده و رسید بانکی واقعی باقی است. |
| خرید واقعی از ابتدا تا فعال‌شدن دقیقاً یک اشتراک | اجرا نشد / مسدود | smoke مرورگر مسیر sandbox-محور و تست‌های gateway mock موفق بودند؛ هیچ پرداخت واقعی یا sandbox پذیرنده انجام نشد. | نیازمند merchant معتبر، دامنهٔ HTTPS قابل دسترس و هماهنگی مالک محصول است؛ معیار نهایی عمداً کامل اعلام نشده است. |

## آزمون‌های اجراشده

همهٔ آزمون‌ها با مفسر آمادهٔ `E:\miranco.project\Performing Arts-CV\.venv\Scripts\python.exe`، روی checkout حاضر و با SQLite/مسیرهای موقت اجرا شدند. هیچ دادهٔ واقعی، کلید، حساب واقعی یا پرداخت واقعی استفاده نشد.

- `manage.py test`: **۶۷ آزمون موفق**.
- `manage.py test portfolio.tests.BillingTests`: اجرای اولیه پس از تغییر status یک انتظار قدیمی را آشکار کرد؛ انتظار به `unknown` اصلاح شد و suite کامل بعدی با ۶۷ آزمون موفق اجرا شد.
- `scripts/browser_smoke.py`: **موفق** با Edge؛ signup دعوتی، کپی دعوت، حریم خصوصی، رزومه، رسانهٔ خصوصی و پخش H.264، paywall، پرداخت‌های شبیه‌سازی‌شدهٔ موجود، منتخب‌ها، موبایل و backup/restore.
- `manage.py check`: موفق، بدون خطا.
- `manage.py makemigrations --check --dry-run`: موفق، بدون migration جاافتاده.
- `python -m py_compile` برای فایل‌های پرداخت و command: موفق.
- `git diff --check`: موفق.
- `reconcile_payments` در تست با سفارش `unknown`: فهرست و verify شبیه‌سازی‌شده موفق؛ فعال‌سازی فقط پس از receipt معتبر انجام شد.

## موارد اجرا‌نشده و محدودیت‌ها

- خرید واقعی و sandbox واقعی درگاه، callback عمومی HTTPS، استرداد، تطبیق با پنل پذیرنده و آزمون کنترل‌شدهٔ رسید اجرا نشد.
- رقم‌های تولیدی پلن‌ها، سیاست ارتقا/مابه‌التفاوت، سیاست استرداد و SLA پشتیبانی مصوبهٔ مالک محصول ندارند و در این مرحله جعل نشدند.
- provider ابری، وب‌سرور production، بار هم‌زمان واقعی درگاه و پایش عملیاتی اجرا نشد.
- دیتابیس به PostgreSQL منتقل نشد و هیچ تغییر خارج از دامنهٔ پرداخت انجام نشد.
