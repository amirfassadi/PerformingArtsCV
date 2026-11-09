from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from .access import can_browse, can_view_profile, storage_quota, storage_used
from .forms import ProfileForm, SignupForm, UploadForm, WorkLinkForm
from .invitations import InvitationUnavailable, register_invited_user
from .models import MB, Favorite, InvitationLink, Plan, PortfolioFile, Profile, SiteSettings, WorkLink
from .services import add_file, remove_file
from .media import LimitedFileIterator, parse_range

def home(request):
    return render(request, 'portfolio/home.html', {'free_mb': SiteSettings.current().free_storage_mb})

def _render_signup(request, context, status=200):
    response = render(request, 'registration/signup.html', context, status=status)
    response['Cache-Control'] = 'private, no-store'
    response['Referrer-Policy'] = 'strict-origin'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response

@never_cache
def signup(request, token=None):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if not token:
        return _render_signup(request, {'requires_invitation': True})
    link = InvitationLink.objects.filter(token=token, is_active=True).select_related('user').first()
    if link is None:
        return _render_signup(request, {'invalid_invitation': True}, status=404)

    form = SignupForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            user = register_invited_user(form, token)
        except InvitationUnavailable:
            return _render_signup(request, {'invalid_invitation': True}, status=404)
        except IntegrityError:
            if not get_user_model().objects.filter(username=form.cleaned_data['username']).exists():
                raise
            form.add_error('username', 'این نام کاربری هم‌زمان توسط حساب دیگری ثبت شد؛ نام دیگری انتخاب کنید.')
        else:
            login(request, user)
            return redirect('dashboard')
    return _render_signup(request, {'form': form, 'invitation': link})

def own_profile(user):
    return Profile.objects.get_or_create(user=user, defaults={'display_name': user.username})[0]

@never_cache
@login_required
def dashboard(request):
    profile = own_profile(request.user)
    quota, used = storage_quota(request.user), storage_used(profile)
    invitation_link, _ = InvitationLink.objects.get_or_create(user=request.user)
    invitees = request.user.sent_invitations.select_related('invitee__profile')
    return render(request, 'portfolio/dashboard.html', {
        'profile': profile, 'quota_mb': quota / MB, 'used_mb': used / MB,
        'remaining_mb': max(0, quota - used) / MB,
        'usage_percent': min(100, used * 100 / quota) if quota else (100 if used else 0),
        'browse_active': can_browse(request.user), 'over_quota': used > quota,
        'invitation_link_active': invitation_link.is_active,
        'invitation_url': request.build_absolute_uri(reverse('signup-invitation', args=[invitation_link.token])),
        'invitees': invitees, 'invite_count': invitees.count(),
    })

@never_cache
@login_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, instance=own_profile(request.user))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'رزومه ذخیره شد.')
        return redirect('dashboard')
    return render(request, 'portfolio/form.html', {'form': form, 'title': 'ویرایش رزومه'})

@never_cache
@login_required
def add_link(request):
    form = WorkLinkForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.profile = own_profile(request.user)
        item.save()
        messages.success(request, 'لینک اثر اضافه شد.')
        return redirect('dashboard')
    return render(request, 'portfolio/form.html', {'form': form, 'title': 'افزودن لینک اثر'})

@login_required
@require_POST
def delete_link(request, pk):
    get_object_or_404(WorkLink, pk=pk, profile__user=request.user).delete()
    return redirect('dashboard')

@never_cache
@login_required
def upload(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    if getattr(request, 'upload_too_large', False):
        form.add_error(None, 'حجم فایل از سقف مجاز هر بارگذاری بیشتر است.')
    elif request.method == 'POST' and form.is_valid():
        try:
            add_file(own_profile(request.user), form.cleaned_data['file'], form.cleaned_data['title'])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'نمونه‌کار اضافه شد.')
            return redirect('dashboard')
    return render(request, 'portfolio/form.html', {
        'form': form, 'title': 'بارگذاری نمونه‌کار', 'multipart': True,
        'hint': 'فرمت‌های مجاز: JPG، PNG، WebP، MP4 و WebM. فایل‌ها عمومی نیستند.',
    })

