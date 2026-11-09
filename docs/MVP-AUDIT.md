# ممیزی فاصله نسخه مبنا تا MVP دعوتی

- تاریخ بررسی: ۲۰۲۶-۱۱-۱۰
- مبنای کد: شاخه `main`، commit `ab24f0774d91af02528090c225e5bc8a255b2e00`
- نسخه مبنای گزارش منتشرشده: شاخه `docs/mvp-audit-issue-3`، commit `4f5e5743a13390db443e61fe5a3a21c339aaf431`
- شاخه اصلاح: `codex/mvp-audit-issue-3-revision`
- مرجع دامنه: تعریف و چک‌لیست مصوب در PR باز [#11](https://github.com/amirfassadi/PerformingArtsCV/pull/11)، شاخه `codex/mvp-invitation-plan`، commit `eeef41c32638a25529607fd20728799d011a82e2`.

این گزارش فقط وضعیت همان commit مبنا را ثبت می‌کند؛ در اصلاح آن قابلیت محصولی یا migration ساخته نشده است. تعریف و معیارهای پذیرش از `docs/MVP.md` و چک‌لیست `docs/MVP-TASKS.md` در PR #11 خوانده شدند؛ این فایل‌ها در commit مبنای `main` نبودند. فایل‌های `docs/BACKEND_IMPLEMENTATION.md`، `docs/FRONTEND_REVIEW.md` و `docs/VPS_PREPARATION.md` نیز در آن commit موجود نبودند و برای افزودن معیار پذیرش استفاده نشدند. تحصیلات ساختاریافته، همکاران، تأیید تلفن/ایمیل و استرداد، شرط مصوب پذیرش در MVP نیستند؛ این ممیزی آن‌ها را مانع اعلام نمی‌کند. اگر دامنه جداگانه‌ای برایشان لازم است، باید تصمیم محصول مستقلی ثبت شود. بازیابی رمز با ایمیل واقعی و پشتیبانی عملیاتی، برعکس، صریحاً در MVP آمده‌اند.

## جمع‌بندی

نسخه مبنا پیاده‌سازی قابل آزمونی برای بخش‌هایی از مسیر رزومه، رسانه، سهمیه و پرداخت دارد. این به معنی تکمیل MVP نیست: ثبت‌نام دعوتی هنوز پیاده نشده، بازیابی رمز/پشتیبانی و تجربه موبایل هنوز تأیید نشده و پرداخت واقعی و استقرار زنده در این ممیزی بررسی نشده‌اند. هیچ باگ محصولی صرفاً از نبود قابلیت یا آزمون نتیجه‌گیری نشده است؛ شکاف‌ها با شناسه و نوع شواهد در جدول یافته‌ها آمده‌اند.

آزمون‌های سرور و رقابت سهمیه در محیط موقت گذشتند؛ snapshot داده ساختگی نیز ساخته، بررسی و در ریشه موقت جدا بازیابی شد. سرویس‌های خارجی و داده واقعی به این ممیزی ارائه یا دسترسی داده نشدند. نتایج تاریخی مرورگر در ابتدای `VALIDATION.md` مربوط به اجرای دیگری است و به این بررسی تازه نسبت داده نمی‌شود.

## جدول وضعیت قابلیت‌ها

| قابلیت | وضعیت پیاده‌سازی | وضعیت بررسی | شاهد کد/تست | فاصله تا معیار پذیرش | تسک مقصد |
|---|---|---|---|---|---|
| دعوت و انتساب دعوت‌کننده | پیاده‌نشده | کد و آزمون ثبت‌نام بررسی و آزمون خودکار اجرا شد؛ دعوت مستقلاً آزمون نشده است. | [signup](../portfolio/views.py#L22)، [SignupForm](../portfolio/forms.py#L9)، `ProductTests.test_signup_creates_only_own_profile_and_no_browse_access` در [tests.py](../portfolio/tests.py#L57) (اجرا شد؛ فقط ثبت‌نام عادی را پوشش می‌دهد). | #2 معیار می‌خواهد ثبت‌نام معتبر با دعوت، انتساب ثابت و کنترل مدیر. آزمون فعلی ساخت حساب/پروفایل را ثابت می‌کند، نه دعوت. | #4 |
| ورود، خروج و بازیابی رمز | پیاده‌سازی جزئی | مسیر ورود/خروج از کد بررسی شد؛ ثبت‌نام در آزمون سرور اجرا شد؛ بازیابی رمز و ایمیل واقعی آزمون نشدند و URL بازیابی دیده نشد. | [config/urls.py](../config/urls.py#L7)، `ProductTests.test_signup_creates_only_own_profile_and_no_browse_access` (اجرا شد). | معیار MVP بازیابی عملیاتی رمز با ایمیل واقعی است؛ مسیر فعلی برای آن دیده نشد. محدودیت تلاش نیز در چک‌لیست #8 است. | #5، #8 |
| پروفایل، انتشار و راه تماس حرفه‌ای | پیاده‌سازی پایه | کد و قالب بررسی شد؛ مالکیت/پیش‌نویس در آزمون سرور اجرا شد؛ نمایش ایمیل حساب فقط از روی کد بررسی شد. | [Profile/ProfileForm](../portfolio/models.py#L32)، [ProfileForm](../portfolio/forms.py#L16)، [profile_detail](../portfolio/views.py#L130)، [profile.html](../templates/portfolio/profile.html#L3)، `ProductTests.test_free_account_can_read_own_but_not_other_profile` ([tests.py](../portfolio/tests.py#L72))، `test_paid_viewer_cannot_read_draft` ([tests.py](../portfolio/tests.py#L99)) و `test_owner_cannot_modify_another_profile_by_forged_form_field` ([tests.py](../portfolio/tests.py#L125)) (اجرا شدند). | هر حساب یک رزومه دارد و نمایش به مشترکان محدود است. حساب ایمیل خصوصی در قالب رزومه نمایش داده نمی‌شود و contact فیلد جداست. تحصیلات ساختاریافته، همکاران و تأیید تلفن معیار مصوب این MVP نیستند؛ الزام تازه‌ای ایجاد نشده است. | #5 |
| جست‌وجو، شهر و منتخب‌ها | پیاده‌شده | کد و آزمون خودکار اجرا شد. | [directory/toggle_favorite](../portfolio/views.py#L109)، `ProductTests.test_paid_viewer_searches_and_favorites` در [tests.py](../portfolio/tests.py#L90) (اجرا شد). | آزمون مسیر جست‌وجو/شهر و افزودن منتخب را پوشش می‌دهد؛ حذف منتخب جداگانه در این تست مشخص نیست. معیار MVP تکمیل مسیر منتخب است. | #5 |
| لینک اثر و رسانه خصوصی | پیاده‌سازی پایه | کد و آزمون‌های سرور اجرا شدند؛ مرورگر واقعی در این ممیزی اجرا نشد. | [upload/media](../portfolio/views.py#L69)، [UploadForm](../portfolio/forms.py#L32)، `test_upload_stores_private_file_and_accounts_actual_bytes` ([tests.py](../portfolio/tests.py#L142))، `test_fake_image_and_html_rejected` ([tests.py](../portfolio/tests.py#L168))، `test_file_authorization_and_byte_ranges` ([tests.py](../portfolio/tests.py#L181)) و `test_disk_write_is_cleaned_when_database_save_fails` ([tests.py](../portfolio/tests.py#L173)) (اجرا شدند). | نوع فایل، مالکیت/اشتراک و rollback بارگذاری آزموده شدند. ابزار تشخیص فایل مفقود/یتیم در کدهای بررسی‌شده پیدا نشد؛ مورد آن با اطمینان محدود در AUD-007 آمده است. | #6 |
| سهمیه و جدایی اشتراک فضا/مشاهده | پیاده‌شده | آزمون‌های سرور و smoke هم‌زمان اجرا شدند؛ بررسی مقدار پیش‌فرض/تنظیم از کد و آزمون بود. | [SiteSettings/access](../portfolio/models.py#L11)، [access.py](../portfolio/access.py#L5)، `test_storage_purchase_does_not_grant_browse` ([tests.py](../portfolio/tests.py#L80))، `test_browse_purchase_does_not_increase_storage` ([tests.py](../portfolio/tests.py#L85))، `test_free_quota_updates_existing_accounts_immediately` ([tests.py](../portfolio/tests.py#L131)) و `test_staff_can_change_quota_from_admin` ([tests.py](../portfolio/tests.py#L237)) (اجرا شدند)؛ [concurrency_smoke.py](../scripts/concurrency_smoke.py) (اجرا شد). | در این سناریو فقط یکی از دو upload هم‌زمان ذخیره شد؛ کاهش سهمیه فایل را حذف نکرد. این شواهد بررسی محدود به SQLite/محیط محلی است. | #6 |
| پلن، quote و callback پرداخت | پیاده‌سازی موجود؛ پرداخت واقعی تأییدنشده | کد و suite سرور اجرا شدند؛ تست‌های درگاه mock هستند، نه اتصال واقعی. | [checkout](../portfolio/payment_views.py#L15)، [billing](../portfolio/billing.py#L29)، `test_checkout_uses_server_price_and_saved_plan_snapshot` ([tests.py](../portfolio/tests.py#L264))، `test_verified_payment_creates_one_grant_even_after_repeat` ([tests.py](../portfolio/tests.py#L277))، `test_failed_verification_never_grants_access` ([tests.py](../portfolio/tests.py#L294))، `test_unsigned_checkout_request_does_not_create_order` ([tests.py](../portfolio/tests.py#L366)) (اجرا شدند با mock). | quote سروری و رفتار تأیید/تکرار mock آزموده‌اند؛ آزمون sandbox واقعی، پرداخت کنترل‌شده و رسیدگی سفارش بی‌callback در این اجرا انجام نشد. معیار پرداخت زنده تا #7 تأیید نشده است. استرداد شرط تازه‌ای افزوده نمی‌شود. | #7 |
| مدیریت، پشتیبانی و حفاظت حساب | پیاده‌سازی جزئی | پنل و اسناد بررسی شدند؛ آزمون تنظیم سهمیه admin اجرا شد؛ بازیابی رمز/گزارش محتوا/حذف حساب/پشتیبانی زنده اجرا نشدند. | [admin.py](../portfolio/admin.py#L8)، `ProductTests.test_staff_can_change_quota_from_admin` در [tests.py](../portfolio/tests.py#L237) (اجرا شد)، [OPERATIONS.md](OPERATIONS.md#L48). | تنظیم سهمیه و مدیریت مدل‌های پایه هست؛ بازیابی رمز، محدودیت تلاش و مسیرهای پشتیبانی/گزارش و درخواست حذف حساب که در #8 برنامه‌ریزی شده‌اند هنوز شاهد عملی ندارند. | #8 |
| تجربه فارسی روی موبایل و دسکتاپ | پیاده‌سازی/رفتار تأییدنشده | آزمون مرورگر اجرا نشد؛ فقط وجود smoke script بررسی شد. | [browser_smoke.py](../scripts/browser_smoke.py#L1) (در این اجرا به علت نبود Playwright با exit code 1 متوقف شد). | هیچ ادعای تکمیل UX یا نبود overflow نمی‌شود. معیار مرور مسیر اصلی در موبایل/دسکتاپ نیازمند اجرای بعدی است. | #8، #10 |
| بکاپ و بازیابی | فرمان محلی پیاده‌شده؛ محل دوم تأییدنشده | آزمون خرابی و مقصد موجود در suite اجرا شد؛ snapshot/verify/restore ساختگی نیز در این اجرا اجرا شد. | `BackupValidationTests.test_corrupted_backup_is_rejected` و `test_existing_backup_destination_is_not_overwritten` در [tests.py](../portfolio/tests.py#L379) (اجرا شدند)، [backup_site.py](../portfolio/management/commands/backup_site.py#L14)، [verify_backup.py](../portfolio/management/commands/verify_backup.py#L12). | بازیابی یک حساب/فایل از snapshot محلی آزمایش شد؛ انتقال، زمان‌بندی، پایش و بازیابی از مقصد دوم بررسی نشدند. | #9 |
| استقرار و سرویس‌های واقعی | وضعیت بیرونی بررسی‌نشده | تنظیمات و راهنمای محلی بررسی شدند؛ در دسترس بودن VPS، دامنه، سرویس ایمیل، پذیرندگی واقعی و مقصد دوم به این ممیزی ارائه یا بررسی نشد. | [settings.py](../config/settings.py#L31)، [OPERATIONS.md](OPERATIONS.md#L13)، [PAYMENTS.md](PAYMENTS.md#L23). `check --deploy` فقط پیکربندی محلی موقت را سنجید. | شواهد موجود برای اعلام وضعیت سرویس‌های بیرونی کافی نیست؛ نه آماده‌بودن و نه نبود آن‌ها نتیجه‌گیری نمی‌شود. | #7، #9 |
| پذیرش MVP و شروع آزمایش | تأییدنشده | آزمون سرور گذشت؛ مسیر مرورگر، سرویس واقعی و مهاجرت داده موجود بررسی نشدند. | جمع‌بندی آزمون‌های بالا؛ تعریف پذیرش در [MVP.md در PR #11](https://github.com/amirfassadi/PerformingArtsCV/blob/codex/mvp-invitation-plan/docs/MVP.md#%D9%85%D8%B9%DB%8C%D8%A7%D8%B1-%D9%BE%D8%A7%DB%8C%D8%A7%D9%86). | معیارهای دعوت، بازیابی ایمیل، تجربه واقعی موبایل، HTTPS و بکاپ محل دوم یک‌جا تأیید نشده‌اند؛ شروع آزمایش تأیید نمی‌شود. | #10 |

## دامنه و شواهد

برای هر سطر «پیاده‌سازی» وضعیت کد در commit مبناست و «بررسی» بیان می‌کند که شواهد در این نوبت اجرا، از روی کد خوانده، با mock آزموده، با سرویس واقعی آزموده، یا اصلاً بررسی نشده‌اند. همه ۴۳ آزمون Django و smoke سهمیه در این نوبت اجرا شدند. نام آزمون، نوع mock و محدودیت هر ردیف صریح است. صرف نبود آزمون یا نبود پیاده‌سازی، باگ اثبات‌شده محسوب نمی‌شود.

| شناسه | نوع | اثر/شدت | انتظار مصوب | واقعیت و روش بازتولید/بررسی | تسک مقصد |
|---|---|---|---|---|---|
| AUD-001 | کار برنامه‌ریزی‌شده | مانع معیار دعوتی | ثبت‌نام فقط با دعوت معتبر؛ انتساب دعوت‌کننده هنگام ثبت‌نام و مدیریت دعوت. | `ProductTests.test_signup_creates_only_own_profile_and_no_browse_access` واقعاً اجرا و قبول شد، اما فقط ثبت‌نام آزاد و ساخت پروفایل را می‌سنجد. [کد signup](../portfolio/views.py#L22) هیچ بررسی دعوت ندارد. این شاهد شکاف دامنه است، نه خرابی مسیر موجود. | #4 |
| AUD-002 | کار برنامه‌ریزی‌شده | مانع معیار حساب/پشتیبانی | بازیابی رمز عملیاتی با ایمیل واقعی؛ محدودیت تلاش، راه تماس/رسیدگی پشتیبانی و آیتم‌های گزارش محتوا/حذف حسابِ چک‌لیست #8. | [config/urls.py](../config/urls.py#L7) و [راهنمای عملیات](OPERATIONS.md#L48) خوانده شدند؛ فقط مسیر ورود و خروج در URLها دیده شد. ارسال ایمیل، بازیابی رمز یا جریان پشتیبانی اجرا نشد. `ProductTests` این موارد را پوشش نمی‌دهد. | #8 |
| AUD-003 | بررسی‌نشده | مانع تأیید تجربه موبایل و پذیرش | مرور مسیر کامل روی موبایل و دسکتاپ. | `python scripts/browser_smoke.py` با کد خروج 1 و `ModuleNotFoundError: No module named 'playwright'` متوقف شد. نصب dev از SOCKS5 به خطای وابستگی SOCKS برخورد کرد؛ تلاش مستقیم PyPI نیز timeout شد. هیچ نتیجه بصری/موبایلی تازه‌ای به دست نیامد. | #8، #10 |
| AUD-004 | ورودی بیرونی / بررسی‌نشده | مانع تأیید پرداخت واقعی | تعیین ورودی‌های محصول و اجرای sandbox واقعی و پرداخت کنترل‌شده پیش از پذیرش. | `test_checkout_uses_server_price_and_saved_plan_snapshot`، `test_verified_payment_creates_one_grant_even_after_repeat` و `test_failed_verification_never_grants_access` اجرا شدند، اما `Zarinpal` را mock می‌کنند. در محیط موقت این ممیزی شناسه پذیرندگی خالی و sandbox روشن بود؛ این مقدار فقط محیط آزمون را توصیف می‌کند و وضعیت سرویس واقعی را اثبات نمی‌کند. هیچ درخواست واقعی درگاه ارسال نشد. | #7 |
| AUD-005 | ورودی بیرونی / بررسی‌نشده | مانع تأیید استقرار | تأیید HTTPS، دامنه، سرور و سرویس‌های موردنیاز در محیط مقصد. | تنظیمات و [راهنمای محلی عملیات](OPERATIONS.md#L13) خوانده شد؛ VPS، دامنه و سرویس ایمیل در این ممیزی ارائه یا بررسی نشدند. بنابراین وضعیت واقعی آن‌ها نامعلوم است؛ از کد محلی درباره وجود/نبود سرویس زنده نتیجه‌گیری نمی‌شود. | #9 |
| AUD-006 | کار برنامه‌ریزی‌شده / بررسی‌نشده | مانع معیار بکاپ دومرحله‌ای | انتقال نسخه امن به محل دوم و اثبات بازیابی در مقصد. | `backup_site`، `verify_backup` و restore روی داده ساختگی و دیسک محلی اجرا شدند و گذشتند؛ مقصد دوم، زمان‌بندی، پایش و restore خارج از ماشین آزمایش نشدند. | #9 |
| AUD-007 | کار برنامه‌ریزی‌شده | اثر: تشخیص خرابی رسانه هنوز اثبات نشده | شناسایی و رسیدگی مستند به فایل مفقود یا بدون رکورد، بدون حذف خودکار. | فرمان‌های مدیریت در کد مرورشده فهرست شدند؛ ابزار تشخیص فایل یتیم/مفقود در آن‌ها دیده نشد. مورد واقعی گم‌شدن فایل ساخته یا آزموده نشد، پس باگ عملیاتی اثبات نشده است. | #6 |
| AUD-008 | بررسی‌نشده | اثر: سازگاری حساب‌های قدیمی نامعلوم | ورود تدریجی به ثبت‌نام دعوتی بدون نسبت‌دادن دعوت‌کننده ساختگی یا از دست‌دادن داده قبلی. | پایگاه داده و رسانه‌های واقعی پروژه عمداً خوانده نشدند؛ migration دعوتی نیز در این مرحله اجرا یا ساخته نشد. پیشنهاد محافظه‌کارانه زیر صرفاً برنامه بررسی در #4 است. | #4 |
| AUD-009 | ورودی بیرونی | مانع تأیید فروش پلن | تعیین قیمت، مدت، ظرفیت و قواعد پلن با تصمیم مالک محصول. | مدل `Plan` و پنل ادمین بررسی شدند، اما پایگاه داده زنده/پلن‌های واقعی خوانده نشدند؛ قیمت و ظرفیت واقعی در این ممیزی تأیید نشده‌اند. هیچ مقدار قیمت حدس زده نمی‌شود. | #7 |
| AUD-010 | هشدار پیکربندی مشاهده‌شده | اثر: تنظیم سیاست HSTS پیش از HTTPS نهایی نیازمند تصمیم است | تصمیم آگاهانه درباره شمول زیردامنه‌ها و preload بر مبنای کنترل HTTPS آن‌ها. | `manage.py check --deploy` با کلید تصادفی موقت، DEBUG خاموش و ریشه داده موقت اجرا شد؛ exit code برابر 0 و فقط `security.W005` و `security.W021` گزارش شدند. این هشدارها اثبات رخنه یا استقرار زنده نیستند؛ مستندات دلیل فعال‌نکردن این گزینه‌ها را بیان می‌کند. | #9 |

در این ممیزی باگ محصولیِ بازتولیدشده گزارش نمی‌شود. به‌ویژه هیچ ادعایی درباره تنظیم‌بودن یا نبودن VPS، دامنه، ایمیل، پذیرندگی واقعی یا مقصد دوم بکاپ مطرح نیست؛ دسترسی/اطلاعات لازم برای بررسی آن منابع ارائه نشد.

## محیط و اعتبارسنجی تکرارپذیر

- سیستم‌عامل/پوسته: Windows، PowerShell.
- مفسر: Python 3.14.7 از `.venv` موجود مخزن (`.venv\Scripts\python.exe`)؛ محیط در این نوبت از نو ساخته نشد.
- وابستگی‌های نصب‌شده: Django 5.2.19 و Waitress 3.0.2. `pip check` خروجی `No broken requirements found.` و کد 0 داشت.
- برای هر بررسی Django، `DATA_ROOT` و `PRIVATE_MEDIA_ROOT` به پوشه‌های تصادفی بیرون مخزن اشاره می‌کردند. کلید آزمون تصادفی موقت، میزبان‌های محلی، پذیرندگی خالی و sandbox روشن بود. پوشه‌های موقت پس از آزمون پاک شدند؛ پایگاه داده/رسانه معمول پروژه دست‌نخورده ماند.

| فرمان یا بررسی واقعی | نتیجه/کد خروج |
|---|---|
| `.\.venv\Scripts\python.exe -m pip check` | موفق؛ `No broken requirements found.`؛ 0 |
| `.\.venv\Scripts\python.exe manage.py check` | موفق؛ `System check identified no issues (0 silenced).`؛ 0 |
| `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` | موفق؛ `No changes detected`؛ 0 |
| `.\.venv\Scripts\python.exe manage.py test --verbosity 1` | موفق؛ 43 آزمون، 3.281 ثانیه، همگی `OK`؛ 0 |
| `.\.venv\Scripts\python.exe scripts\concurrency_smoke.py` | موفق؛ `PASS: two concurrent uploads cannot exceed one account quota; no extra file remains.`؛ 0 |
| `.\.venv\Scripts\python.exe manage.py migrate --noinput` روی `DATA_ROOT` موقت | موفق؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py shell -c "<ساخت User و Profile ساختگی و add_file با PNG آزمایشی>"` | موفق؛ `SYNTHETIC_FIXTURE_CREATED`؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py backup_site $snapshot` و `.\.venv\Scripts\python.exe manage.py verify_backup $snapshot` در همان PowerShell process | هر دو exit 0؛ `Backup complete: ... (2 files)` و `Backup verified: checksums, database and media references are valid.` |
| `Copy-Item` از DB و private-media snapshot به DATA_ROOT جدا، سپس `.\.venv\Scripts\python.exe manage.py check` و shell assertion | همه exit 0؛ `RESTORE_OK profiles=1 files=1 bytes=68` |
| `.\.venv\Scripts\python.exe scripts\browser_smoke.py` | ناموفق پیش از شروع مرورگر؛ `ModuleNotFoundError: No module named 'playwright'`؛ 1 |
| با `DJANGO_DEBUG=0`، کلید تصادفی بلند موقت و ریشه داده موقت، `.\.venv\Scripts\python.exe manage.py check --deploy` | کد 0؛ دو هشدار `security.W005` و `security.W021`. این فقط تنظیمات محلی موقت را بررسی می‌کند. |

### تلاش نصب Playwright

Playwright نسخه `1.64.1` و PySocks در `.venv` نصب نبودند. متغیرهای proxy محیط از scheme نوع `socks5` استفاده می‌کنند؛ هنگام اجرای `.\.venv\Scripts\python.exe -m pip install --no-input --retries 0 --timeout 8 -r requirements-dev.txt` با proxy فعال، pip خطای `Missing dependencies for SOCKS support` داد؛ exit code 1. علت شکست اولیه، نبود پیاده‌سازی SOCKS در محیط پایتون (`socks`/PySocks موجود نبود) است؛ هیچ آدرس proxy یا اعتبارنامه‌ای در گزارش ثبت نمی‌شود.

برای تشخیص جداگانه، نصب یک‌بار با متغیرهای proxy موقتاً از همان فرایند پاک و با timeout محدود اجرا شد؛ TLS verification غیرفعال نشد:

```powershell
.\.venv\Scripts\python.exe -m pip install --no-input --retries 1 --timeout 8 -r requirements-dev.txt
```

این تلاش نیز ناموفق بود: درخواست HTTPS به `pypi.org/simple/playwright/` پس از ۸ ثانیه timeout شد و pip نسخه‌ای پیدا نکرد؛ کد خروج 1. اجرای مجدد `scripts\browser_smoke.py` همچنان به import خطا خورد. نصب Chromium هم انجام نشد، چون بسته Playwright قابل دریافت نبود.

روش اجرای بعدی پس از فراهم‌شدن دسترسی معتبر pip (proxy پشتیبان SOCKS یا مسیر شبکه مجاز):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\browser_smoke.py
```

Microsoft Edge در مسیر مورد انتظار smoke script موجود بود؛ پس از نصب Playwright، فرمان نصب جداگانه Chromium لازم نیست. نتیجه مرورگر تاریخی ابتدای [VALIDATION.md](VALIDATION.md) مربوط به اجرای قبلی است و شاهد اجرای حاضر نیست.

## تداوم داده در تغییر به ثبت‌نام دعوتی

داده واقعی در این ممیزی بررسی نشد. برای #4 فقط پیشنهاد بررسی است: از DB و رسانه‌های ارجاع‌شده snapshot بگیرید و آن را verify کنید؛ migration افزایشی را روی کپی داده اجرا کنید؛ حساب‌ها، hash رمز، پروفایل‌ها، منتخب‌ها، اشتراک/پرداخت و ارجاع رسانه را تطبیق دهید؛ کاربران قدیمی را حفظ و برایشان دعوت‌کننده ساختگی ایجاد نکنید؛ rollback/restore را بیازمایید. این پیشنهاد نه migration است و نه شاهدی از وضعیت کاربران واقعی.

## محدوده تحویل مرحله ۱

این PR فقط گزارش را تصحیح می‌کند: دامنه پذیرفته‌شده، وضعیت پیاده‌سازی در برابر وضعیت بررسی، یافته‌های شناسه‌دار، منشأ خطای محیط و محدودیت منابع بیرونی. مرحله‌های #4 تا #10 در این شاخه اجرا نمی‌شوند. پذیرش و شروع آزمایش کاربران واقعی همچنان نیازمند بررسی‌های اشاره‌شده در جدول یافته‌ها و تأیید مالک محصول است.
