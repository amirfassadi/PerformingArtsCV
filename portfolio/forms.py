from pathlib import Path
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from .models import Profile, WorkLink

class SignupForm(UserCreationForm):
    email = forms.EmailField(label='ایمیل')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'city', 'specialty', 'skills', 'biography', 'experience', 'contact', 'published']
        widgets = {'biography': forms.Textarea(attrs={'rows': 4}), 'experience': forms.Textarea(attrs={'rows': 5})}

class WorkLinkForm(forms.ModelForm):
    class Meta:
        model = WorkLink
        fields = ['title', 'url']

    def clean_url(self):
        value = self.cleaned_data['url']
        URLValidator(schemes=['http', 'https'])(value)
        return value

class UploadForm(forms.Form):
    title = forms.CharField(label='عنوان نمونه‌کار', max_length=120)
    file = forms.FileField(label='تصویر یا ویدئو', widget=forms.ClearableFileInput(attrs={
        'accept': '.jpg,.jpeg,.png,.webp,.mp4,.webm',
    }))

    def clean_file(self):
        value = self.cleaned_data['file']
        signature = value.read(32)
        value.seek(0)
        suffix = Path(value.name).suffix.lower()
        checks = {
            '.jpg': ('image/jpeg', signature.startswith(b'\xff\xd8\xff')),
            '.jpeg': ('image/jpeg', signature.startswith(b'\xff\xd8\xff')),
            '.png': ('image/png', signature.startswith(b'\x89PNG\r\n\x1a\n')),
            '.webp': ('image/webp', signature[:4] == b'RIFF' and signature[8:12] == b'WEBP'),
            '.mp4': ('video/mp4', signature[4:8] == b'ftyp'),
            '.webm': ('video/webm', signature.startswith(b'\x1aE\xdf\xa3')),
        }
        content_type, valid = checks.get(suffix, ('', False))
        if not valid:
            raise ValidationError('فایل معتبر JPG، PNG، WebP، MP4 یا WebM انتخاب کنید.')
        value.detected_content_type = content_type
        return value
