# ممیزی فاصله نسخه مبنا تا MVP دعوتی

## وضعیت تحویل

- وضعیت: `READY_FOR_REVIEW`
- زمان به‌روزرسانی: ۲۰۲۶-۱۱-۱۰ ۰۱:۳۲ (+03:30).
- تسک: #3؛ مجری: Copilot.
- شاخه گزارش: `codex/mvp-audit-issue-3-final`.
- شاخه منتشرشده مبنا: `docs/mvp-audit-issue-3` در `a5c24e19a50d97e441778660395f1829a75734a2`؛ PR #12 باز است و ادغام نشده.
- SHA کد بررسی‌شده: `main` در `ab24f0774d91af02528090c225e5bc8a255b2e00`.
- فایل‌های خروجی: `docs/MVP-AUDIT.md` و `docs/VALIDATION.md`؛ فقط مستندات تغییر می‌کنند.
- نتیجه انتشار: ناموفق؛ push عادی به `docs/mvp-audit-issue-3` با exit 128 و به‌علت غیرفعال‌بودن prompt تعاملی احراز هویت انجام نشد. head منتشرشده همچنان `a5c24e19a50d97e441778660395f1829a75734a2` است؛ PR #12 باز و ادغام‌نشده مانده است.
- مرجع پذیرش: PR #11 در `eeef41c32638a25529607fd20728799d011a82e2`.
- تغییرات این مرحله فقط گزارش و سوابق اعتبارسنجی هستند؛ پیاده‌سازی محصول یا migration انجام نمی‌شود.

