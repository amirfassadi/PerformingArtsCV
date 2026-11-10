# گزارش آماده‌سازی Issue 009

- وضعیت: `READY_FOR_REVIEW`
- زمان: 2026-11-10 21:39:30 +03:30
- شاخه: `codex/issue-9-deployment-backup`
- مبنا: `ae3b84d4670831456446b3995fc48e93d279d826`
- SHA کد: `6e70af79346de2094370fd363bb9a66532d8a174`
- انتشار: بر عهدهٔ هماهنگ‌کننده

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
- سناریوی مستقیم synthetic backup/restore: healthcheck، backup ثانویه، verify، restore و تطبیق داده/فایل موفق.
- snapshot با manifest خراب: `verify_backup` با exit code 1 شکست خورد.

تمام داده‌ها و مسیرها در زیرپوشه موقت `%TEMP%\performingartscv-issue009` ساخته شدند و پس از آزمون وارد Git نشدند.

## محدودیت‌ها و تصمیم‌های لازم

- استقرار HTTPS واقعی، دامنه، DNS، سرور، systemd/Caddy واقعی و پایش production اجرا نشد.
- انتقال به مقصد دوم خارجی/ابری، رمزنگاری خارج از دیسک، retention، RPO/RTO و هشدار عملیاتی نیازمند تصمیم مالک پروژه است.
- سیاست‌های حقوقی، مالی و پشتیبانی مصوب نشده‌اند؛ این گزارش هیچ SLA یا وعده‌ای جعل نمی‌کند.
- ایمیل واقعی، پرداخت واقعی و ظرفیت production آزموده نشدند. آزمون مرورگر و بکاپ صرفاً محلی و شبیه‌سازی‌شده‌اند.
- `check --deploy` همچنان دو هشدار HSTS را عمداً نگه می‌دارد تا پوشش همه زیردامنه‌ها و preload به‌صورت رسمی تعیین شود.
