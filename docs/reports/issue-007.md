# گزارش Issue #7 — مرحلهٔ ۵: پلن‌ها و پرداخت

## وضعیت تحویل

- وضعیت: `READY_FOR_REVIEW`
- تسک: Issue #7 — مرحلهٔ ۵
- زمان گزارش: ۲۰۲۶-۱۱-۱۰ ۲۰:۴۲ (+۰۳:۳۰)
- شاخه: `codex/issue-7-payment-plans`
- SHA مبنای تأییدشده: `ca0fa823fea5a155b4e108a83d31dfdbf1fae331`
- SHA commit محلی این اصلاح: `079885e782112731a6bd57d2e27c591150497a19` (implementation commit; report metadata follows in the next local commit).
- وضعیت انتشار: بر عهدهٔ هماهنگ‌کننده؛ push، احراز هویت، PR، merge، استقرار و بستن Issue انجام نشد.

`READY_FOR_REVIEW` به معنی آماده‌بودن اصلاحات فنی برای بازبینی مستقل است. خرید واقعی از ابتدا تا فعال‌شدن دقیقاً یک اشتراک قابل ادعا نیست، چون پذیرندگی، دامنهٔ callback عمومی و محیط sandbox واقعی در اختیار این اجرا نیست؛ این محدودیت همچنان باز و صریح است.

## بررسی مبنا و تصمیم‌های مالی

کد موجود پیش از این اصلاح، قیمت، مدت، نوع و ظرفیت را از `Plan` فعال روی سرور می‌گرفت و در `Payment` به‌صورت snapshot ذخیره می‌کرد. مبلغ‌ها و قواعد زیر در کد جعل یا تغییر نشدند:

- قیمت ریالی، مدت پلن‌ها، ظرفیت پلن‌های فضا و قواعد ارتقا باید توسط مالک محصول/مدیر تعیین شوند؛ در این محیط مقدار مصوب تازه‌ای ارائه نشده است.
- خرید یک‌باره است و تمدید خودکار اضافه نشده است.
- اشتراک مشاهده و فضا مستقل‌اند و می‌توانند هم‌زمان برای یک حساب فعال باشند.
- خرید پلن متفاوت مابه‌التفاوت یا ارتقای خودکار ایجاد نمی‌کند؛ تصمیم محصول برای ارتقا هنوز لازم است.
- پذیرنده، دامنهٔ HTTPS عمومی، سیاست استرداد، SLA پشتیبانی و روند مالی تطبیق باید پیش از فروش واقعی توسط مالک محصول نهایی شوند.

## تغییرات پیاده‌سازی

- `portfolio/models.py` و migration `0005_alter_payment_status.py`: وضعیت‌های `canceled` و `unknown` به وضعیت‌های پرداخت اضافه شدند.
- `portfolio/payment_views.py`: callback با authority ثبت‌شده تطبیق می‌شود؛ `NOK`، callback نامعتبر و خطای تأیید فقط وضعیت recoverable `unknown` می‌سازند و پرداخت `paid` را پایین نمی‌آورند.
- `portfolio/billing.py`: هر سفارش دارای authority، حتی برچسب‌خورده به‌عنوان `canceled` یا `failed`، فقط با پاسخ معتبر قابل بازیابی است؛ سفارش بدون authority به provider ارسال نمی‌شود و تراکنش با retry محدود در contention SQLite محافظت می‌شود.
- `portfolio/management/commands/reconcile_payments.py`: همهٔ سفارش‌های حل‌نشده را فهرست می‌کند، اما `--verify` فقط سفارش دارای authority را استعلام می‌کند و موارد بدون authority را صریحاً گزارش می‌دهد.
- `portfolio/tests.py`: sequence کامل `NOK → OK → verify`، callback دیررس پس از paid، بازیابی canceled و contention سه worker با SQLite جداگانه پوشش داده شد.
- `templates/portfolio/payment.html`: failed بدون authority و canceled بدون authority مسیر retry ندارند؛ وضعیت‌های دارای authority پیام و دکمهٔ استعلام مجاز دارند.
- `docs/PAYMENTS.md`: راهنمای پشتیبانی و تطبیق سفارش‌های بلاتکلیف، بدون ثبت کلید یا اطلاعات کارت.

## معیارهای پذیرش

