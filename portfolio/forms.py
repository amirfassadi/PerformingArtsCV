from pathlib import Path
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from .models import Profile, WorkLink
from .media_validation import InvalidMedia, validate_media

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
        suffix = Path(value.name).suffix.lower()
        try:
            content_type = validate_media(value.read(), suffix)
        except InvalidMedia:
            raise ValidationError('فایل معتبر JPG، PNG، WebP، MP4 یا WebM انتخاب کنید.')
        finally:
            value.seek(0)
        value.detected_content_type = content_type
        return value
