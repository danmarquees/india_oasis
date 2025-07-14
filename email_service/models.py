from django.db import models
from django.contrib.auth.models import User
from store.models import Order

class EmailTemplate(models.Model):
    """
    Modelo para gerenciar templates de e-mail
    """
    EMAIL_TYPES = (
        ('order_confirmation', 'Confirmação de Pedido'),
        ('payment_approved', 'Pagamento Aprovado'),
        ('payment_rejected', 'Pagamento Rejeitado'),
        ('order_shipped', 'Pedido Enviado'),
        ('order_delivered', 'Pedido Entregue'),
        ('order_cancelled', 'Pedido Cancelado'),
        ('welcome', 'Boas-vindas'),
        ('password_reset', 'Recuperação de Senha'),
        ('newsletter', 'Newsletter'),
    )

    name = models.CharField(max_length=100, verbose_name='Nome do Template')
    email_type = models.CharField(
        max_length=30,
        choices=EMAIL_TYPES,
        unique=True,
        verbose_name='Tipo de E-mail'
    )
    subject = models.CharField(max_length=200, verbose_name='Assunto')
    html_content = models.TextField(verbose_name='Conteúdo HTML')
    text_content = models.TextField(
        blank=True,
        null=True,
        verbose_name='Conteúdo Texto',
        help_text='Versão em texto plano (opcional)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Template de E-mail'
        verbose_name_plural = 'Templates de E-mail'
        ordering = ['email_type']

    def __str__(self):
        return f'{self.name} ({self.get_email_type_display()})'

class EmailLog(models.Model):
    """
    Modelo para registrar histórico de e-mails enviados
    """
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('sent', 'Enviado'),
        ('failed', 'Falhou'),
        ('bounced', 'Retornou'),
    )

    recipient_email = models.EmailField(verbose_name='E-mail do Destinatário')
    recipient_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Nome do Destinatário'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuário'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Pedido'
    )
    email_template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        verbose_name='Template'
    )
    subject = models.CharField(max_length=200, verbose_name='Assunto')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado em')
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mensagem de Erro'
    )
    attempts = models.PositiveIntegerField(default=0, verbose_name='Tentativas')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Log de E-mail'
        verbose_name_plural = 'Logs de E-mail'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient_email} - {self.email_template.name} ({self.status})'

class EmailConfig(models.Model):
    """
    Modelo para configurações de e-mail
    """
    key = models.CharField(max_length=100, unique=True, verbose_name='Chave')
    value = models.TextField(verbose_name='Valor')
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição'
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Configuração de E-mail'
        verbose_name_plural = 'Configurações de E-mail'
        ordering = ['key']

    def __str__(self):
        return f'{self.key}: {self.value[:50]}...'

    @classmethod
    def get_config(cls, key, default=None):
        """
        Método para obter configuração por chave
        """
        try:
            config = cls.objects.get(key=key, is_active=True)
            return config.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, key, value, description=None):
        """
        Método para definir configuração
        """
        config, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description or '',
                'is_active': True
            }
        )
        return config

class EmailQueue(models.Model):
    """
    Modelo para fila de e-mails a serem enviados
    """
    PRIORITY_CHOICES = (
        (1, 'Alta'),
        (2, 'Média'),
        (3, 'Baixa'),
    )

    recipient_email = models.EmailField(verbose_name='E-mail do Destinatário')
    recipient_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Nome do Destinatário'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuário'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Pedido'
    )
    email_template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        verbose_name='Template'
    )
    context_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Dados do Contexto'
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2,
        verbose_name='Prioridade'
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Agendado para'
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name='Máximo de Tentativas'
    )
    attempts = models.PositiveIntegerField(default=0, verbose_name='Tentativas')
    is_processed = models.BooleanField(default=False, verbose_name='Processado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Fila de E-mail'
        verbose_name_plural = 'Fila de E-mails'
        ordering = ['priority', 'created_at']

    def __str__(self):
        return f'{self.recipient_email} - {self.email_template.name} (Prioridade: {self.get_priority_display()})'
