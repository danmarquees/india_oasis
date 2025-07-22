from django.contrib import admin
from .models import PaymentConfig, Notification
from django.urls import path
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .views import painel_pagamentos

@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ("chave_publica", "modo_sandbox")

    change_list_template = "admin/payment_processing/paymentconfig_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('painel/', self.admin_site.admin_view(painel_pagamentos), name='painel_pagamentos'),
        ]
        return custom_urls + urls

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("event_type", "message", "created_at", "is_read")
    list_filter = ("event_type", "is_read")
    search_fields = ("message",)
    readonly_fields = ("event_type", "message", "created_at")
    ordering = ("-created_at",)
