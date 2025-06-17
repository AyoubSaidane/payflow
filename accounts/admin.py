# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission

from accounts.views import User


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename')


class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'get_groups'
    )
    prepopulated_fields = {'username': ('first_name', 'last_name',)}

    fieldsets = (
        ('Personal info', {'fields': ('first_name', 'last_name', 'username', 'email', 'password', 'is_admin')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'username', 'password1', 'password2',),
        }),
    )

    def get_groups(self, obj):
        return "\n".join([group.name for group in obj.groups.all()])


admin.site.register(User, CustomUserAdmin)

admin.site.site_header = 'SafeFlat Admin'
