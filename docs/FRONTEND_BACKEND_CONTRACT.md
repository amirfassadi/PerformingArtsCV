# سند قرارداد ارتباط فرانت‌اند و بک‌اند (Frontend-Backend Contract)
## محصول: «درباره‌ی من» — پلتفرم رزومه و نمونه‌کار اهالی سینما و تئاتر

- **نسخه سند:** ۱.۰.۰
- **شاخه گیت مربوطه:** `feat/artistic-frontend`
- **هدف سند:** تفکیک دقیق قابلیت‌های متصل‌شده به مدل‌های فعلی از قابلیت‌های جدید نیازمند ارتقای مدل‌ها و APIهای بک‌اند، به همراه مشخصات ساختار داده‌ها، اعتبارسنجی‌ها و استانداردهای امنیتی سمت سرور.

---

## ۱. ماتریس وضعیت اتصال صفحات و قابلیت‌ها

| ردیف | نام صفحه / قابلیت | وضعیت اتصال فعلی | نیازمندی بک‌اند برای تکمیل نهایی |
| :--- | :--- | :--- | :--- |
| ۱ | **صفحه اصلی (`home.html`)** | **متصل** | مقدار `free_storage_mb` از `SiteSettings` خوانده می‌شود. |
| ۲ | **ثبت‌نام اولیه (`signup.html`)** | **متصل** | ایجاد ردیف `User` و ساخت خودکار `Profile` با سهمیه رایگان. |
| ۳ | **احراز شماره همراه و OTP (`otp_verify.html`)** | **آماده اتصال (طراحی‌شده)** | نیازمند مدل `PhoneVerification`، سرویس ارسال پیامک (کاوه نگار/فراز) و Endpoint بررسی کد. |
| ۴ | **ورود به سیستم (`login.html`)** | **متصل** | ورود با نام کاربری/رمز عبور جنگو. در گام بعد ورود با OTP موبایل اضافه می‌شود. |
| ۵ | **میز کار هنرمند (`dashboard.html`)** | **متصل** | محاسبه سهمیه مصرفی، سقف، درصد، وضعیت انتشار و لیست فایل‌ها/لینک‌ها متصل است. |
| ۶ | **مشخصات پایه رزومه (`edit-profile`)** | **متصل** | نام هنری، شهر، تخصص، مهارت‌ها، بیوگرافی، راه ارتباطی و وضعیت انتشار به مدل `Profile` متصلند. |
| ۷ | **سوابق تحصیلی و دانشگاهی** | **آماده اتصال (طراحی‌شده)** | نیازمند ایجاد مدل `EducationRecord` و متدهای CRUD. |
| ۸ | **سوابق کاری، پروژه‌ها و همکاران** | **آماده اتصال (طراحی‌شده)** | نیازمند ایجاد مدل `ExperienceRecord` و مدل فرعی `ProjectCollaborator`. |
| ۹ | **بارگذاری فایل نمونه‌کار (`upload`)** | **متصل** | کنترل سهمیه در تراکنش اتمیک، بررسی فرمت امضای باینری (JPG/PNG/WebP/MP4/WebM). |
| ۱۰ | **لینک آثار در وب (`add-link`)** | **متصل** | ذخیره عنوان و آدرس معتبر HTTP/HTTPS در مدل `WorkLink`. |
| ۱۱ | **کشف هنرمندان (`directory.html`)** | **متصل** | بررسی دسترسی اشتراک مشاهده (`can_browse`)، فیلتر شهر، تخصص، جستجو و منتخب‌ها. |
| ۱۲ | **نمایش کامل رزومه (`profile.html`)** | **متصل** | کنترل دسترسی سمت سرور (فقط مالک یا مشترکان مشاهده). |
| ۱۳ | **صفحه محدودیت دسترسی (`locked.html`)** | **متصل** | بازگشت خطای ۴۰۳ در صورت عدم وجود اشتراک مشاهده معتبر. |
| ۱۴ | **پلن‌ها و پیش‌فاکتور (`plans.html`, `checkout.html`)** | **متصل** | تمایز پلن `browse` و `storage`، اتصال به درگاه زرین‌پال در حالت سندباکس/واقعی. |
| ۱۵ | **تنظیمات حساب و وضعیت ایمیل (`account_settings.html`)** | **آماده اتصال (طراحی‌شده)** | نمایش ۳ وضعیت ایمیل، ارسال توکن ۴۸ ساعته و مسیر تایید ایمیل. |

---

## ۲. ساختار پیشنهادی مدل‌ها و فیلدهای جدید در بک‌اند