| معیار | نتیجه | شاهد | محدودیت/کار باقی‌مانده |
|---|---|---|---|
| مبلغ و مشخصات سفارش از سرور تعیین و ثابت ثبت شوند | موفق در شبیه‌سازی | `test_checkout_uses_server_price_and_saved_plan_snapshot` و `test_plan_edits_do_not_change_existing_purchase`; تغییر قیمت قبل از POST نیز در `test_price_change_requires_customer_to_confirm_again` رد شد. | قیمت و مدت نهایی کسب‌وکار هنوز باید توسط مالک محصول تأیید شوند. |
| استقلال اشتراک مشاهده و فضا و نبود تمدید خودکار | موفق | `test_storage_payment_does_not_grant_browse`، `test_same_plan_renewal_starts_after_existing_entitlement` و اجرای مرورگر paywall/paid browsing؛ مدل `Entitlement.kind` جداست و هیچ job تمدید خودکار وجود ندارد. | خرید هم‌زمان واقعی در درگاه اجرا نشد. |
| درخواست، بازگشت، تأیید و وضعیت‌های ناموفق/لغوشده/نامشخص | موفق فنی در شبیه‌سازی | `test_forged_authority_and_nok_callback_remain_recoverable`، `test_late_nok_never_downgrades_paid_payment`، timeout، کد منفی gateway و خطای request؛ NOK دیگر recovery را مسدود نمی‌کند. | callback عمومی واقعی و پاسخ‌های sandbox واقعی در دسترس نبودند. |
| فعال‌سازی فقط پس از تأیید معتبر و جلوگیری از تکرار | موفق فنی در شبیه‌سازی | تکرار ترتیبی، receipt تکراری و `test_callback_retry_and_reconciliation_contention_grants_once` با سه worker/اتصال SQLite؛ یک entitlement، یک receipt و paid نهایی ثبت شد. | هم‌زمانی provider واقعی و sandbox واقعی اجرا نشد؛ SQLite محیط آزمون بود. |
| پیگیری و تطبیق سفارش بلاتکلیف | موفق فنی | `reconcile_payments` همهٔ حل‌نشده‌ها را فهرست می‌کند، بدون authority را ارسال نمی‌کند و دارای authority را با `--verify` بازیابی می‌کند؛ خروجی skip صریح است. | تطبیق با پنل پذیرنده و رسید بانکی واقعی باقی است. |
| خرید واقعی از ابتدا تا فعال‌شدن دقیقاً یک اشتراک | اجرا نشد / مسدود | smoke مرورگر مسیر sandbox-محور و تست‌های gateway mock موفق بودند؛ هیچ پرداخت واقعی یا sandbox پذیرنده انجام نشد. | نیازمند merchant معتبر، دامنهٔ HTTPS قابل دسترس و هماهنگی مالک محصول است؛ معیار نهایی عمداً کامل اعلام نشده است. |

## آزمون‌های اجراشده

همهٔ آزمون‌ها با مفسر آمادهٔ `E:\miranco.project\Performing Arts-CV\.venv\Scripts\python.exe`، روی checkout حاضر و با SQLite/مسیرهای موقت اجرا شدند. هیچ دادهٔ واقعی، کلید، حساب واقعی یا پرداخت واقعی استفاده نشد.

- `manage.py test portfolio.tests.BillingTests portfolio.tests.PaymentConcurrencyTests`: **۲۱ آزمون موفق**؛ شامل sequence بازیابی، وضعیت‌های UI و contention واقعی سه thread با اتصال‌های مستقل SQLite.
- `manage.py test`: **۷۰ آزمون موفق** پس از اصلاح.
- `scripts/browser_smoke.py`: **موفق** با Edge؛ signup دعوتی، کپی دعوت، حریم خصوصی، رزومه، رسانهٔ خصوصی و پخش H.264، paywall، پرداخت‌های شبیه‌سازی‌شدهٔ موجود، منتخب‌ها، موبایل و backup/restore.
- smoke مرورگر اندازه‌های دسکتاپ ۱۴۴۰ و موبایل ۳۹۰/۳۶۰ را در جریان موجود بررسی کرد؛ overflow افقی گزارش نشد.
- `manage.py check`: موفق، بدون خطا.
- `manage.py makemigrations --check --dry-run`: موفق، بدون migration جاافتاده.
- `python -m py_compile` برای فایل‌های پرداخت و command: موفق.
- `git diff --check`: موفق.
- `reconcile_payments` در تست با سفارش `unknown`: فهرست و verify شبیه‌سازی‌شده موفق؛ سفارش بدون authority در مسیر verify ارسال نمی‌شود.

## موارد اجرا‌نشده و محدودیت‌ها

- خرید واقعی و sandbox واقعی درگاه، callback عمومی HTTPS، استرداد، تطبیق با پنل پذیرنده و آزمون کنترل‌شدهٔ رسید اجرا نشد.
- رقم‌های تولیدی پلن‌ها، سیاست ارتقا/مابه‌التفاوت، سیاست استرداد و SLA پشتیبانی مصوبهٔ مالک محصول ندارند و در این مرحله جعل نشدند.
- provider ابری، وب‌سرور production، بار هم‌زمان واقعی درگاه و پایش عملیاتی اجرا نشد.
- دیتابیس به PostgreSQL منتقل نشد و هیچ تغییر خارج از دامنهٔ پرداخت انجام نشد.

## نتیجهٔ بازبینی مستقل هماهنگ‌کننده

نسخهٔ 92fe61fa69fedf91b9f75b460f59b887d3bb1349 بررسی شد. ۷۰ تست، آزمون کامل Edge و ۱۸ بررسی تکمیلی چیدمان موفق بودند. سناریوی بازیابی پس از NOK و اجرای هم‌زمان سه ورودی واقعی برنامه (callback، استعلام صاحب حساب، ابزار تطبیق) روی SQLite موقت مستقلاً موفق شدند؛ یک اشتراک و یک رسید برای سفارش هم‌زمان ثبت شد. هیچ درخواست واقعی به درگاه یا تراکنش مالی انجام نشد.

PAY-001 و PAY-002 رفع و اصلاحات فنی تأیید شدند. جزئیات و محدودیت‌ها در docs/reports/issue-007-review.md ثبت است. طبق هفت مورد اصلی Issue، ۵ مورد پذیرفته شد: مرحلهٔ ۵ برابر ۷۱٫۴٪ و کل MVP برابر ۵۸٫۹٪ است. تعیین شرایط تجاری پلن‌ها و آزمون sandbox/واقعی معتبر باقی است؛ مرحلهٔ ۵ هنوز کامل نیست و Issue بسته نمی‌شود.
