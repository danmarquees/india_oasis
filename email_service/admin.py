from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import EmailTemplate, EmailLog, EmailConfig, EmailQueue

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'email_type', 'subject', 'is_active', 'created_at']
    list_filter = ['email_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'email_type']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'email_type', 'subject', 'is_active')
        }),
        ('Conteúdo', {
            'fields': ('html_content', 'text_content'),
            'classes': ('wide',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request)

    actions = ['activate_templates', 'deactivate_templates']

    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} templates ativados com sucesso.')
    activate_templates.short_description = "Ativar templates selecionados"

    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} templates desativados com sucesso.')
    deactivate_templates.short_description = "Desativar templates selecionados"

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'recipient_name', 'template_name', 'status', 'attempts', 'sent_at', 'created_at']
    list_filter = ['status', 'email_template__email_type', 'sent_at', 'created_at']
    search_fields = ['recipient_email', 'recipient_name', 'subject']
    readonly_fields = ['recipient_email', 'recipient_name', 'user', 'order', 'email_template', 'subject', 'status', 'sent_at', 'error_message', 'attempts', 'created_at']

    fieldsets = (
        ('Destinatário', {
            'fields': ('recipient_email', 'recipient_name', 'user')
        }),
        ('E-mail', {
            'fields': ('email_template', 'subject', 'order')
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'attempts', 'error_message')
        }),
        ('Datas', {
            'fields': ('created_at',)
        }),
    )

    def template_name(self, obj):
        return obj.email_template.name
    template_name.short_description = 'Template'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    actions = ['retry_failed_emails']

    def retry_failed_emails(self, request, queryset):
        """Ação para reenviar emails falhados"""
        from .services import EmailService

        failed_emails = queryset.filter(status='failed')
        service = EmailService()

        retried = 0
        for email_log in failed_emails:
            # Adicionar à fila para reenvio
            EmailQueue.objects.create(
                recipient_email=email_log.recipient_email,
                recipient_name=email_log.recipient_name,
                user=email_log.user,
                order=email_log.order,
                email_template=email_log.email_template,
                context_data={},
                priority=1,
                max_attempts=1
            )
            retried += 1

        self.message_user(request, f'{retried} emails adicionados à fila para reenvio.')
    retry_failed_emails.short_description = "Reenviar emails falhados"

@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['key', 'value', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Configuração', {
            'fields': ('key', 'value', 'description', 'is_active')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def value_preview(self, obj):
        """Mostra uma prévia do valor"""
        if len(obj.value) > 50:
            return obj.value[:50] + '...'
        return obj.value
    value_preview.short_description = 'Valor'

    actions = ['activate_configs', 'deactivate_configs']

    def activate_configs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} configurações ativadas com sucesso.')
    activate_configs.short_description = "Ativar configurações selecionadas"

    def deactivate_configs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} configurações desativadas com sucesso.')
    deactivate_configs.short_description = "Desativar configurações selecionadas"

@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'template_name', 'priority_display', 'attempts', 'max_attempts', 'is_processed', 'scheduled_at', 'created_at']
    list_filter = ['priority', 'is_processed', 'email_template__email_type', 'scheduled_at', 'created_at']
    search_fields = ['recipient_email', 'recipient_name']
    readonly_fields = ['attempts', 'created_at']

    fieldsets = (
        ('Destinatário', {
            'fields': ('recipient_email', 'recipient_name', 'user')
        }),
        ('E-mail', {
            'fields': ('email_template', 'order', 'context_data')
        }),
        ('Configurações', {
            'fields': ('priority', 'scheduled_at', 'max_attempts', 'is_processed')
        }),
        ('Status', {
            'fields': ('attempts', 'created_at')
        }),
    )

    def template_name(self, obj):
        return obj.email_template.name
    template_name.short_description = 'Template'

    def priority_display(self, obj):
        colors = {1: 'red', 2: 'orange', 3: 'green'}
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_display.short_description = 'Prioridade'

    actions = ['process_emails', 'reset_attempts', 'mark_as_processed']

    def process_emails(self, request, queryset):
        """Processa emails da fila"""
        from .services import EmailService

        service = EmailService()
        processed = 0

        for email_queue in queryset.filter(is_processed=False):
            try:
                success = service._send_immediate(
                    recipient_email=email_queue.recipient_email,
                    recipient_name=email_queue.recipient_name,
                    user=email_queue.user,
                    order=email_queue.order,
                    template=email_queue.email_template,
                    context=email_queue.context_data
                )

                email_queue.attempts += 1
                if success:
                    email_queue.is_processed = True
                    processed += 1

                email_queue.save()

            except Exception as e:
                email_queue.attempts += 1
                email_queue.save()

        self.message_user(request, f'{processed} emails processados com sucesso.')
    process_emails.short_description = "Processar emails selecionados"

    def reset_attempts(self, request, queryset):
        updated = queryset.update(attempts=0)
        self.message_user(request, f'{updated} contadores de tentativas resetados.')
    reset_attempts.short_description = "Resetar tentativas"

    def mark_as_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, f'{updated} emails marcados como processados.')
    mark_as_processed.short_description = "Marcar como processado"

# Configurações personalizadas do admin
admin.site.site_header = "India Oasis - Sistema de E-mail"
admin.site.site_title = "India Oasis Email"
admin.site.index_title = "Gerenciamento de E-mails"
