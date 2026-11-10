from django.contrib import admin
from django.contrib.auth import views as auth_views
from portfolio.views import LimitedPasswordResetView, admin_login, login_view
from django.urls import include, path

urlpatterns = [
    path('admin/login/', admin_login, name='admin-login'),
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('password-reset/', LimitedPasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.txt',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/reset/done/',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('portfolio.urls')),
]