- تاریخ بررسی: ۲۰۲۶-۱۱-۱۰
- مبنای کد: شاخه `main`، commit `ab24f0774d91af02528090c225e5bc8a255b2e00`
- نسخه مبنای گزارش منتشرشده: شاخه `docs/mvp-audit-issue-3`، commit `4f5e5743a13390db443e61fe5a3a21c339aaf431`
- نسخه فعلی PR #12 در شروع این نوبت: `a5c24e19a50d97e441778660395f1829a75734a2`
- مرجع دامنه: تعریف و چک‌لیست مصوب در PR باز [#11](https://github.com/amirfassadi/PerformingArtsCV/pull/11)، شاخه `codex/mvp-invitation-plan`، commit `eeef41c32638a25529607fd20728799d011a82e2`.

این گزارش فقط وضعیت همان commit مبنا را ثبت می‌کند؛ در اصلاح آن قابلیت محصولی یا migration ساخته نشده است. تعریف و معیارهای پذیرش از `docs/MVP.md` و چک‌لیست `docs/MVP-TASKS.md` در PR #11 خوانده شدند؛ این فایل‌ها در commit مبنای `main` نبودند. فایل‌های `docs/BACKEND_IMPLEMENTATION.md`، `docs/FRONTEND_REVIEW.md` و `docs/VPS_PREPARATION.md` نیز در آن commit موجود نبودند و برای افزودن معیار پذیرش استفاده نشدند. تحصیلات ساختاریافته، همکاران، تأیید تلفن/ایمیل و استرداد، شرط مصوب پذیرش در MVP نیستند؛ این ممیزی آن‌ها را مانع اعلام نمی‌کند. اگر دامنه جداگانه‌ای برایشان لازم است، باید تصمیم محصول مستقلی ثبت شود. بازیابی رمز با ایمیل واقعی و پشتیبانی عملیاتی، برعکس، صریحاً در MVP آمده‌اند.

## جمع‌بندی

نسخه مبنا پیاده‌سازی قابل آزمونی برای بخش‌هایی از مسیر رزومه، رسانه، سهمیه و پرداخت دارد. این به معنی تکمیل MVP نیست: ثبت‌نام دعوتی هنوز پیاده نشده، بازیابی رمز/پشتیبانی و تجربه موبایل هنوز تأیید نشده و پرداخت واقعی و استقرار زنده در این ممیزی بررسی نشده‌اند. هیچ باگ محصولی صرفاً از نبود قابلیت یا آزمون نتیجه‌گیری نشده است؛ شکاف‌ها با شناسه و نوع شواهد در جدول یافته‌ها آمده‌اند.

۴۳ آزمون سرور، رقابت سهمیه و snapshot/بازیابی داده ساختگی در محیط موقت گذشتند؛ آزمون مرورگر اجرا نشد، چون Playwright نصب نبود و دریافت وابستگی‌ها از PyPI timeout شد. سرویس‌های خارجی و داده واقعی به این ممیزی ارائه یا دسترسی داده نشدند. نتایج تاریخی مرورگر در ابتدای `VALIDATION.md` مربوط به اجرای دیگری است و به این بررسی تازه نسبت داده نمی‌شود.

## جدول وضعیت قابلیت‌ها

| قابلیت | وضعیت پیاده‌سازی | وضعیت بررسی | شاهد کد/تست | فاصله تا معیار پذیرش | تسک مقصد |
|---|---|---|---|---|---|
| حساب: ثبت‌نام، ورود، خروج، بازیابی رمز و یک رزومه | ناقص | ثبت‌نام/یک‌به‌یک پروفایل: گذشته؛ ورود/خروج: کد بررسی شد؛ بازیابی/ایمیل: بررسی‌نشده. | [signup](../portfolio/views.py#L22)، [config/urls.py](../config/urls.py#L7)، [Profile.user](../portfolio/models.py#L34)، `ProductTests.test_signup_creates_only_own_profile_and_no_browse_access` ([tests.py](../portfolio/tests.py#L57)، اجرا شد). | آزمون ساخت حساب دقیقاً یک پروفایل را تأیید کرد؛ بازیابی رمز با ایمیل واقعی معیار MVP است و هنوز شاهد ندارد. | #5، #8 |
| رزومه: فیلدها، ویرایش مالک، پیش‌نویس و انتشار | ناقص | مالکیت/پیش‌نویس: گذشته در آزمون سرور؛ فرم از کد بررسی شد؛ مرورگر: بررسی‌نشده. | [Profile/ProfileForm](../portfolio/models.py#L32)، [ProfileForm](../portfolio/forms.py#L16)، [profile_detail](../portfolio/views.py#L130)، `test_free_account_can_read_own_but_not_other_profile` ([tests.py](../portfolio/tests.py#L72))، `test_paid_viewer_cannot_read_draft` ([tests.py](../portfolio/tests.py#L99)) و `test_owner_cannot_modify_another_profile_by_forged_form_field` ([tests.py](../portfolio/tests.py#L125)). | مالکیت، draft و حصار دسترسی با آزمون سرور پوشش دارند؛ مسیر مرورگر/UX بررسی‌نشده است. تحصیلات ساختاریافته، همکاران و تأیید تلفن شرط مصوب MVP نیستند. | #5 |
| رسانه: تصویر، ویدئو، لینک، عنوان، نمایش و حذف | ناقص | آپلود تصویر/مجوز فایل/حذف: گذشته در آزمون سرور؛ کد لینک: بررسی شد؛ ویدئو و نمایش مرورگری: بررسی‌نشده. | [UploadForm](../portfolio/forms.py#L32)، [upload/media](../portfolio/views.py#L69)، `test_upload_stores_private_file_and_accounts_actual_bytes` ([tests.py](../portfolio/tests.py#L142))، `test_file_authorization_and_byte_ranges` ([tests.py](../portfolio/tests.py#L181))، `test_owner_delete_frees_space_and_removes_blob` ([tests.py](../portfolio/tests.py#L210))، `test_work_links_reject_javascript_urls` ([tests.py](../portfolio/tests.py#L245)). | تصویر، دسترسی مستقیم و حذف فایل در آزمون سرور هستند؛ ویدئو/نمایش مرورگری تأیید نشده‌اند. آزمون حذف اثر لینک خارجی جداگانه اجرا نشد. | #6 |
| سهمیه: پیش‌فرض، مدیر، مصرف، حذف، لینک خارجی، هم‌زمانی و انقضا | ناقص | پیش‌فرض/تنظیم/مصرف/حذف/رقابت: گذشته؛ انقضای grant فضا و عدم‌شمارش لینک خارجی: آزمون اختصاصی بررسی‌نشده. | [SiteSettings](../portfolio/models.py#L11)، [storage_quota/storage_used](../portfolio/access.py#L21)، [add_file/remove_file](../portfolio/services.py#L6)، `test_free_quota_updates_existing_accounts_immediately` ([tests.py](../portfolio/tests.py#L131))، `test_owner_delete_frees_space_and_removes_blob` ([tests.py](../portfolio/tests.py#L210))، `test_quota_is_total_not_sum_of_paid_plans` ([tests.py](../portfolio/tests.py#L137)) و `test_staff_can_change_quota_from_admin` ([tests.py](../portfolio/tests.py#L237))؛ `concurrency_smoke.py` اجرا شد. | مقدار پیش‌فرض ۱۰۰ MB و دو بارگذاری هم‌زمان بررسی شدند. کد entitlement منقضی را کنار می‌گذارد؛ آزمون مستقیم کاهش سهمیه پس از انقضای grant فضا اجرا نشد. لینک خارجی در محاسبه `PortfolioFile.size` وارد نیست؛ آزمون مستقل ندارد. باگ سهمیه اثبات نشده است. | #6 |
| دسترسی: مهمان، مالک، رایگان، فضای پولی، مشاهده؛ صفحه/فایل مستقیم و draft/انقضا/لغو | ناقص | مهمان/رایگان/تفکیک فضا-مشاهده/draft/لغو: گذشته در آزمون سرور؛ همهٔ ترکیب‌ها و انقضای فایل: بررسی‌نشده. | `test_anonymous_cannot_read_profile_or_directory` ([tests.py](../portfolio/tests.py#L68))، `test_free_account_can_read_own_but_not_other_profile` ([tests.py](../portfolio/tests.py#L72))، `test_storage_purchase_does_not_grant_browse` ([tests.py](../portfolio/tests.py#L80))، `test_expired_revoked_and_future_grants_do_not_allow_browse` ([tests.py](../portfolio/tests.py#L107))، `test_file_authorization_and_byte_ranges` ([tests.py](../portfolio/tests.py#L181)). | اشتراک فضا مشاهده نمی‌دهد. انقضا/لغو browse و revoke فایل پوشش دارند؛ ماتریس کامل تمام نقش‌ها در هر مسیر/انقضای دسترسی رسانه کامل نیست. این شکاف پوشش آزمون است، نه نقص اثبات‌شده در کنترل دسترسی. | #5، #6 |
| کشف افراد: جست‌وجو، شهر و منتخب‌های هر حساب | ناقص | جست‌وجو/شهر/افزودن و فیلتر منتخب: گذشته؛ حذف منتخب و جداسازی دو حساب: بررسی‌نشده. | [directory/toggle_favorite](../portfolio/views.py#L109)، `ProductTests.test_paid_viewer_searches_and_favorites` ([tests.py](../portfolio/tests.py#L90)، اجرا شد). | جست‌وجو/فیلتر و افزودن منتخب پوشش دارند؛ رفتار حذف و استقلال منتخب چند حساب آزمون نشده است، نه اینکه خراب‌بودن آن اثبات شده باشد. | #5 |
| پلن و پرداخت: استقلال، مبلغ سرور، snapshot، تکرار/هم‌زمان، بازگشت و پیگیری | ناقص | مبلغ/snapshot/تأیید تکراری/رسید تکراری: گذشته با mock یا DB؛ sandbox واقعی، callback هم‌زمان و رسیدگی سفارش بی‌بازگشت: بررسی‌نشده. | `test_storage_payment_does_not_grant_browse` ([tests.py](../portfolio/tests.py#L336))، `test_checkout_uses_server_price_and_saved_plan_snapshot` ([tests.py](../portfolio/tests.py#L264))، `test_verified_payment_creates_one_grant_even_after_repeat` ([tests.py](../portfolio/tests.py#L277))، `test_same_gateway_receipt_cannot_fulfill_two_orders` ([tests.py](../portfolio/tests.py#L372)) و `test_callback_does_not_require_session_but_detail_does` ([tests.py](../portfolio/tests.py#L303)). | آزمون‌ها callback واقعی/هم‌زمان نیستند. مسیر بازیابی خطای موقت در کد هست ولی مستقلاً آزمون نشده؛ تطبیق سفارش بی‌callback در کد بررسی‌شده نیافتیم. استرداد معیار مصوب این MVP نیست. | #7 |
| مدیریت، محدودیت تلاش، ایمیل، گزارش محتوا/حذف حساب و RTL/موبایل | ناقص | مدیریت سهمیه: گذشته در آزمون؛ پنل کد بررسی شد؛ تلاش/بازیابی/گزارش/حذف: شاهد اجرایی پیدا نشد؛ مرورگر موبایل/RTL: ناموفق پیش از شروع مرورگر. | [admin.py](../portfolio/admin.py#L8)، `test_staff_can_change_quota_from_admin` ([tests.py](../portfolio/tests.py#L237)، اجرا شد)، [config/urls.py](../config/urls.py#L7)، [browser_smoke.py](../scripts/browser_smoke.py#L1). | مدیریت پایه موجود است؛ نیازهای #8 و آزمون موبایل/RTL هنوز شاهد اجرایی ندارند. از کد CSS/HTML نتیجه UX نمی‌گیریم. | #8 |
| رسانهٔ خصوصی، بکاپ/بازیابی و آمادگی استقرار/پایش | ناقص | backup/verify/restore ساختگی و deploy-check: گذشته؛ محل دوم/VPS/پایش: بررسی‌نشده. | [backup_site.py](../portfolio/management/commands/backup_site.py#L14)، [verify_backup.py](../portfolio/management/commands/verify_backup.py#L12)، `BackupValidationTests.test_corrupted_backup_is_rejected` و `test_existing_backup_destination_is_not_overwritten` ([tests.py](../portfolio/tests.py#L380)، اجرا شدند)، [settings.py](../config/settings.py#L31). | backup/restore محلی روی داده ساختگی موفق است؛ انتقال/پایش/بازیابی محل دوم و استقرار مقصد تأیید نشده‌اند. `check --deploy` فقط config محلی را بررسی می‌کند. | #9 |
| دعوت و انتساب دعوت‌کننده | پیاده‌سازی‌نشده | مدل‌ها، migrationها، URLها و فرم/مسیر ثبت‌نام بررسی؛ تست ثبت‌نام عادی گذشته؛ دعوت مستقلاً بررسی‌نشده چون endpoint/model وجود ندارد. | [signup](../portfolio/views.py#L22)، [SignupForm](../portfolio/forms.py#L9)، `ProductTests.test_signup_creates_only_own_profile_and_no_browse_access` ([tests.py](../portfolio/tests.py#L57)، اجرا شد). migrationهای `0001_initial`، `0002_payment` و `0003_entitlement_is_test` مرور شدند؛ مدل دعوتی در آن‌ها نیست. | ثبت‌نام معتبر، انتساب ثابت و مدیریت دعوت کار برنامه‌ریزی‌شده #4 است، نه باگ کشف‌شده در scope پایه. | #4 |

## دامنه و شواهد

برای هر سطر «پیاده‌سازی» وضعیت کد در commit مبناست و «بررسی» بیان می‌کند که شواهد در این نوبت اجرا، از روی کد خوانده، با mock آزموده، با سرویس واقعی آزموده، یا اصلاً بررسی نشده‌اند. همه ۴۳ آزمون Django و smoke سهمیه در اجرای تکمیلی این نوبت اجرا شدند. نام آزمون، نوع mock و محدودیت هر ردیف صریح است. صرف نبود آزمون یا نبود پیاده‌سازی، باگ اثبات‌شده محسوب نمی‌شود.

| شناسه | نوع | اثر/شدت | انتظار مصوب | واقعیت و روش بازتولید/بررسی | تسک مقصد |
|---|---|---|---|---|---|
| AUD-001 | کار برنامه‌ریزی‌شده | مانع معیار دعوتی | ثبت‌نام فقط با دعوت معتبر؛ انتساب دعوت‌کننده هنگام ثبت‌نام و مدیریت دعوت. | `ProductTests.test_signup_creates_only_own_profile_and_no_browse_access` واقعاً اجرا و قبول شد، اما فقط ثبت‌نام آزاد و ساخت پروفایل را می‌سنجد. [کد signup](../portfolio/views.py#L22) هیچ بررسی دعوت ندارد. این شاهد شکاف دامنه است، نه خرابی مسیر موجود. | #4 |
| AUD-002 | کار برنامه‌ریزی‌شده | مانع معیار حساب/پشتیبانی | بازیابی رمز عملیاتی با ایمیل واقعی؛ محدودیت تلاش، راه تماس/رسیدگی پشتیبانی و آیتم‌های گزارش محتوا/حذف حسابِ چک‌لیست #8. | [config/urls.py](../config/urls.py#L7) و [راهنمای عملیات](OPERATIONS.md#L48) خوانده شدند؛ فقط مسیر ورود و خروج در URLها دیده شد. ارسال ایمیل، بازیابی رمز یا جریان پشتیبانی اجرا نشد. `ProductTests` این موارد را پوشش نمی‌دهد. | #8 |
| AUD-003 | بررسی‌نشده | مانع تأیید تجربه موبایل و پذیرش | مرور مسیر کامل روی موبایل و دسکتاپ. | `python scripts/browser_smoke.py` با کد خروج 1 و `ModuleNotFoundError: No module named 'playwright'` متوقف شد. نصب dev از SOCKS5 به خطای وابستگی SOCKS برخورد کرد؛ تلاش مستقیم PyPI نیز timeout شد. هیچ نتیجه بصری/موبایلی تازه‌ای به دست نیامد. | #8، #10 |
| AUD-004 | ورودی بیرونی / بررسی‌نشده | مانع تأیید پرداخت واقعی | تعیین ورودی‌های محصول و اجرای sandbox واقعی و پرداخت کنترل‌شده پیش از پذیرش. | `test_checkout_uses_server_price_and_saved_plan_snapshot`، `test_verified_payment_creates_one_grant_even_after_repeat` و `test_failed_verification_never_grants_access` اجرا شدند، اما `Zarinpal` را mock می‌کنند. در محیط موقت این ممیزی شناسه پذیرندگی خالی و sandbox روشن بود؛ این مقدار فقط محیط آزمون را توصیف می‌کند و وضعیت سرویس واقعی را اثبات نمی‌کند. هیچ درخواست واقعی درگاه ارسال نشد. | #7 |
| AUD-005 | ورودی بیرونی / بررسی‌نشده | مانع تأیید استقرار | تأیید HTTPS، دامنه، سرور و سرویس‌های موردنیاز در محیط مقصد. | تنظیمات و [راهنمای محلی عملیات](OPERATIONS.md#L13) خوانده شد؛ VPS، دامنه و سرویس ایمیل در این ممیزی ارائه یا بررسی نشدند. بنابراین وضعیت واقعی آن‌ها نامعلوم است؛ از کد محلی درباره وجود/نبود سرویس زنده نتیجه‌گیری نمی‌شود. | #9 |
| AUD-006 | کار برنامه‌ریزی‌شده / بررسی‌نشده | مانع معیار بکاپ دومرحله‌ای | انتقال نسخه امن به محل دوم و اثبات بازیابی در مقصد. | `backup_site`، `verify_backup` و restore در مسیر موقت جدا اجرا شدند. snapshot شامل ۲ کاربر، ۲ پروفایل، یک لینک، یک فایل ۶۸ بایتی، ۲ پلن، ۲ entitlement، یک منتخب و یک پرداخت بود؛ شمار رکوردها و بایت‌های فایل پس از restore تطبیق داده شد. مقصد دوم، زمان‌بندی، پایش و restore خارج از ماشین آزمایش نشدند. | #9 |
| AUD-007 | کار برنامه‌ریزی‌شده | اثر: تشخیص خرابی رسانه هنوز اثبات نشده | شناسایی و رسیدگی مستند به فایل مفقود یا بدون رکورد، بدون حذف خودکار. | فرمان‌های مدیریت در کد مرورشده فهرست شدند؛ ابزار تشخیص فایل یتیم/مفقود در آن‌ها دیده نشد. مورد واقعی گم‌شدن فایل ساخته یا آزموده نشد، پس باگ عملیاتی اثبات نشده است. | #6 |
| AUD-008 | بررسی‌نشده | اثر: سازگاری حساب‌های قدیمی نامعلوم | ورود تدریجی به ثبت‌نام دعوتی بدون نسبت‌دادن دعوت‌کننده ساختگی یا از دست‌دادن داده قبلی. | پایگاه داده و رسانه‌های واقعی پروژه عمداً خوانده نشدند؛ migration دعوتی نیز در این مرحله اجرا یا ساخته نشد. پیشنهاد محافظه‌کارانه زیر صرفاً برنامه بررسی در #4 است. | #4 |
| AUD-009 | ورودی بیرونی | مانع تأیید فروش پلن | تعیین قیمت، مدت، ظرفیت و قواعد پلن با تصمیم مالک محصول. | مدل `Plan` و پنل ادمین بررسی شدند، اما پایگاه داده زنده/پلن‌های واقعی خوانده نشدند؛ قیمت و ظرفیت واقعی در این ممیزی تأیید نشده‌اند. هیچ مقدار قیمت حدس زده نمی‌شود. | #7 |
| AUD-010 | کار برنامه‌ریزی‌شده / هشدار پیکربندی مشاهده‌شده | اثر: تنظیم سیاست HSTS پیش از HTTPS نهایی نیازمند تصمیم است | تصمیم آگاهانه درباره شمول زیردامنه‌ها و preload بر مبنای کنترل HTTPS آن‌ها. | `manage.py check --deploy` با کلید تصادفی موقت، DEBUG خاموش و ریشه داده موقت اجرا شد؛ exit code برابر 0 و فقط `security.W005` و `security.W021` گزارش شدند. این هشدارها اثبات رخنه یا استقرار زنده نیستند؛ مستندات دلیل فعال‌نکردن این گزینه‌ها را بیان می‌کند. | #9 |

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
| `.\.venv\Scripts\python.exe manage.py test --verbosity 1` | موفق؛ 43 آزمون، 2.885 ثانیه، همگی `OK`؛ 0 |
| `.\.venv\Scripts\python.exe scripts\concurrency_smoke.py` | موفق؛ `PASS: two concurrent uploads cannot exceed one account quota; no extra file remains.`؛ 0 |
| `.\.venv\Scripts\python.exe manage.py migrate --noinput` روی `DATA_ROOT` موقت | موفق؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py shell -c <ساخت داده‌های مصنوعی>` | موفق؛ fixture شامل ۲ کاربر، ۲ رزومه، یک لینک، یک فایل PNG، ۲ پلن، ۲ entitlement، یک منتخب و یک پرداخت بود؛ exit 0 |
| `.\.venv\Scripts\python.exe manage.py backup_site <snapshot>` و `.\.venv\Scripts\python.exe manage.py verify_backup <snapshot>` | هر دو exit 0؛ snapshot با ۲ فایل (DB و رسانه) ساخته و checksum، سلامت SQLite و ارجاع رسانه تأیید شد |
| کپی DB و رسانه snapshot به DATA_ROOT جدا، سپس `.\.venv\Scripts\python.exe manage.py check` و assertion شمار رکورد/بایت | همه exit 0؛ `RESTORE_OK` با همان شمارهای fixture و فایل ۶۸ بایتی برابر با PNG اولیه |
| `.\.venv\Scripts\python.exe scripts\browser_smoke.py` | ناموفق پیش از شروع مرورگر؛ `ModuleNotFoundError: No module named 'playwright'`؛ 1 |
| با `DJANGO_DEBUG=0`، کلید تصادفی بلند موقت و ریشه داده موقت، `.\.venv\Scripts\python.exe manage.py check --deploy` | کد 0؛ دو هشدار `security.W005` و `security.W021`. این فقط تنظیمات محلی موقت را بررسی می‌کند. |

برای سنجش نصب پاک، یک venv موقت با Python 3.14.7 ساخته شد (exit 0) و `python -m pip install --no-input --retries 1 --timeout 8 -r requirements.txt` بدون proxy اجرا شد؛ دسترسی مستقیم به `pypi.org/simple/django/` timeout شد و نصب با exit 1 پایان یافت. venv موقت پاک شد. آزمون‌های بالا با `.venv` موجود مخزن اجرا شدند؛ نصب پاک وابستگی‌های runtime و dev در این محیط تأیید نشد.

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

داده واقعی در این ممیزی بررسی نشد. برای #4 فقط پیشنهاد برنامه‌ریزی است: (۱) پیش از rollout از DB و رسانه‌های ارجاع‌شده snapshot بگیرید و verify/restore را بیازمایید؛ (۲) migration را افزایشی طراحی کنید تا دعوت‌های جدید و انتساب اختیاری اضافه شوند، در حالی که حساب‌های قدیمی بدون دعوت‌کنندهٔ ساختگی باقی بمانند؛ (۳) محدودیت دعوت را فقط برای ثبت‌نام جدید اعمال کنید و ورود، hash رمز، پروفایل‌ها، منتخب‌ها، اشتراک/پرداخت و فایل‌های حساب‌های قبلی را حفظ کنید؛ (۴) migration و rollback را روی کپی امن دادهٔ موجود آزمایش و شمار رکوردها، روابط و hash فایل‌ها را قبل/بعد تطبیق دهید؛ و (۵) مسیر آغازین مدیر/صدور دعوت را پیش از فعال‌سازی ثبت‌نام دعوتی مشخص کنید. سناریوی synthetic restore بالا فقط بکاپ نسخه فعلی را می‌سنجد؛ سازگاری migration با داده واقعی یا آینده را اثبات نمی‌کند. این پیشنهاد نه migration است و نه شاهدی از وضعیت کاربران واقعی.

## محدوده تحویل مرحله ۱

این PR فقط گزارش را تصحیح می‌کند: دامنه پذیرفته‌شده، وضعیت پیاده‌سازی در برابر وضعیت بررسی، یافته‌های شناسه‌دار، منشأ خطای محیط و محدودیت منابع بیرونی. مرحله‌های #4 تا #10 در این شاخه اجرا نمی‌شوند. پذیرش و شروع آزمایش کاربران واقعی همچنان نیازمند بررسی‌های اشاره‌شده در جدول یافته‌ها و تأیید مالک محصول است.
