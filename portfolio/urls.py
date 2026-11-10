from django.urls import path
from . import views
from . import payment_views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signup/<str:token>/', views.signup, name='signup-invitation'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/edit/', views.edit_profile, name='edit-profile'),
    path('dashboard/links/add/', views.add_link, name='add-link'),
    path('dashboard/links/<int:pk>/delete/', views.delete_link, name='delete-link'),
    path('dashboard/upload/', views.upload, name='upload'),
    path('dashboard/files/<uuid:pk>/delete/', views.delete_file, name='delete-file'),
    path('artists/', views.directory, name='directory'),
    path('artists/<uuid:pk>/', views.profile_detail, name='profile'),
    path('artists/<uuid:pk>/favorite/', views.toggle_favorite, name='favorite'),
    path('files/<uuid:pk>/', views.media, name='media'),
    path('plans/', views.plans, name='plans'),
    path('support/', views.support, name='support'),
    path('support/content/', views.support, {'kind': 'content'}, name='report-content'),
    path('support/account-deletion/', views.support, {'kind': 'account'}, name='account-deletion'),
    path('legal/<str:page>/', views.legal, name='legal'),
    path('checkout/<int:pk>/', payment_views.checkout, name='checkout'),
    path('payments/<uuid:pk>/callback/', payment_views.callback, name='payment-callback'),
    path('payments/<uuid:pk>/', payment_views.payment_detail, name='payment-detail'),
    path('payments/<uuid:pk>/verify/', payment_views.retry_verification, name='payment-retry'),
]
