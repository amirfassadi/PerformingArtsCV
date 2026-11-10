# گزارش آماده‌سازی Issue 009

- وضعیت: `READY_FOR_REVIEW`
- زمان: 2026-11-10 21:39:30 +03:30
- شاخه: `codex/issue-9-deployment-backup`
- مبنا: `ae3b84d4670831456446b3995fc48e93d279d826`
- SHA کد: `6e70af79346de2094370fd363bb9a66532d8a174`
- SHA اصلاح DEPLOY-001: `7a5cd6e8bdda2a372a534eb299272d314c5c1aec`
- SHA اصلاح فرمان service: `55fe0fd126c9555cc9068420af1e0dd495454066`
- انتشار: بر عهدهٔ هماهنگ‌کننده

## اصلاح نهایی فرمان Waitress — 2026-11-10 22:21 +03:30

- هر دو نام هدر اکنون در یک option واحد و quote‌شدهٔ Waitress قرار دارند:
  `--trusted-proxy-headers="x-forwarded-for x-forwarded-proto"`.
- این مقدار در `deploy/performingartscv.service.example` و راهنمای `docs/OPERATIONS.md`
  یکسان است؛ گزینهٔ تکراری حذف شد و peer دقیق `127.0.0.1` و یک hop بدون تغییر باقی ماند.
- `scripts/waitress_service_smoke.py` خط `ExecStart` را مستقیماً از فایل service می‌خواند،
  با `shlex` همان optionها را parse می‌کند و تنها interpreter، application fixture و port
  موقت را جایگزین می‌کند. آزمون مستقل kwargs جایگزین آزمون فرمان service نیست.
- با فرمان استخراج‌شده و Waitress نصب‌شده، دو IP ساختگی به دو `REMOTE_ADDR` متفاوت رسیدند،
  `X-Forwarded-Proto=https` به scheme HTTPS تبدیل شد، زنجیرهٔ جعلی با `trusted-proxy-count=1`
  فقط hop نهایی را گرفت و quota را دور نزد.
- همان فرمان روی Django واقعی با داده/SQLite موقت اجرا شد؛ درخواست‌های POST به
  `/login/`، `/admin/login/` و دوباره `/login/` برای یک IP نتایج `200, 200, 429` دادند،
  بنابراین quota ورود عادی و ادمین مشترک باقی ماند.
- بخش پاک‌سازی Caddy همچنان در نمونه باقی است؛ Caddy واقعی در این محیط اجرا نشد و
  صرفاً مرز آن با header overwrite مستند و شبیه‌سازی شد. peer غیر trusted در آزمون middleware
  قبلی رد شد؛ هیچ wildcard trust یا مصرف مستقیم هدر در Django اضافه نشده است.

## اصلاح DEPLOY-001 — 2026-11-10 21:54 تا 22:05 +03:30

- Waitress اکنون فقط `127.0.0.1` را به‌عنوان `--trusted-proxy` می‌پذیرد، یک hop را
  از `X-Forwarded-For` می‌خواند و فقط `x-forwarded-for` و `x-forwarded-proto` را
  trusted می‌کند. گزینهٔ `--clear-untrusted-proxy-headers` فعال است.
- Caddy قبل از ارسال، `X-Forwarded-For` و `X-Forwarded-Proto` ورودی را حذف و با
  `{remote_host}` و `{scheme}` خودش جایگزین می‌کند و `Forwarded` را حذف می‌کند.
  برنامه همچنان فقط روی loopback گوش می‌دهد.
- مسیر مستقیم بدون این گزینه‌های Waitress امن باقی می‌ماند؛ Django در
  `request_identity` همچنان فقط `REMOTE_ADDR` را می‌خواند و هدر دلخواه کاربر را
  مستقیماً مصرف نمی‌کند. HTTPS/scheme و هویت client دو موضوع جدا هستند.

### شاهد یکپارچه Waitress

`scripts/waitress_proxy_smoke.py` با Waitress نصب‌شده (`3.0.2`) اجرا شد و موفق بود:

- دو هویت ساختگی `198.51.100.10` و `203.0.113.20` مستقل ماندند.
- همان هویت بین `/login/` و `/admin/login/` یک سهمیه مشترک داشت و درخواست سوم `429` شد.
- زنجیرهٔ جعلی `198.51.100.10, 203.0.113.20` فقط به hop نهایی مجاز نگاشت شد و quota را دور نزد.
- middleware برای peer غیرمجاز `192.0.2.44` هدرهای forwarding را حذف کرد.
- فرمان واقعی CLI با گزینه‌های نمونه نیز روی پورت موقت اجرا و با workload ده‌درخواستی موفق شد.
- Caddy واقعی در محیط حاضر نصب/اجرا نشد؛ بخش Caddy با تنظیم header overwrite نمونه و
  peer محلی شبیه‌سازی شد، نه استقرار واقعی.

### بار HTTP و شکست عملیاتی

- `scripts/http_workload_smoke.py` روی Waitress ایزوله، endpoint ریشه، ۴۰ درخواست،
  هم‌زمانی ۴: `failures=0`, مدت `0.211s`, میانه `0.0028s`, بیشینه `0.1721s`.
- اجرای جداگانه با همان flags سرویس، ۱۰ درخواست و هم‌زمانی ۲: `failures=0`,
  مدت `0.349s`.
- این آزمایش محدود توسعه‌ای است و ظرفیت production، SLA یا بار نماینده را اثبات نمی‌کند.
- healthcheck با مسیر رسانه مفقود و سپس با حد فضای آزاد غیرممکن هر دو exit code `1`
  دادند. مقصد backup داخل private media نیز exit code `1` داد و انتشار انجام نشد.
