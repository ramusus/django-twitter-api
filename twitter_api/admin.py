# -*- coding: utf-8 -*-
from django.contrib import admin

class TwitterModelAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [field.name for field in obj._meta.fields if field.name not in ['id']]
        return []