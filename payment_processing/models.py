from django.db import models

# Create your models here.

class PaymentConfig(models.Model):
    chave_publica = models.CharField("Chave Pública", max_length=255)
    chave_privada = models.CharField("Chave Privada", max_length=255)
    modo_sandbox = models.BooleanField("Modo Sandbox", default=True)
    # Adicione outros campos conforme necessário

    class Meta:
        verbose_name = "Configuração de Pagamento"
        verbose_name_plural = "Configurações de Pagamento"

    def __str__(self):
        return "Configuração de Pagamento"

class Notification(models.Model):
    EVENT_CHOICES = [
        ("novo_pedido", "Novo Pedido"),
        ("pedido_pendente", "Pedido Pendente"),
        ("pagamento_aprovado", "Pagamento Aprovado"),
        ("pagamento_rejeitado", "Pagamento Rejeitado"),
        ("acao_admin", "Ação Administrativa"),
    ]
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_event_type_display()}] {self.message}"