### ۲.۱. سوابق تحصیلی هنرمند (`EducationRecord`)

```python
class EducationRecord(models.Model):
    class DegreeLevel(models.TextChoices):
        BACHELOR = 'bachelor', 'کارشناسی (لیسانس)'
        MASTER = 'master', 'کارشناسی ارشد (فوق لیسانس)'
        PHD = 'phd', 'دکتری تخصصی'
        ASSOCIATE = 'associate', 'کاردانی (فوق دیپلم)'
        DIPLOMA = 'diploma', 'دیپلم هنرستان / آزاد'
        COURSE = 'course', 'دوره جامع / کارگاه تخصصی آزاد'

    class EducationStatus(models.TextChoices):
        GRADUATED = 'graduated', 'فارغ‌التحصیل'
        STUDYING = 'studying', 'در حال تحصیل'
        INCOMPLETE = 'incomplete', 'تحصیل ناتمام / انصرافی'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField('نام دانشگاه یا مؤسسه آموزشی', max_length=150)
    degree = models.CharField('مقطع تحصیلی', max_length=20, choices=DegreeLevel.choices)
    field = models.CharField('رشته و گرایش', max_length=120)
    location = models.CharField('شهر یا کشور محل تحصیل', max_length=100, blank=True)
    start_year = models.PositiveSmallIntegerField('سال ورود')
    end_year = models.PositiveSmallIntegerField('سال پایان', null=True, blank=True)
    status = models.CharField('وضعیت تحصیلی', max_length=15, choices=EducationStatus.choices, default=EducationStatus.GRADUATED)
    description = models.TextField('توضیحات تکمیلی یا پایان‌نامه', max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**قواعد اعتبارسنجی سمت سرور (`clean`):**
1. تبدیل ارقام فارسی به انگلیسی پیش از ذخیره سال‌ها (`۱۳۹۸` -> `1398`).
2. بررسی محدوده سال ورود (مثلاً بین ۱۳۳۰ تا ۱۴۱۰ یا معادل میلادی ۱۹۵۰ تا ۲۰۳۵).
3. چنانچه `status == 'graduated'` باشد، وارد کردن `end_year` الزامی است و باید `end_year >= start_year`.
4. چنانچه `status == 'studying'` باشد، فیلد `end_year` اختیاری است.

---

### ۲.۲. سوابق کاری و پروژه‌ها (`ExperienceRecord`)

```python
class ExperienceRecord(models.Model):
    class ActivityType(models.TextChoices):
        THEATER = 'theater', 'تئاتر و صحنه'
        FEATURE_FILM = 'feature_film', 'فیلم سینمایی بلند'
        SHORT_FILM = 'short_film', 'فیلم کوتاه'
        SERIES = 'series', 'سریال و نمایش خانگی'
        TELEFILM = 'telefilm', 'تله‌فیلم / تله‌تئاتر'
        COMMERCIAL = 'commercial', 'تیزر تبلیغاتی / پرفورمنس'
        OTHER = 'other', 'سایر'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='experiences')
    project_title = models.CharField('نام اثر یا پروژه', max_length=150)
    activity_type = models.CharField('نوع فعالیت', max_length=25, choices=ActivityType.choices)
    role = models.CharField('نقش یا سمت هنرمند', max_length=100)
    character_name = models.CharField('نام کاراکتر / نقش بازیگری', max_length=100, blank=True)
    start_date = models.CharField('سال یا تاریخ شروع', max_length=50)
    end_date = models.CharField('سال یا تاریخ پایان', max_length=50, blank=True)
    is_ongoing = models.BooleanField('همکاری ادامه دارد', default=False)
    production_group = models.CharField('گروه، تماشاخانه یا کمپانی تولیدکننده', max_length=150, blank=True)
    description = models.TextField('شرح مسئولیت و دستاوردها', max_length=2000, blank=True)
    external_url = models.URLField('لینک اثر یا تیزر', max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### ۲.۳. همکاران در پروژه (`ProjectCollaborator`)

```python
class ProjectCollaborator(models.Model):
    experience = models.ForeignKey(ExperienceRecord, on_delete=models.CASCADE, related_name='collaborators')
    name = models.CharField('نام و نام خانوادگی همکار', max_length=120)
    role = models.CharField('سمت در پروژه', max_length=80)  # کارگردان، تهیه کننده، طراح صحنه و...
    # در این فاز فیلد حساب متصل به صورت تعمدی وجود ندارد تا ادعای تایید متقابل ایجاد نگردد.
```

---

## ۳. قرارداد احراز شماره همراه و ورود پیامکی (OTP)

### ۳.۱. مدل داده پیشنهادی (`PhoneVerification`)
```python
class PhoneVerification(models.Model):
    phone_number = models.CharField(max_length=11, db_index=True)  # قالب 09123456789
    otp_code_hash = models.CharField(max_length=128)  # ذخیره هش‌شده کد (نه متن ساده)
    attempts_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
```

### ۳.۲. وب‌سرویس‌ها و مسیرهای پیشنهادی:

1. **`POST /api/auth/otp/send/`**
   - **ورودی:** `{"phone": "09123456789"}`
   - **اعتبارسنجی سرور:** اعتبارسنجی فرمت Regex برای خطوط همراه ایران (`^09\d{9}$`).
   - **محدودیت نرخ (Rate Limiting):** حداکثر ۱ درخواست در هر ۱۲۰ ثانیه برای یک شماره، حداکثر ۵ درخواست در روز برای یک IP.
   - **پاسخ موفق (HTTP 200):** `{"status": "sent", "wait_seconds": 120, "masked_phone": "0912***6789"}`
   - **پاسخ خطا (HTTP 429):** `{"error": "rate_limited", "message": "لطفاً پیش از درخواست مجدد ۱۲۰ ثانیه صبر کنید."}`

2. **`POST /api/auth/otp/verify/`**
   - **ورودی:** `{"phone": "09123456789", "code": "58319"}`
   - **اعتبارسنجی سرور:** بررسی انقضا (حداکثر ۲ دقیقه)، بررسی تطابق هش کد.
   - **سقف تلاش:** در صورت ۳ بار اشتباه، رکورد منقضی شده و درخواست کد جدید اجباری است.
   - **پاسخ موفق (HTTP 200):** ایجاد نشست کاربر و بازگشت `{"status": "verified", "redirect_url": "/dashboard/"}`.
   - **پاسخ خطای کد اشتباه (HTTP 400):** `{"error": "invalid_code", "remaining_attempts": 2}`.

---

## ۴. نقشه راه و قرارداد تأیید نشانی ایمیل (فاز بعد)

۱. **سه وضعیت صریح برای ایمیل:**
   - `unregistered`: ایمیل ثبت نشده است.
   - `pending`: ایمیل ثبت شده و لینک تأیید ارسال گردیده ولی هنوز باز نشده است.
   - `verified`: لینک با موفقیت کلیک و توکن تأیید شده است.
۲. **توکن تأیید:** استفاده از `django.core.signing.TimestampSigner` با حداکثر مهلت ۴۸ ساعت.
۳. **قانون محصول:** ایمیل صرفاً برای پشتیبانی، بازیابی رمز و فاکتور است؛ عدم تأیید ایمیل در این فاز نباید مانع ساخت، ویرایش یا انتشار رزومه شود.

---

## ۵. ضوابط امنیتی و کنترل دسترسی سمت سرور (Server-Side Rules)

**توجه حیاتی:** کنترل‌های فرانت‌اند فقط برای تجربه کاربری و راهنمایی است. سرور باید تمام قواعد زیر را مستقلاً اجرا کند:

1. **قانون انحصار دسترسی به فایل‌ها:** آدرس مستقیم فایل در پوشه رسانه نباید به صورت Public سرو شود. فایل‌ها حتماً از طریق View با دکوراتور دسترسی و احراز `can_view_profile` یا مالکیت بررسی و ارسال شوند (`no-store` هدرها رعایت شوند).
2. **استقلال اشتراک فضا و مشاهده:**
   - داشتن `kind == 'storage'` هیچ‌گونه دسترسی به جستجو در `Profile.objects.filter(published=True)` نمی‌دهد و باید مستقیماً خطای ۴۰۳ (`locked.html`) برگرداند.
   - داشتن `kind == 'browse'` سقف سهمیه `free_storage_mb` را اضافه نمی‌کند.
3. **تراکنش هم‌روندی سهمیه فایل:** پیش از هر بارگذاری، قفل دیتابیس گرفته شود (`select_for_update`) تا مجموع مصرف فایل‌های کاربر از `quota` بیشتر نشود.
4. **حریم خصوصی شماره و ایمیل:** سریالایزرها و قالب‌های نمایش رزومه برای دیگران، هرگز نباید فیلدهای `user.email` یا `user.phone` را به مشترکان نمایش دهند؛ تنها فیلد مجاز ارتباطی، فیلد متنی `Profile.contact` است که خود کاربر با اراده وارد کرده است.
