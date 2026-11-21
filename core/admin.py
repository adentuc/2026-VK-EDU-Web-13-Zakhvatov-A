from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0


admin.site.unregister(get_user_model())

@admin.register(get_user_model())
class AccountAdmin(UserAdmin):
    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating']
    search_fields = ['user__username', 'user__email']
    list_filter = ['user__is_active']
    list_select_related = ['user']
    raw_id_fields = ['user']
