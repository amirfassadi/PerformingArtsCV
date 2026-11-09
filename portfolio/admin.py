from django.contrib import admin
from .models import Entitlement, Payment, Plan, PortfolioFile, Profile, SiteSettings, WorkLink

admin.site.site_header = 'مدیریت صحنه‌نما'
admin.site.site_title = 'صحنه‌نما'

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fields = ['free_storage_mb']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

class WorkLinkInline(admin.TabularInline):
    model = WorkLink
    extra = 0

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user', 'city', 'published']
    list_filter = ['published']
    search_fields = ['display_name', 'user__username']
    inlines = [WorkLinkInline]

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind', 'storage_mb', 'duration_days', 'price_rial', 'active']
    list_filter = ['kind', 'active']

@admin.register(Entitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ['user', 'kind', 'storage_mb', 'starts_at', 'ends_at', 'revoked', 'reference']
    list_filter = ['kind', 'revoked']
    search_fields = ['user__username', 'reference']

@admin.register(PortfolioFile)
class PortfolioFileAdmin(admin.ModelAdmin):
    list_display = ['title', 'profile', 'size', 'created_at']
    fields = ['title', 'profile', 'size', 'content_type', 'created_at']
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'plan_name', 'amount_rial', 'sandbox', 'status', 'created_at']
    list_filter = ['status', 'sandbox']
    search_fields = ['user__username', 'ref_id', 'authority']
    readonly_fields = [field.name for field in Payment._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