- نمونه `backup-task.example.ps1` خطای healthcheck/backup را با exit غیرصفر propagate
  می‌کند؛ schedule واقعی یا alert تحویل‌شده نصب نشد.

## تغییرات

- فرمان `healthcheck` برای وجود مسیر رسانه خصوصی، صحت SQLite، قیود کلید خارجی و حداقل فضای آزاد اضافه شد.
- `backup_to_secondary` با staging، بررسی کامل و rename اتمیک فقط snapshot معتبر را منتشر می‌کند و در شکست staging را پاک می‌کند.
- `backup_site` برای SQLite فایل از backup API و برای دیتابیس‌های URI/in-memory تستی از اتصال فعال/serialize استفاده می‌کند.
- نمونه‌های Caddy، systemd و زمان‌بندی PowerShell در `deploy/` اضافه شد. Caddy فقط static را مستقیم سرو می‌کند و مسیر رسانه خصوصی را منتشر نمی‌کند.
- تنظیم حداقل فضای آزاد و نمونه متغیر محیطی مستند شد.
- راهنمای عملیات دربارهٔ HTTPS، کاربر محدود، proxy trust، مسیرهای پایدار، بکاپ ثانویه، restore و تصمیم‌های باز تکمیل شد.

## معیارهای پذیرش

1. **آماده‌سازی استقرار:** آماده. نمونه‌ها HTTPS، reverse proxy، اجرای loopback با کاربر/گروه محدود، restart، متغیر محیطی و مسیرهای writable صریح دارند. دامنه، سرور و سرویس واقعی انتخاب یا مستقر نشدند.
2. **امنیت تنظیمات و رسانه خصوصی:** آماده برای بازبینی. `DEBUG=0`، secret بیرون Git، host/CSRF/cookie و proxy trust در تنظیمات و راهنما پوشش داده شده‌اند؛ هیچ route مستقیم برای `private-media` در Caddy وجود ندارد.
3. **بکاپ و مقصد دوم:** آماده برای محیط محلی. snapshot شامل SQLite و رسانه‌های دارای رکورد است، manifest هش دارد، و مقصد ثانویه پس از verify منتشر می‌شود. مقصد خارجی، رمزنگاری و retention واقعی هنوز تعیین نشده‌اند.
4. **restore کامل:** تأیید محلی. در مسیر موقت مستقل، حساب `restore-user`، پروفایل، پرداخت paid، entitlement browse، رابطه دعوت، رکورد رسانه و محتوای فایل پس از restore تطبیق شدند. داده واقعی پروژه دست‌کاری نشد.
5. **سلامت و شکست‌پذیری:** آماده. healthcheck موفق و خطای فضای کم آزموده شد؛ snapshot خراب با exit code 1 رد شد و snapshot ناقص منتشر نشد. audit رسانه نیز `0 missing`, `0 untracked`, `0 size mismatch` گزارش کرد.
6. **بار محدود محلی:** آماده برای بازبینی، نه ظرفیت‌سنجی تولید. `scripts/concurrency_smoke.py` با دیتابیس و رسانه موقت موفق شد و از ایجاد مصرف سهمیه اضافی جلوگیری کرد. نتیجه به ظرفیت production تعمیم داده نمی‌شود.

## آزمون‌های اجراشده

- `manage.py test`: **84 passed**
- `manage.py test portfolio.tests.BackupValidationTests`: **5 passed**
- `manage.py check`: موفق
- `manage.py makemigrations --check --dry-run`: بدون تغییر
- `python -m compileall -q portfolio config scripts`: موفق
- `git diff --check`: موفق
- `manage.py check --deploy` با تنظیمات تولید ساختگی: exit 0؛ هشدارهای HSTS subdomains/preload و secret کوتاه ساختگی ثبت شد و به‌عنوان استقرار تولید تلقی نشد.
- `scripts/browser_smoke.py`: موفق؛ شامل تست مرورگر و backup/restore ایزوله.
- `scripts/waitress_proxy_smoke.py`: موفق؛ مرز اعتماد peer/header و سهمیه مستقل.
- `scripts/waitress_service_smoke.py`: موفق؛ استخراج و اجرای دقیق فرمان service، HTTPS،
  دو هویت، anti-spoof و quota مشترک Django login/admin.
- `scripts/http_workload_smoke.py`: موفق؛ workload محدود بالا.
- سناریوی مستقیم synthetic backup/restore: healthcheck، backup ثانویه، verify، restore و تطبیق داده/فایل موفق.
- snapshot با manifest خراب: `verify_backup` با exit code 1 شکست خورد.

تمام داده‌ها و مسیرها در زیرپوشه موقت `%TEMP%\performingartscv-issue009` ساخته شدند و پس از آزمون وارد Git نشدند.

## محدودیت‌ها و تصمیم‌های لازم

- استقرار HTTPS واقعی، دامنه، DNS، سرور، systemd/Caddy واقعی و پایش production اجرا نشد.
- انتقال به مقصد دوم خارجی/ابری، رمزنگاری خارج از دیسک، retention، RPO/RTO و هشدار عملیاتی نیازمند تصمیم مالک پروژه است.
- سیاست‌های حقوقی، مالی و پشتیبانی مصوب نشده‌اند؛ این گزارش هیچ SLA یا وعده‌ای جعل نمی‌کند.
- ایمیل واقعی، پرداخت واقعی و ظرفیت production آزموده نشدند. آزمون مرورگر و بکاپ صرفاً محلی و شبیه‌سازی‌شده‌اند.
- `check --deploy` همچنان دو هشدار HSTS را عمداً نگه می‌دارد تا پوشش همه زیردامنه‌ها و preload به‌صورت رسمی تعیین شود.
