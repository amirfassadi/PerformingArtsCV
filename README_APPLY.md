# راهنمای اعمال تغییرات فرانت‌اند هنری «درباره‌ی من» در مخزن گیت‌هاب

پروژه: درباره‌ی من (PerformingArtsCV)
شاخه هدف در مخزن: feat/artistic-frontend
مخزن اصلی: https://github.com/amirfassadi/PerformingArtsCV

## علت عدم امکان Push مستقیم از محیط فعلی
محیط اجرایی هوش مصنوعی سندباکس دارای محدودیت امنیتی در اتصال به اینترنت جهت ارسال مستقیم کدهای احراز هویت (Git Credentials / SSH Keys) به حساب‌های شخصی گیت‌هاب است. بنابراین به عنوان یک مهندس ارشد نرم‌افزار و بر اساس ضوابط امنیتی، هیچ‌گونه توکن یا کلیدی در گفت‌وگو درخواست نگردید و تمام خروجی‌ها به صورت بسته‌ی آماده و استاندارد تحویل داده شده است.

## فهرست فایل‌های تغییریافته و ایجادشده (۱۹ فایل)
۱. `static/app.css` (طراحی کامل و هنری استایل‌ها، فونت وزیرمتن، مشکی زغالی و قرمز سینمایی)
۲. `templates/base.html` (هدر، فوتر، ناوبری واکنش‌گرا و پیام‌های سیستمی با نام «درباره‌ی من»)
۳. `templates/portfolio/home.html` (صفحه اصلی و معرفی ارزش‌های پیشنهادی، سهمیه ۱۰۰MB)
۴. `templates/portfolio/profile.html` (نمایش رزومه هنرمند، خط زمانی سوابق و همکاران، تحصیلات و گالری)
5. `templates/portfolio/dashboard.html` (داشبورد هنرمند، سهمیه ۱۰۰MB، سوئیچ انتشار و دسترسی‌ها)
۶. `templates/portfolio/directory.html` (کشف هنرمندان، فیلتر شهر، تخصص، مهارت و منتخب‌ها)
۷. `templates/portfolio/plans.html` (تفکیک دقیق اشتراک مشاهده از بسته فضا، درگاه زرین‌پال ریالی)
۸. `templates/portfolio/checkout.html` (پیش‌فاکتور خرید اشتراک با تذکر عدم تداخل فضا و مشاهده)
۹. `templates/portfolio/payment.html` (رسید پرداخت با کد پیگیری و حالت آزمایشی/واقعی)
۱۰. `templates/portfolio/locked.html` (صفحه خطای ۴۰۳ هنری برای دسترسی بدون اشتراک مشاهده)
۱۱. `templates/portfolio/form.html` (فرم استاندارد ویرایش رزومه با حفظ CSRF جنگو)
۱۲. `templates/registration/login.html` (ورود به سیستم)
۱۳. `templates/registration/signup.html` (ثبت‌نام و درخواست شماره همراه)
۱۴. `templates/registration/otp_verify.html` (احراز شماره همراه با شمارنده ۱۲۰ ثانیه‌ای و کد ۵ رقمی)
۱۵. `templates/portfolio/education_form.html` (فرم سوابق تحصیلی، دانشگاه، مقطع، سال ورود/پایان و وضعیت)
۱۶. `templates/portfolio/experience_form.html` (فرم پروژه‌ها، نوع فعالیت، نقش، کاراکتر و جدول همکاران)
۱۷. `templates/portfolio/account_settings.html` (تنظیمات شماره همراه و ۳ وضعیت ایمیل)
۱۸. `templates/portfolio/email_verification.html` (صفحات فرود لینک ایمیل: معتبر، منقضی و نامعتبر)
۱۹. `docs/FRONTEND_BACKEND_CONTRACT.md` (مستندات قرارداد ارتباط فرانت‌اند و بک‌اند)

## روش ۱: اعمال مستقیم با Git Patch (سریع‌ترین روش)
در پوشه مخزن محلی خود دستورات زیر را اجرا کنید:

```bash
# رفتن به پوشه مخزن
cd PerformingArtsCV

# ایجاد و رفتن به شاخه feat/artistic-frontend
git checkout -b feat/artistic-frontend

# اعمال پچ
git apply /path/to/feat-artistic-frontend.patch

# بررسی وضعیت فایل‌ها
git status

# ثبت کامیت
git add -A
git commit -m "feat(frontend): Artistic cinema-theater UI, mobile OTP, education & experience records, contract doc"

# ارسال به گیت‌هاب
git push -u origin feat/artistic-frontend
```

سپس در گیت‌هاب یک Pull Request از شاخه `feat/artistic-frontend` به `main` باز فرمایید.

## روش ۲: جایگزینی دستی فایل‌ها
فایل‌های موجود در پوشه `templates/`، `static/` و `docs/` موجود در این فایل ZIP را در ریشه پروژه Django کپی کنید.

## روش اجرای پروژه Django و بررسی
```bash
python manage.py migrate
python manage.py runserver
```
و به آدرس `http://127.0.0.1:8000` مراجعه فرمایید.
