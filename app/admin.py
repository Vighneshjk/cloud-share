from django.contrib import admin
from .models import UploadedFile, SecureLink, ShareLink

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'user', 'size', 'uploaded_at', 'expires_at')
    search_fields = ('original_name', 'user__username')
    list_filter = ('uploaded_at', 'user')

@admin.register(SecureLink)
class SecureLinkAdmin(admin.ModelAdmin):
    list_display = ('file', 'token', 'expiry_time', 'is_active')
    list_filter = ('is_active', 'expiry_time')

@admin.register(ShareLink)
class ShareLinkAdmin(admin.ModelAdmin):
    list_display = ('file', 'link_id', 'expires_at')
    list_filter = ('expires_at',)
