import logging
import smtplib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from store.models import Order
from .models import EmailTemplate, EmailLog, EmailConfig, EmailQueue

logger = logging.getLogger(__name__)

class EmailService:
    """
    Serviço principal para envio de e-mails
    """

    def __init__(self):
        self.default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@indiaoasis.com.br')
        self.email_enabled = getattr(settings, 'ORDER_EMAIL_ENABLED', True)

    def send_email(self,
                   recipient_email: str,
                   template_type: str,
                   context: Dict[str, Any],
                   recipient_name: str = None,
                   user: User = None,
                   order: Order = None,
                   priority: int = 2,
                   scheduled_at: datetime = None) -> bool:
        """
        Envia e-mail usando template específico

        Args:
            recipient_email: E-mail do destinatário
            template_type: Tipo do template (ex: 'order_confirmation')
            context: Dados para renderizar o template
            recipient_name: Nome do destinatário
            user: Usuário relacionado
            order: Pedido relacionado
            priority: Prioridade do e-mail (1=alta, 2=média, 3=baixa)
            scheduled_at: Data para envio agendado

        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        if not self.email_enabled:
            logger.info("Envio de e-mail desabilitado nas configurações")
            return False

        try:
            # Buscar template
            template = EmailTemplate.objects.get(
                email_type=template_type,
                is_active=True
            )

            # Se agendado, adicionar à fila
            if scheduled_at:
                return self._add_to_queue(
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    user=user,
                    order=order,
                    template=template,
                    context=context,
                    priority=priority,
                    scheduled_at=scheduled_at
                )

            # Enviar imediatamente
            return self._send_immediate(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                user=user,
                order=order,
                template=template,
                context=context
            )

        except EmailTemplate.DoesNotExist:
            logger.error(f"Template '{template_type}' não encontrado")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {str(e)}")
            return False

    def _add_to_queue(self, **kwargs) -> bool:
        """
        Adiciona e-mail à fila de envio
        """
        try:
            EmailQueue.objects.create(
                recipient_email=kwargs['recipient_email'],
                recipient_name=kwargs.get('recipient_name'),
                user=kwargs.get('user'),
                order=kwargs.get('order'),
                email_template=kwargs['template'],
                context_data=kwargs['context'],
                priority=kwargs.get('priority', 2),
                scheduled_at=kwargs.get('scheduled_at'),
            )
            logger.info(f"E-mail adicionado à fila: {kwargs['recipient_email']}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar e-mail à fila: {str(e)}")
            return False

    def _send_immediate(self,
                       recipient_email: str,
                       recipient_name: str,
                       user: User,
                       order: Order,
                       template: EmailTemplate,
                       context: Dict[str, Any]) -> bool:
        """
        Envia e-mail imediatamente
        """
        email_log = EmailLog.objects.create(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            user=user,
            order=order,
            email_template=template,
            subject=template.subject,
            status='pending'
        )

        try:
            # Renderizar template
            rendered_subject = self._render_template(template.subject, context)
            rendered_html = self._render_template(template.html_content, context)
            rendered_text = None

            if template.text_content:
                rendered_text = self._render_template(template.text_content, context)

            # Criar e-mail
            email = EmailMultiAlternatives(
                subject=rendered_subject,
                body=rendered_text or rendered_html,
                from_email=self.default_from_email,
                to=[recipient_email]
            )

            # Adicionar versão HTML se disponível
            if rendered_html:
                email.attach_alternative(rendered_html, "text/html")

            # Enviar
            email.send()

            # Atualizar log
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.attempts = 1
            email_log.save()

            logger.info(f"E-mail enviado com sucesso para {recipient_email}")
            return True

        except Exception as e:
            # Atualizar log com erro
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.attempts = 1
            email_log.save()

            logger.error(f"Erro ao enviar e-mail para {recipient_email}: {str(e)}")
            return False

    def _render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """
        Renderiza template Django com contexto
        """
        try:
            template = Template(template_content)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Erro ao renderizar template: {str(e)}")
            return template_content

    def process_email_queue(self, max_emails: int = 50) -> int:
        """
        Processa fila de e-mails

        Args:
            max_emails: Máximo de e-mails para processar

        Returns:
            int: Número de e-mails processados
        """
        processed = 0

        # Buscar e-mails pendentes
        pending_emails = EmailQueue.objects.filter(
            is_processed=False,
            attempts__lt=models.F('max_attempts'),
            scheduled_at__lte=timezone.now()
        ).order_by('priority', 'created_at')[:max_emails]

        for email_queue in pending_emails:
            try:
                success = self._send_immediate(
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
                logger.error(f"Erro ao processar e-mail da fila {email_queue.id}: {str(e)}")
                email_queue.attempts += 1
                email_queue.save()

        return processed

class OrderEmailService(EmailService):
    """
    Serviço específico para e-mails de pedidos
    """

    def send_order_confirmation(self, order: Order) -> bool:
        """
        Envia e-mail de confirmação de pedido
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Confirmado',
            'message': 'Seu pedido foi confirmado com sucesso!'
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='order_confirmation',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=1  # Alta prioridade
        )

    def send_payment_approved(self, order: Order) -> bool:
        """
        Envia e-mail de pagamento aprovado
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Pagamento Aprovado',
            'message': 'Seu pagamento foi aprovado! Seu pedido está sendo processado.'
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='payment_approved',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=1  # Alta prioridade
        )

    def send_payment_rejected(self, order: Order) -> bool:
        """
        Envia e-mail de pagamento rejeitado
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Pagamento Rejeitado',
            'message': 'Houve um problema com seu pagamento. Tente novamente ou entre em contato conosco.'
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='payment_rejected',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=1  # Alta prioridade
        )

    def send_order_shipped(self, order: Order, tracking_code: str = None) -> bool:
        """
        Envia e-mail de pedido enviado
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Enviado',
            'message': 'Seu pedido foi enviado!',
            'tracking_code': tracking_code
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='order_shipped',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=2  # Média prioridade
        )

    def send_order_delivered(self, order: Order) -> bool:
        """
        Envia e-mail de pedido entregue
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Entregue',
            'message': 'Seu pedido foi entregue com sucesso! Esperamos que goste dos produtos.'
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='order_delivered',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=2  # Média prioridade
        )

    def send_order_cancelled(self, order: Order, reason: str = None) -> bool:
        """
        Envia e-mail de pedido cancelado
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Cancelado',
            'message': 'Seu pedido foi cancelado.',
            'cancellation_reason': reason
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='order_cancelled',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=1  # Alta prioridade
        )

    def _get_order_context(self, order: Order) -> Dict[str, Any]:
        """
        Cria contexto padrão para e-mails de pedido
        """
        return {
            'order': order,
            'order_number': order.id,
            'customer_name': f"{order.first_name} {order.last_name}",
            'customer_email': order.email,
            'order_total': order.total_price,
            'order_date': order.created.strftime('%d/%m/%Y %H:%M'),
            'order_status': order.get_status_display(),
            'order_items': order.items.all(),
            'shipping_address': {
                'address': order.address,
                'city': order.city,
                'state': order.state,
                'postal_code': order.postal_code,
            },
            'store_name': 'India Oasis',
            'store_url': 'https://www.indiaoasis.com.br',
            'support_email': getattr(settings, 'ORDER_EMAIL_ADMIN', 'suporte@indiaoasis.com.br'),
            'current_year': timezone.now().year,
        }

class UserEmailService(EmailService):
    """
    Serviço específico para e-mails de usuários
    """

    def send_welcome_email(self, user: User) -> bool:
        """
        Envia e-mail de boas-vindas
        """
        context = {
            'user': user,
            'user_name': user.first_name or user.username,
            'store_name': 'India Oasis',
            'store_url': 'https://www.indiaoasis.com.br',
            'support_email': getattr(settings, 'ORDER_EMAIL_ADMIN', 'suporte@indiaoasis.com.br'),
            'current_year': timezone.now().year,
        }

        return self.send_email(
            recipient_email=user.email,
            template_type='welcome',
            context=context,
            recipient_name=user.first_name or user.username,
            user=user,
            priority=3  # Baixa prioridade
        )

class EmailTemplateService:
    """
    Serviço para gerenciar templates de e-mail
    """

    @staticmethod
    def create_default_templates():
        """
        Cria templates padrão do sistema
        """
        default_templates = [
            {
                'name': 'Confirmação de Pedido',
                'email_type': 'order_confirmation',
                'subject': 'Pedido #{{ order_number }} Confirmado - India Oasis',
                'html_content': EmailTemplateService._get_order_confirmation_html(),
                'text_content': EmailTemplateService._get_order_confirmation_text(),
            },
            {
                'name': 'Pagamento Aprovado',
                'email_type': 'payment_approved',
                'subject': 'Pagamento Aprovado - Pedido #{{ order_number }} - India Oasis',
                'html_content': EmailTemplateService._get_payment_approved_html(),
                'text_content': EmailTemplateService._get_payment_approved_text(),
            },
            {
                'name': 'Pagamento Rejeitado',
                'email_type': 'payment_rejected',
                'subject': 'Problema com Pagamento - Pedido #{{ order_number }} - India Oasis',
                'html_content': EmailTemplateService._get_payment_rejected_html(),
                'text_content': EmailTemplateService._get_payment_rejected_text(),
            },
            {
                'name': 'Pedido Enviado',
                'email_type': 'order_shipped',
                'subject': 'Pedido #{{ order_number }} Enviado - India Oasis',
                'html_content': EmailTemplateService._get_order_shipped_html(),
                'text_content': EmailTemplateService._get_order_shipped_text(),
            },
            {
                'name': 'Pedido Entregue',
                'email_type': 'order_delivered',
                'subject': 'Pedido #{{ order_number }} Entregue - India Oasis',
                'html_content': EmailTemplateService._get_order_delivered_html(),
                'text_content': EmailTemplateService._get_order_delivered_text(),
            },
            {
                'name': 'Pedido Cancelado',
                'email_type': 'order_cancelled',
                'subject': 'Pedido #{{ order_number }} Cancelado - India Oasis',
                'html_content': EmailTemplateService._get_order_cancelled_html(),
                'text_content': EmailTemplateService._get_order_cancelled_text(),
            },
            {
                'name': 'Boas-vindas',
                'email_type': 'welcome',
                'subject': 'Bem-vindo à India Oasis!',
                'html_content': EmailTemplateService._get_welcome_html(),
                'text_content': EmailTemplateService._get_welcome_text(),
            },
        ]

        for template_data in default_templates:
            EmailTemplate.objects.update_or_create(
                email_type=template_data['email_type'],
                defaults=template_data
            )

    @staticmethod
    def _get_order_confirmation_html():
        return """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #333;">Pedido Confirmado!</h1>
            <p>Olá {{ customer_name }},</p>
            <p>Seu pedido #{{ order_number }} foi confirmado com sucesso!</p>

            <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0;">
                <h2>Detalhes do Pedido</h2>
                <p><strong>Número do Pedido:</strong> #{{ order_number }}</p>
                <p><strong>Data:</strong> {{ order_date }}</p>
                <p><strong>Status:</strong> {{ order_status }}</p>
                <p><strong>Total:</strong> R$ {{ order_total }}</p>
            </div>

            <div style="background-color: #f9f9f9; padding: 20px; margin: 20px 0;">
                <h3>Itens do Pedido</h3>
                {% for item in order_items %}
                <div style="border-bottom: 1px solid #ddd; padding: 10px 0;">
                    <p><strong>{{ item.product.name }}</strong></p>
                    <p>Quantidade: {{ item.quantity }} | Preço: R$ {{ item.price }}</p>
                </div>
                {% endfor %}
            </div>

            <div style="background-color: #f9f9f9; padding: 20px; margin: 20px 0;">
                <h3>Endereço de Entrega</h3>
                <p>{{ shipping_address.address }}</p>
                <p>{{ shipping_address.city }}, {{ shipping_address.state }}</p>
                <p>CEP: {{ shipping_address.postal_code }}</p>
            </div>

            <p>Obrigado por escolher a India Oasis!</p>
            <p>Em caso de dúvidas, entre em contato conosco em {{ support_email }}</p>

            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                © {{ current_year }} India Oasis. Todos os direitos reservados.
            </p>
        </div>
        """

    @staticmethod
    def _get_order_confirmation_text():
        return """
        Pedido Confirmado!

        Olá {{ customer_name }},

        Seu pedido #{{ order_number }} foi confirmado com sucesso!

        Detalhes do Pedido:
        - Número do Pedido: #{{ order_number }}
        - Data: {{ order_date }}
        - Status: {{ order_status }}
        - Total: R$ {{ order_total }}

        Itens do Pedido:
        {% for item in order_items %}
        - {{ item.product.name }} (Quantidade: {{ item.quantity }}, Preço: R$ {{ item.price }})
        {% endfor %}

        Endereço de Entrega:
        {{ shipping_address.address }}
        {{ shipping_address.city }}, {{ shipping_address.state }}
        CEP: {{ shipping_address.postal_code }}

        Obrigado por escolher a India Oasis!
        Em caso de dúvidas, entre em contato conosco em {{ support_email }}

        © {{ current_year }} India Oasis. Todos os direitos reservados.
        """

    @staticmethod
    def _get_payment_approved_html():
        return """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #28a745;">Pagamento Aprovado!</h1>
            <p>Olá {{ customer_name }},</p>
            <p>Ótimas notícias! Seu pagamento foi aprovado e seu pedido está sendo processado.</p>

            <div style="background-color: #d4edda; padding: 20px; margin: 20px 0; border-left: 4px solid #28a745;">
                <h2>Detalhes do Pagamento</h2>
                <p><strong>Pedido:</strong> #{{ order_number }}</p>
                <p><strong>Valor:</strong> R$ {{ order_total }}</p>
                <p><strong>Status:</strong> {{ order_status }}</p>
            </div>

            <p>Seu pedido será processado e enviado em breve. Você receberá um e-mail quando o produto for enviado.</p>

            <p>Obrigado por escolher a India Oasis!</p>
            <p>Em caso de dúvidas, entre em contato conosco em {{ support_email }}</p>

            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                © {{ current_year }} India Oasis. Todos os direitos reservados.
            </p>
        </div>
        """

    @staticmethod
    def _get_payment_approved_text():
        return """
        Pagamento Aprovado!

        Olá {{ customer_name }},

        Ótimas notícias! Seu pagamento foi aprovado e seu pedido está sendo processado.

        Detalhes do Pagamento:
        - Pedido: #{{ order_number }}
        - Valor: R$ {{ order_total }}
        - Status: {{ order_status }}

        Seu pedido será processado e enviado em breve. Você receberá um e-mail quando o produto for enviado.

        Obrigado por escolher a India Oasis!
        Em caso de dúvidas, entre em contato conosco em {{ support_email }}

        © {{ current_year }} India Oasis. Todos os direitos reservados.
        """

    @staticmethod
    def _get_payment_rejected_html():
        return """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #dc3545;">Problema com Pagamento</h1>
            <p>Olá {{ customer_name }},</p>
            <p>Infelizmente, houve um problema com o pagamento do seu pedido #{{ order_number }}.</p>

            <div style="background-color: #f8d7da; padding: 20px; margin: 20px 0; border-left: 4px solid #dc3545;">
                <h2>Detalhes do Pedido</h2>
                <p><strong>Pedido:</strong> #{{ order_number }}</p>
                <p><strong>Valor:</strong> R$ {{ order_total }}</p>
                <p><strong>Status:</strong> {{ order_status }}</p>
            </div>

            <p>Você pode tentar realizar o pagamento novamente ou entrar em contato conosco para obter ajuda.</p>

            <p>Para tentar novamente, acesse sua conta em {{ store_url }}</p>

            <p>Em caso de dúvidas, entre em contato conosco em {{ support_email }}</p>

            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                © {{ current_year }} India Oasis. Todos os direitos reservados.
            </p>
        </div>
        """

    @staticmethod
    def _get_payment_rejected_text():
        return """
        Problema com Pagamento

        Olá {{ customer_name }},

        Infelizmente, houve um problema com o pagamento do seu pedido #{{ order_number }}.

        Detalhes do Pedido:
        - Pedido: #{{ order_number }}
        - Valor: R$ {{ order_total }}
        - Status: {{ order_status }}

        Você pode tentar realizar o pagamento novamente ou entrar em contato conosco para obter ajuda.

        Para tentar novamente, acesse sua conta em {{ store_url }}

        Em caso de dúvidas, entre em contato conosco em {{ support_email }}

        © {{ current_year }} India Oasis. Todos os direitos reservados.
        """

    @staticmethod
    def _get_order_shipped_html():
        return """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #007bff;">Pedido Enviado!</h1>
            <p>Olá {{ customer_name }},</p>
            <p>Seu pedido #{{ order_number }} foi enviado!</p>

            <div style="background-color: #cce5ff; padding: 20px; margin: 20px 0; border-left: 4px solid #007bff;">
                <h2>Informações de Envio</h2>
                <p><strong>Pedido:</strong> #{{ order_number }}</p>
                {% if tracking_code %}
                <p><strong>Código de Rastreamento:</strong> {{ tracking_code }}</p>
                {% endif %}
                <p><strong>Status:</strong> {{ order_status }}</p>
            </div>

            <p>Seu pedido está a caminho! Você pode acompanhar o envio usando o código de rastreamento acima.</p>

            <p>Obrigado por escolher a India Oasis!</p>
            <p>Em caso de dúvidas, entre em contato conosco em {{ support_email }}</p>

            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                © {{ current_year }} India Oasis. Todos os direitos reservados.
            </p>
        </div>
        """

    @staticmethod
    def _get_order_shipped_text():
        return """
        Pedido Enviado!

        Olá {{ customer_name }},

        Seu pedido #{{ order_number }} foi enviado!

        Informações de Envio:
        - Pedido: #{{ order_number }}
        {% if tracking_code %}
        - Código de Rastreamento: {{ tracking_code }}
        {% endif %}
        - Status: {{ order_status }}

        Seu pedido está a caminho! Você pode acompanhar o envio usando o código de rastreamento acima.

        Obrigado por escolher a India Oasis!
        Em caso de dúvidas, entre em contato conosco em {{ support_email }}

        © {{ current_year }} India Oasis. Todos os direitos reservados.
        """

    @staticmethod
    def _get_order_delivered_html():
        return """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #28a745;">Pedido Entregue!</h1>
            <p>Olá {{ customer_name }},</p>
            <p>Seu pedido #{{ order_number }} foi entregue com sucesso!</p>

            <div style="background-color: #d4edda; padding: 20px; margin: 20px 0; border-left: 4px solid #28a745;">
                <h2>Pedido Finalizado</h2>
                <p><strong>Pedido:</strong> #{{ order_number }}</p>
                <p><strong>Status:</strong> {{ order_status }}</p>
            </div>

            <p>Esperamos que você goste dos produtos! Se tiver alguma dúvida ou problema, não hesite em nos contatar.</p>

            <p>Que tal avaliar sua experiência? Acesse {{ store_url }} e deixe sua avaliação!</p>

            <p>Obrigado por escolher a India Oasis!</p>
            <p>Em caso de dúvidas, entre em contato conosco em {{ support_email }}</p>

            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                © {{ current_year }} India Oasis. Todos os direitos reservados.
            </p>
        </div>
        """

    @staticmethod
    def _get_order_delivered_text():
        return """
        Pedido Entregue!

        Olá {{ customer_name }},

        Seu pedido #{{ order_number }} foi entregue com sucesso!

        Pedido Finalizado:
        - Pedido: #{{ order_number }}
        - Status: {{ order_status }}

        Esperamos que você goste dos produtos! Se tiver alguma dúvida ou problema, não hesite em nos contatar.

        Que tal avaliar sua experiência? Acesse {{ store_url }} e deixe sua avaliação!

        Obrigado por escolher a India Oasis!
        Em caso de dúvidas, entre em contato conosco em {{ support_email }}

        © {{ current_year }} India Oasis. Todos os direitos reservados.
        """

    @staticmethod
    def _get_order_cancelled_html():
        return """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #dc3545;">Pedido Cancelado</h1>
            <p>Olá {{ customer_name }},</p>
            <p>Seu pedido #{{ order_number }} foi cancelado.</p>

            <div style="background-color: #f8d7da; padding: 20px; margin: 20px 0; border-left: 4px solid #dc3545;">
                <h2>Detalhes do Cancelamento</h2>
                <p><strong>Pedido:</strong> #{{ order_number }}</p>
                <p><strong>Status:</strong> {{ order_status }}</p>
                {% if cancellation_reason %}
                <p><strong>Motivo:</strong> {{ cancellation_reason }}</p>
                {% endif %}
            </div>

            <p>Se você cancelou por engano ou deseja fazer um novo pedido, visite nossa loja em {{ store_url }}</p>

            <p>Se o cancelamento não foi solicitado por você, entre em contato conosco imediatamente.</p>

            <p>Em caso de dúvidas, entre em contato conosco em {{ support_email }}</p>

            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                © {{ current_year }} India Oasis. Todos os direitos reservados.
            </p>
        </div>
        """

    @staticmethod
    def _get_order_cancelled_text():
        return """
        Pedido Cancelado

        Olá {{ customer_name }},

        Seu pedido #{{ order_number }} foi cancelado.

        Detalhes do Cancelamento:
        - Pedido: #{{ order_number }}
        - Status: {{ order_status }}
        {% if cancellation_reason %}
        - Motivo: {{ cancellation_reason }}
        {% endif %}

        Se você cancelou por engano ou deseja fazer um novo pedido, visite nossa loja em {{ store_url }}

        Se o cancelamento não foi solicitado por você, entre em contato conosco imediatamente.

        Em caso de dúvidas, entre em contato conosco em {{ support_email }}

        © {{ current_year }} India Oasis. Todos os direitos reservados.
        """

    @staticmethod
    def _get_welcome_html():
        return """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #007bff;">Bem-vindo à India Oasis!</h1>
            <p>Olá {{ user_name }},</p>
            <p>Seja muito bem-vindo(a) à India Oasis! Estamos felizes em tê-lo(a) conosco.</p>

            <div style="background-color: #e7f3ff; padding: 20px; margin: 20px 0; border-left: 4px solid #007bff;">
                <h2>Explore nossa loja</h2>
                <p>Descubra produtos únicos e de qualidade em nossa coleção especial.</p>
                <p>Navegue por nossas categorias e encontre exatamente o que você procura.</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ store_url }}" style="background-color: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">
                    Visitar Loja
                </a>
            </div>

            <h3>Vantagens de ser nosso cliente:</h3>
            <ul>
                <li>Produtos de alta qualidade</li>
                <li>Entrega rápida e segura</li>
                <li>Atendimento personalizado</li>
                <li>Ofertas exclusivas</li>
            </ul>

            <p>Se tiver alguma dúvida, não hesite em nos contatar em {{ support_email }}</p>

            <p>Obrigado por escolher a India Oasis!</p>

            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                © {{ current_year }} India Oasis. Todos os direitos reservados.
            </p>
        </div>
        """

    @staticmethod
    def _get_welcome_text():
        return """
        Bem-vindo à India Oasis!

        Olá {{ user_name }},

        Seja muito bem-vindo(a) à India Oasis! Estamos felizes em tê-lo(a) conosco.

        Explore nossa loja:
        Descubra produtos únicos e de qualidade em nossa coleção especial.
        Navegue por nossas categorias e encontre exatamente o que você procura.

        Visite nossa loja: {{ store_url }}

        Vantagens de ser nosso cliente:
        - Produtos de alta qualidade
        - Entrega rápida e segura
        - Atendimento personalizado
        - Ofertas exclusivas

        Se tiver alguma dúvida, não hesite em nos contatar em {{ support_email }}

        Obrigado por escolher a India Oasis!

        © {{ current_year }} India Oasis. Todos os direitos reservados.
