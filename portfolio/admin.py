from django.contrib import admin
from .models import Entitlement, Invitation, InvitationLink, Payment, Plan, PortfolioFile, Profile, SiteSettings, SupportRequest, WorkLink

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

@admin.register(InvitationLink)
class InvitationLinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at', 'last_used_at']
    list_filter = ['is_active']
    search_fields = ['user__username']
    readonly_fields = ['user', 'token', 'created_at', 'last_used_at']
    list_editable = ['is_active']
    actions = ['deactivate_links']

    @admin.action(description='غیرفعال‌کردن لینک‌های دعوت انتخاب‌شده')
    def deactivate_links(self, request, queryset):
        queryset.update(is_active=False)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['inviter', 'invitee_display_name', 'invitee', 'link_owner', 'created_at']
    search_fields = ['inviter__username', 'invitee__username', 'invitee__profile__display_name']
    readonly_fields = ['inviter', 'invitee', 'link', 'created_at']

    @admin.display(description='نام نمایشی دعوت‌شده')
    def invitee_display_name(self, obj):
        return obj.invitee_display_name

    @admin.display(description='صاحب لینک')
    def link_owner(self, obj):
        return obj.link.user

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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

@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ['kind', 'subject', 'user', 'status', 'created_at']
    list_filter = ['kind', 'status']
    search_fields = ['subject', 'message', 'user__username']
    readonly_fields = ['user', 'kind', 'subject', 'message', 'created_at']
