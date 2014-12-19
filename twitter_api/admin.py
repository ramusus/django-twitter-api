# -*- coding: utf-8 -*-
from django.contrib import admin
from models import Status, User


class TwitterModelAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [field.name for field in obj._meta.fields]
        return []


class StatusAdmin(TwitterModelAdmin):
    list_display = ['id', 'author', 'text']


class UserAdmin(TwitterModelAdmin):
    exclude = ('followers',)


admin.site.register(Status, StatusAdmin)
admin.site.register(User, UserAdmin)
