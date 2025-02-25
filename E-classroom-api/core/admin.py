from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import User, BlacklistedToken

class customUserAdmin(UserAdmin):
    list_display = ('username','email','role','is_active', 'last_login')
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    readonly_fields = ['last_login']
    ordering = ('-date_joined',)

admin.site.register(User)
admin.site.register(BlacklistedToken)