@login_required
@require_POST
def delete_file(request, pk):
    item = get_object_or_404(PortfolioFile, pk=pk, profile__user=request.user)
    remove_file(item)
    messages.success(request, 'فایل حذف شد و فضای آن آزاد شد.')
    return redirect('dashboard')

def locked(request):
    return render(request, 'portfolio/locked.html', status=403)

@never_cache
@login_required
def directory(request):
    if not can_browse(request.user):
        return locked(request)
    profiles = Profile.objects.filter(published=True).exclude(user=request.user)
    query = request.GET.get('q', '').strip()[:120]
    city = request.GET.get('city', '').strip()[:80]
    if query:
        profiles = profiles.filter(Q(display_name__icontains=query) | Q(specialty__icontains=query) | Q(skills__icontains=query))
    if city:
        profiles = profiles.filter(city__icontains=city)
    only_favorites = request.GET.get('favorites') == '1'
    if only_favorites:
        profiles = profiles.filter(favorite__user=request.user)
    from django.core.paginator import Paginator
    page = Paginator(profiles, 12).get_page(request.GET.get('page'))
    return render(request, 'portfolio/directory.html', {
        'page': page, 'q': query, 'city': city, 'only_favorites': only_favorites,
    })

@never_cache
@login_required
def profile_detail(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if not can_view_profile(request.user, profile):
        return locked(request)
    return render(request, 'portfolio/profile.html', {
        'profile': profile, 'is_owner': profile.user_id == request.user.pk,
        'is_favorite': Favorite.objects.filter(user=request.user, profile=profile).exists(),
    })

@never_cache
@login_required
@require_POST
def toggle_favorite(request, pk):
    if not can_browse(request.user):
        return locked(request)
    profile = get_object_or_404(Profile, pk=pk, published=True)
    favorite, created = Favorite.objects.get_or_create(user=request.user, profile=profile)
    if not created:
        favorite.delete()
    return redirect('profile', pk=pk)

@never_cache
@login_required
def media(request, pk):
    item = get_object_or_404(PortfolioFile.objects.select_related('profile'), pk=pk)
    if not can_view_profile(request.user, item.profile):
        return HttpResponse(status=403)
    try:
        handle = item.file.open('rb')
    except FileNotFoundError:
        return HttpResponse('فایل فعلاً در دسترس نیست.', status=404)
    requested_range = request.headers.get('Range')
    if requested_range:
        try:
            start, end = parse_range(requested_range, item.size)
        except ValueError:
            handle.close()
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{item.size}'
            return response
        handle.seek(start)
        response = StreamingHttpResponse(LimitedFileIterator(handle, end - start + 1),
                                         status=206, content_type=item.content_type)
        response['Content-Range'] = f'bytes {start}-{end}/{item.size}'
        response['Content-Length'] = end - start + 1
    else:
        response = FileResponse(handle, content_type=item.content_type)
    response['Accept-Ranges'] = 'bytes'
    response['Content-Disposition'] = 'inline'
    response['Cache-Control'] = 'private, no-store'
    response['Cross-Origin-Resource-Policy'] = 'same-origin'
    return response

@never_cache
@login_required
def plans(request):
    return render(request, 'portfolio/plans.html', {
        'plans': Plan.objects.filter(active=True).order_by('kind', 'price_rial'),
        'browse_active': can_browse(request.user),
        'free_mb': SiteSettings.current().free_storage_mb,
        'gateway_ready': bool(settings.ZARINPAL_MERCHANT_ID),
        'sandbox': settings.ZARINPAL_SANDBOX,
        'payments': request.user.payment_set.all()[:10],
    })
