from django.contrib import admin
from frameworks_and_drivers.django.parsing.data_manager.models import (
    Content,
    Tags,
    Like,
    User,
    MacroCategory,
)


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "date_start",
        "date_end",
        "event_type",
        "publisher_type",
        "get_tags",
        "get_macro",
        "created",
    )
    list_filter = (
        "city",
        "event_type",
        "publisher_type",
        "date_start",
        "created",
    )
    search_fields = (
        "name",
        "description",
        "location",
        "unique_id",
    )
    readonly_fields = ("unique_id", "created", "updated")
    date_hierarchy = "date_start"
    list_per_page = 25


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username",)


@admin.register(MacroCategory)
class MacroCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
