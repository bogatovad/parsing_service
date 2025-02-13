from django.contrib import admin
from frameworks_and_drivers.django.parsing.data_manager.models import Content, Tags, Like, User, MacroCategory


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'image', 'contact', 'date_start', 'date_end', 'time',
                    'location', 'cost', 'city', 'get_tags')


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', )


@admin.register(MacroCategory)
class MacroCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )
